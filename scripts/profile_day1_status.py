"""Create a value-free current-order status count table from a verified snapshot."""

from __future__ import annotations

import csv
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
import re
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_ROOT = PROJECT_ROOT / "data" / "raw" / "pancake_orders"
ALLOWED_CODES = {0, 1, 3, 4, 5, 6}
NUMERIC_CODE = re.compile(r"\d+\Z")


def normalize_status(value: Any) -> str:
    """Return a safe status category; never serialize arbitrary source values."""
    if isinstance(value, bool):
        return "<NON_INTEGER>"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str) and NUMERIC_CODE.fullmatch(value.strip()):
        return str(int(value.strip()))
    if value is None:
        return "<MISSING>"
    return "<NON_INTEGER>"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-id", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"\d{8}T\d{6}Z", args.snapshot_id):
        parser.error("--snapshot-id must use YYYYMMDDTHHMMSSZ format")
    snapshot_id = args.snapshot_id
    snapshot_dir = SNAPSHOT_ROOT / snapshot_id
    manifest_path = snapshot_dir / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"Status profile stopped ({type(exc).__name__}); no source values printed.")
        return 2

    if manifest.get("snapshot_id") != snapshot_id or manifest.get("status") != "complete":
        print("Status profile stopped: expected complete snapshot was not found.")
        return 2

    counts: Counter[str] = Counter()
    total_rows = 0
    root = snapshot_dir.resolve()
    for page in manifest.get("pages", []):
        page_name = page.get("file")
        if not isinstance(page_name, str):
            print("Status profile stopped: invalid page entry in manifest.")
            return 2
        page_path = (snapshot_dir / page_name).resolve()
        if not page_path.is_relative_to(root):
            print("Status profile stopped: page path escaped the snapshot folder.")
            return 2
        try:
            page_bytes = page_path.read_bytes()
            if hashlib.sha256(page_bytes).hexdigest() != page.get("sha256"):
                print("Status profile stopped: a page checksum did not match the manifest.")
                return 2
            payload = json.loads(page_bytes)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            print(f"Status profile stopped ({type(exc).__name__}); no source values printed.")
            return 2

        rows = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(rows, list) or len(rows) != page.get("rows"):
            print("Status profile stopped: page row metadata did not match.")
            return 2
        for row in rows:
            if not isinstance(row, dict):
                counts["<NON_INTEGER>"] += 1
            else:
                counts[normalize_status(row.get("status"))] += 1
        total_rows += len(rows)

    if total_rows != manifest.get("row_count"):
        print("Status profile stopped: row count did not match the manifest.")
        return 2

    output_dir = PROJECT_ROOT / "outputs" / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "status_counts.csv"
    with output_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["status_code", "order_count", "valid_purchase_by_owner_rule", "decision"])
        for code in sorted(counts, key=lambda item: (item.startswith("<"), int(item) if NUMERIC_CODE.fullmatch(item) else item)):
            numeric = int(code) if NUMERIC_CODE.fullmatch(code) else None
            allowed = numeric in ALLOWED_CODES if numeric is not None else False
            valid_purchase = numeric == 3
            decision = (
                "valid purchase"
                if valid_purchase
                else "excluded by owner rule"
                if allowed
                else "unmapped code/category; excluded pending owner review"
            )
            writer.writerow([code, counts[code], str(valid_purchase).lower(), decision])

    unknown = {
        int(code): count
        for code, count in counts.items()
        if NUMERIC_CODE.fullmatch(code) and int(code) not in ALLOWED_CODES
    }
    print(f"Snapshot: {snapshot_id}; rows profiled: {total_rows}")
    print(f"Status counts written to {output_path.relative_to(PROJECT_ROOT)}")
    print("status_code,order_count,valid_purchase_by_owner_rule,decision")
    for code in sorted(counts, key=lambda item: (item.startswith("<"), int(item) if NUMERIC_CODE.fullmatch(item) else item)):
        numeric = int(code) if NUMERIC_CODE.fullmatch(code) else None
        valid_purchase = numeric == 3
        decision = "valid" if valid_purchase else "excluded" if numeric in ALLOWED_CODES else "unmapped/excluded"
        print(f"{code},{counts[code]},{str(valid_purchase).lower()},{decision}")
    print("No sales amounts, customer fields, or order-level values were read into output.")
    if unknown:
        unknown_text = ", ".join(f"{code} ({unknown[code]} orders)" for code in sorted(unknown))
        print(f"Owner review required for unmapped numeric status codes: {unknown_text}")
    for code in ("<MISSING>", "<NON_INTEGER>"):
        if counts[code]:
            print(f"Owner review required for {code}: {counts[code]} orders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
