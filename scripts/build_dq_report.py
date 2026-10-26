"""Build an aggregate, value-free data-quality report from a feasibility profile."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import re
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROFILE_ROOT = PROJECT_ROOT / "data" / "restricted"
SNAPSHOT_ID_PATTERN = re.compile(r"\d{8}T\d{6}Z\Z")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot-id", required=True)
    args = parser.parse_args()
    if not SNAPSHOT_ID_PATTERN.fullmatch(args.snapshot_id):
        parser.error("--snapshot-id must use YYYYMMDDTHHMMSSZ format")

    profile_path = PROFILE_ROOT / f"feasibility_{args.snapshot_id}.json"
    try:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"DQ report stopped ({type(exc).__name__}); no source values printed.")
        return 2
    if profile.get("snapshot_id") != args.snapshot_id:
        print("DQ report stopped: profile snapshot ID did not match.")
        return 2

    counts = profile.get("field_presence_counts")
    order_count = profile.get("order_count")
    if not isinstance(counts, dict) or not isinstance(order_count, int) or order_count <= 0:
        print("DQ report stopped: profile counts were incomplete.")
        return 2

    item_rows = counts.get("item_rows")
    if not isinstance(item_rows, int):
        print("DQ report stopped: item-row count was unavailable.")
        return 2

    definitions = [
        ("fact_orders", "status", order_count, counts.get("present_status"), "Current status only; valid-purchase rule is status 3."),
        ("fact_orders", "inserted_at", order_count, counts.get("present_inserted_at"), "Owner decision: source timestamp is UTC; convert to Asia/Ho_Chi_Minh for calendar dates."),
        ("fact_orders", "updated_at", order_count, counts.get("present_updated_at"), "Not used to construct historical labels or features."),
        ("fact_orders", "customer_id", order_count, counts.get("present_customer.customer_id"), "Missing customer IDs excluded from customer-level analysis."),
        ("fact_orders", "items_nonempty", order_count, counts.get("nonempty_items"), "Orders without item lines excluded from basket analysis."),
        ("fact_order_items", "product_id", item_rows, counts.get("item_rows_with_product_id"), "Basket rules group variations by product_id."),
        ("fact_order_items", "variation_id", item_rows, counts.get("item_rows_with_variation_id"), "No direct variation identifiers in shared outputs."),
    ]

    rows: list[dict[str, object]] = []
    for entity, field, total, present, action in definitions:
        if not isinstance(present, int) or present < 0 or present > total:
            print(f"DQ report stopped: profile count for {entity}.{field} was invalid.")
            return 2
        missing = total - present
        rows.append(
            {
                "snapshot_id": args.snapshot_id,
                "entity": entity,
                "field": field,
                "total_records": total,
                "present_records": present,
                "missing_records": missing,
                "missing_pct": f"{missing / total * 100:.2f}",
                "handling": action,
            }
        )

    output_dir = PROJECT_ROOT / "outputs" / "tables"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "dq_report.csv"
    fieldnames = list(rows[0])
    with output_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"DQ report written: {output_path.relative_to(PROJECT_ROOT)}")
    print(f"Snapshot: {args.snapshot_id}; orders: {order_count}; item rows: {item_rows}")
    print("Only aggregate field-presence counts were used; no record values were read.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
