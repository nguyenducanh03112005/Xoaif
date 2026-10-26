"""Download a local, paginated Pancake orders snapshot with integrity metadata."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ingest.client import PancakeAPIError, PancakeClient
from ingest.settings import load_settings

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = PROJECT_ROOT / "data" / "raw" / "pancake_orders"


def write_json(path: Path, payload: Any) -> str:
    body = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    path.write_bytes(body)
    return hashlib.sha256(body).hexdigest()


def get_integer(payload: dict[str, Any], key: str, *, minimum: int = 0) -> int:
    value = payload.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"API response metadata field {key} was invalid.")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--max-pages", type=int, default=5000)
    args = parser.parse_args()
    if args.page_size < 1 or args.max_pages < 1:
        parser.error("--page-size and --max-pages must be positive")

    try:
        settings = load_settings()
    except ValueError as exc:
        print(f"Snapshot not started: {exc}")
        return 2

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    snapshot_dir = RAW_ROOT / run_id
    try:
        snapshot_dir.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        print("Snapshot not started: run directory already exists.")
        return 2

    started_at = datetime.now(timezone.utc).isoformat()
    manifest: dict[str, Any] = {
        "format_version": 1,
        "snapshot_id": run_id,
        "source": "pancake_pos",
        "shop_id": settings.shop_id,
        "endpoint": "GET /shops/{SHOP_ID}/orders",
        "filters": None,
        "pagination": {"page_size_requested": args.page_size},
        "started_at_utc": started_at,
        "status": "running",
        "pages": [],
        "integrity": {
            "page_metadata_consistent": None,
            "unique_order_ids": None,
            "row_count_matches_total_entries": None,
        },
        "consistency_note": (
            "The API did not provide a snapshot token. Stable page metadata and unique IDs "
            "are checked, but concurrent source edits during extraction cannot be ruled out."
        ),
    }
    manifest_path = snapshot_dir / "manifest.json"
    write_json(manifest_path, manifest)

    try:
        client = PancakeClient(settings)
        first_payload = client.list_orders(
            settings.shop_id,
            page_number=1,
            page_size=args.page_size,
        )
        total_pages = get_integer(first_payload, "total_pages", minimum=1)
        total_entries = get_integer(first_payload, "total_entries")
        if total_pages > args.max_pages:
            raise ValueError("API result exceeds the configured maximum page count.")

        manifest["pagination"].update(
            {
                "page_size_effective": get_integer(first_payload, "page_size", minimum=1),
                "total_pages": total_pages,
                "total_entries": total_entries,
            }
        )
        order_ids: set[str] = set()
        extracted_rows = 0
        page_hashes: list[dict[str, Any]] = []

        for page_number in range(1, total_pages + 1):
            payload = first_payload if page_number == 1 else client.list_orders(
                settings.shop_id,
                page_number=page_number,
                page_size=args.page_size,
            )
            if not isinstance(payload, dict) or payload.get("success") is not True:
                raise ValueError("API returned an invalid orders response.")
            if get_integer(payload, "page_number", minimum=1) != page_number:
                raise ValueError("API response page number did not match the request.")
            if get_integer(payload, "page_size", minimum=1) != manifest["pagination"]["page_size_effective"]:
                raise ValueError("API page size changed during snapshot extraction.")
            if get_integer(payload, "total_pages", minimum=1) != total_pages:
                raise ValueError("API total page count changed during snapshot extraction.")
            if get_integer(payload, "total_entries") != total_entries:
                raise ValueError("API total entry count changed during snapshot extraction.")

            rows = payload.get("data")
            if not isinstance(rows, list) or len(rows) > args.page_size:
                raise ValueError("API data page was missing or exceeded the requested page size.")
            for row in rows:
                if not isinstance(row, dict) or row.get("id") is None:
                    raise ValueError("API returned an order without a stable ID.")
                order_id = str(row["id"])
                if order_id in order_ids:
                    raise ValueError("Duplicate order IDs appeared across API pages.")
                order_ids.add(order_id)

            page_name = f"page_{page_number:06d}.json"
            page_hash = write_json(snapshot_dir / page_name, payload)
            page_hashes.append({"file": page_name, "sha256": page_hash, "rows": len(rows)})
            extracted_rows += len(rows)
            if page_number < total_pages:
                time.sleep(0.25)

        if extracted_rows != total_entries:
            raise ValueError("Extracted row count did not match API total_entries.")

        manifest["pages"] = page_hashes
        manifest["row_count"] = extracted_rows
        manifest["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        manifest["integrity"] = {
            "page_metadata_consistent": True,
            "unique_order_ids": True,
            "row_count_matches_total_entries": True,
        }
        manifest["status"] = "complete"
        write_json(manifest_path, manifest)
    except (PancakeAPIError, ValueError, OSError) as exc:
        manifest["status"] = "failed"
        manifest["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        manifest["error_type"] = type(exc).__name__
        write_json(manifest_path, manifest)
        print(f"Snapshot failed ({type(exc).__name__}); see local manifest for status.")
        return 1

    print(f"Snapshot complete: {run_id}")
    print(f"Pages: {total_pages}; order records: {extracted_rows}")
    print(f"Local restricted path: {snapshot_dir.relative_to(PROJECT_ROOT)}")
    print("No order/customer field values were printed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
