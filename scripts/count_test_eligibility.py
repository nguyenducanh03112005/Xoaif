"""Count distinct pre-test eligible customers without reading or deriving labels."""

from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

import yaml
from zoneinfo import ZoneInfo

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ingest.identifiers import pseudonymize_id
from ingest.access_log import record_reserved_access
from ingest.settings import load_analytics_hmac_key

LOCAL_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
SNAPSHOT_ROOT = PROJECT_ROOT / "data" / "raw" / "pancake_orders"


def local_date(value: Any) -> date | None:
    """Normalize an owner-declared UTC timestamp to its local calendar date."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)
    return parsed.astimezone(LOCAL_TZ).date()


def parse_scenario(raw: str) -> tuple[str, date]:
    try:
        name, date_text = raw.split("=", 1)
        if not re.fullmatch(r"N\d+", name):
            raise ValueError
        return name, date.fromisoformat(date_text)
    except ValueError:
        raise argparse.ArgumentTypeError("scenario must be Nxxx=YYYY-MM-DD") from None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-id", required=True)
    parser.add_argument("--scenario", action="append", type=parse_scenario, required=True)
    parser.add_argument(
        "--record",
        action="store_true",
        help="verify the locked split, then save aggregate counts and access-log entries",
    )
    args = parser.parse_args()
    if not re.fullmatch(r"\d{8}T\d{6}Z", args.snapshot_id):
        parser.error("--snapshot-id must use YYYYMMDDTHHMMSSZ format")
    if len({name for name, _ in args.scenario}) != len(args.scenario):
        parser.error("scenario names must be unique")

    snapshot_dir = SNAPSHOT_ROOT / args.snapshot_id
    manifest_path = snapshot_dir / "manifest.json"
    try:
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes)
        if manifest.get("snapshot_id") != args.snapshot_id or manifest.get("status") != "complete":
            raise ValueError("snapshot is not complete or ID does not match")
        pages = manifest["pages"]
        if not isinstance(pages, list) or not pages:
            raise ValueError("manifest has no page records")
        hmac_key = load_analytics_hmac_key(PROJECT_ROOT / "xoaif.env")
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, ValueError) as exc:
        print(f"Eligibility count stopped ({type(exc).__name__}); no source values printed.")
        return 2

    cohorts = {name: set() for name, _ in args.scenario}
    starts = dict(args.scenario)
    snapshot_root = snapshot_dir.resolve()
    rows_seen = 0

    try:
        for expected_page, page_record in enumerate(pages, start=1):
            page_name = page_record["file"]
            page_path = (snapshot_dir / page_name).resolve()
            if not page_path.is_relative_to(snapshot_root):
                raise ValueError("manifest page escaped snapshot directory")
            page_bytes = page_path.read_bytes()
            if hashlib.sha256(page_bytes).hexdigest() != page_record.get("sha256"):
                raise ValueError("page checksum mismatch")
            payload = json.loads(page_bytes)
            if payload.get("page_number") != expected_page:
                raise ValueError("page number mismatch")
            rows = payload.get("data")
            if not isinstance(rows, list) or len(rows) != page_record.get("rows"):
                raise ValueError("page row count mismatch")
            for row in rows:
                if not isinstance(row, dict):
                    raise ValueError("invalid order row shape")
                rows_seen += 1
                purchased_on = local_date(row.get("inserted_at"))
                if purchased_on is None:
                    continue
                candidate_names = [
                    name for name, test_start in starts.items()
                    if purchased_on < test_start
                ]
                if not candidate_names:
                    # For rows on/after every candidate start, do not inspect
                    # status or customer fields; these are reserved-period data.
                    continue
                # Eligibility only: current validity status and customer ID for
                # pre-start orders. No label-period behavior or labels are read.
                if row.get("status") not in (3, "3"):
                    continue
                customer = row.get("customer")
                customer_id = customer.get("customer_id") if isinstance(customer, dict) else None
                if customer_id is None or str(customer_id).strip() == "":
                    continue
                pseudonym = pseudonymize_id(
                    customer_id, key=hmac_key, namespace="xoaif/customer/v1"
                )
                for name in candidate_names:
                    cohorts[name].add(pseudonym)
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"Eligibility count stopped ({type(exc).__name__}); no source values printed.")
        return 2

    if rows_seen != manifest.get("row_count"):
        print("Eligibility count stopped: row total did not match manifest.")
        return 2

    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    split_hash = ""
    threshold = 0
    if args.record:
        config_path = PROJECT_ROOT / "config" / "split.yaml"
        lock_path = PROJECT_ROOT / "config" / "split.lock.json"
        try:
            config_bytes = config_path.read_bytes()
            config = yaml.safe_load(config_bytes)
            lock = json.loads(lock_path.read_text(encoding="utf-8"))
            split_hash = hashlib.sha256(config_bytes).hexdigest()
            threshold = int(config["min_test_eligible_customers"])
            configured_starts = {
                name: date.fromisoformat(str(value))
                for name, value in config["eligibility_preflight_candidates"].items()
            }
            if (
                config.get("status") != "locked"
                or config.get("snapshot_id") != args.snapshot_id
                or split_hash != lock.get("config_sha256")
                or manifest_hash != lock.get("snapshot_manifest_sha256")
                or manifest_hash != config.get("snapshot_manifest_sha256")
                or configured_starts != starts
            ):
                raise ValueError("split, snapshot, or scenarios do not match the lock")
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
            print(f"Eligibility record stopped ({type(exc).__name__}); no record was written.")
            return 2

    print(f"Snapshot: {args.snapshot_id}; rows checksum-verified: {rows_seen}")
    print(f"Manifest SHA-256: {manifest_hash}")
    print("Eligible = distinct customers with >=1 status-3 purchase before scenario test_start.")
    for name, test_start in args.scenario:
        count = len(cohorts[name])
        suffix = f"; threshold={threshold}; passed={count >= threshold}" if args.record else ""
        print(f"{name}; test_start={test_start.isoformat()}; eligible_customers={count}{suffix}")
    print("No labels, post-start behavior, amounts, order IDs, customer IDs, or pseudonyms were output.")

    if args.record:
        output_dir = PROJECT_ROOT / "outputs" / "tables"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "eligibility_preflight.csv"
        with output_path.open("w", encoding="utf-8-sig", newline="") as handle:
            import csv

            writer = csv.writer(handle)
            writer.writerow(["candidate", "test_start", "eligible_customers", "minimum", "passed"])
            for name, test_start in args.scenario:
                count = len(cohorts[name])
                writer.writerow([name, test_start.isoformat(), count, threshold, str(count >= threshold).lower()])
        log_path = PROJECT_ROOT / "outputs" / "logs" / "reserved_access.jsonl"
        for name, _ in args.scenario:
            record_reserved_access(
                log_path,
                kind="eligibility_count",
                step=f"preflight_{name}",
                split_hash=split_hash,
                split_locked=True,
            )
        print(f"Aggregate eligibility counts recorded: {output_path.relative_to(PROJECT_ROOT)}")
        print(f"Reserved-data metadata log updated: {log_path.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
