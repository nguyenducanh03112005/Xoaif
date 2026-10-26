"""Verify a completed raw snapshot and produce a value-free feasibility profile."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = PROJECT_ROOT / "data" / "raw" / "pancake_orders"
RESTRICTED_ROOT = PROJECT_ROOT / "data" / "restricted"


def parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def timestamp_has_timezone(value: Any) -> bool | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).tzinfo is not None
    except ValueError:
        return None


def count_present(record: dict[str, Any], key: str) -> bool:
    return key in record and record[key] is not None and record[key] != ""


def main() -> int:
    snapshot_dirs = sorted(
        (path for path in RAW_ROOT.iterdir() if path.is_dir()),
        key=lambda path: path.name,
    ) if RAW_ROOT.exists() else []
    if not snapshot_dirs:
        print("No raw snapshot directory found.")
        return 2

    snapshot_dir = snapshot_dirs[-1]
    manifest_path = snapshot_dir / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        print("Snapshot manifest is missing or invalid.")
        return 2
    if manifest.get("status") != "complete":
        print("Snapshot is not marked complete; refusing to profile it.")
        return 2

    page_records = manifest.get("pages")
    if not isinstance(page_records, list) or not page_records:
        print("Snapshot manifest has no page checksums.")
        return 2

    totals: Counter[str] = Counter()
    seen_ids: set[str] = set()
    order_count = 0
    created_times: list[datetime] = []
    updated_times: list[datetime] = []
    status_event_timestamps = 0
    status_event_count = 0
    status_history_latest_matches_current = 0
    status_history_monotonic_orders = 0
    status_history_ascending_orders = 0
    status_history_descending_orders = 0
    status_history_all_same_timestamp_orders = 0
    status_history_contains_current = 0
    status_history_last_item_matches_current = 0
    status_event_timestamps_with_offset = 0
    status_event_timestamps_without_offset = 0
    order_updated_after_latest_status_event = 0
    order_updated_equal_latest_status_event = 0
    order_updated_before_latest_status_event = 0

    try:
        for expected_page, page_record in enumerate(page_records, start=1):
            page_path = snapshot_dir / page_record["file"]
            raw_page = page_path.read_bytes()
            if hashlib.sha256(raw_page).hexdigest() != page_record.get("sha256"):
                raise ValueError("A page checksum did not match the manifest.")
            payload = json.loads(raw_page)
            for key, expected in (
                ("page_number", expected_page),
                ("page_size", manifest["pagination"]["page_size_effective"]),
                ("total_pages", manifest["pagination"]["total_pages"]),
                ("total_entries", manifest["pagination"]["total_entries"]),
            ):
                if payload.get(key) != expected:
                    raise ValueError("Page metadata did not match the snapshot manifest.")
            rows = payload.get("data")
            if not isinstance(rows, list) or len(rows) != page_record.get("rows"):
                raise ValueError("Page row count did not match the snapshot manifest.")

            for row in rows:
                if not isinstance(row, dict) or row.get("id") is None:
                    raise ValueError("An order record was missing its stable ID.")
                order_id = str(row["id"])
                if order_id in seen_ids:
                    raise ValueError("Duplicate order IDs were found in the snapshot.")
                seen_ids.add(order_id)
                order_count += 1

                for field in ("id", "status", "inserted_at", "updated_at", "customer", "items", "status_history", "histories"):
                    if count_present(row, field):
                        totals[f"present_{field}"] += 1
                for field in ("status_history", "histories", "items"):
                    value = row.get(field)
                    if isinstance(value, list) and value:
                        totals[f"nonempty_{field}"] += 1

                customer = row.get("customer")
                if isinstance(customer, dict) and count_present(customer, "customer_id"):
                    totals["present_customer.customer_id"] += 1
                items = row.get("items")
                if isinstance(items, list):
                    for item in items:
                        if not isinstance(item, dict):
                            totals["invalid_item_shapes"] += 1
                            continue
                        totals["item_rows"] += 1
                        if count_present(item, "product_id"):
                            totals["item_rows_with_product_id"] += 1
                        if count_present(item, "variation_id"):
                            totals["item_rows_with_variation_id"] += 1

                status_history = row.get("status_history")
                if isinstance(status_history, list):
                    dated_events: list[tuple[datetime, dict[str, Any]]] = []
                    history_statuses: list[Any] = []
                    for event in status_history:
                        if not isinstance(event, dict):
                            totals["invalid_status_history_shapes"] += 1
                            continue
                        status_event_count += 1
                        event_time = parse_timestamp(event.get("updated_at"))
                        if event_time is not None:
                            status_event_timestamps += 1
                            dated_events.append((event_time, event))
                            if timestamp_has_timezone(event.get("updated_at")):
                                status_event_timestamps_with_offset += 1
                            else:
                                status_event_timestamps_without_offset += 1
                        if count_present(event, "status"):
                            history_statuses.append(event["status"])
                        if not count_present(event, "status"):
                            totals["status_history_events_missing_status"] += 1
                    if row.get("status") in history_statuses:
                        status_history_contains_current += 1
                    if status_history and isinstance(status_history[-1], dict):
                        if status_history[-1].get("status") == row.get("status"):
                            status_history_last_item_matches_current += 1
                    if len(dated_events) == len(status_history) and dated_events:
                        event_times = [item[0] for item in dated_events]
                        ascending = all(a <= b for a, b in zip(event_times, event_times[1:]))
                        descending = all(a >= b for a, b in zip(event_times, event_times[1:]))
                        if ascending or descending:
                            status_history_monotonic_orders += 1
                        if ascending and not descending:
                            status_history_ascending_orders += 1
                        elif descending and not ascending:
                            status_history_descending_orders += 1
                        elif ascending and descending:
                            status_history_all_same_timestamp_orders += 1
                        latest_event = max(dated_events, key=lambda item: item[0])[1]
                        if row.get("status") is not None and latest_event.get("status") == row.get("status"):
                            status_history_latest_matches_current += 1
                        order_updated = parse_timestamp(row.get("updated_at"))
                        if order_updated is not None:
                            if order_updated > max(event_times):
                                order_updated_after_latest_status_event += 1
                            elif order_updated == max(event_times):
                                order_updated_equal_latest_status_event += 1
                            else:
                                order_updated_before_latest_status_event += 1

                created = parse_timestamp(row.get("inserted_at"))
                updated = parse_timestamp(row.get("updated_at"))
                if created is not None:
                    created_times.append(created)
                    if timestamp_has_timezone(row.get("inserted_at")) is True:
                        totals["order_inserted_at_with_timezone_offset"] += 1
                    elif timestamp_has_timezone(row.get("inserted_at")) is False:
                        totals["order_inserted_at_without_timezone_offset"] += 1
                if updated is not None:
                    updated_times.append(updated)
                    if timestamp_has_timezone(row.get("updated_at")) is True:
                        totals["order_updated_at_with_timezone_offset"] += 1
                    elif timestamp_has_timezone(row.get("updated_at")) is False:
                        totals["order_updated_at_without_timezone_offset"] += 1
    except (OSError, KeyError, TypeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Snapshot verification failed ({type(exc).__name__}); no profile was written.")
        return 1

    expected_rows = manifest.get("row_count")
    expected_entries = manifest.get("pagination", {}).get("total_entries")
    if order_count != expected_rows or order_count != expected_entries:
        print("Snapshot row totals did not match the manifest; no profile was written.")
        return 1

    def utc_range(values: list[datetime]) -> dict[str, str | None]:
        if not values:
            return {"min": None, "max": None}
        return {"min": min(values).isoformat(), "max": max(values).isoformat()}

    profile = {
        "snapshot_id": manifest["snapshot_id"],
        "snapshot_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "profiled_at_utc": datetime.now(timezone.utc).isoformat(),
        "profile_type": "source_feasibility_only_no_behavior_metrics",
        "order_count": order_count,
        "field_presence_counts": dict(sorted(totals.items())),
        "status_history_event_count": status_event_count,
        "status_history_events_with_parseable_updated_at": status_event_timestamps,
        "orders_with_monotonic_status_history_timestamps": status_history_monotonic_orders,
        "orders_with_ascending_status_history_timestamps": status_history_ascending_orders,
        "orders_with_descending_status_history_timestamps": status_history_descending_orders,
        "orders_with_all_status_history_timestamps_equal": status_history_all_same_timestamp_orders,
        "orders_where_latest_dated_status_matches_current_status": status_history_latest_matches_current,
        "orders_where_current_status_appears_anywhere_in_history": status_history_contains_current,
        "orders_where_last_list_item_status_matches_current": status_history_last_item_matches_current,
        "status_history_event_timestamps_with_timezone_offset": status_event_timestamps_with_offset,
        "status_history_event_timestamps_without_timezone_offset": status_event_timestamps_without_offset,
        "orders_order_updated_after_latest_status_event": order_updated_after_latest_status_event,
        "orders_order_updated_equal_latest_status_event": order_updated_equal_latest_status_event,
        "orders_order_updated_before_latest_status_event": order_updated_before_latest_status_event,
        "inserted_at_normalized_range": utc_range(created_times),
        "updated_at_normalized_range": utc_range(updated_times),
        "timezone_note": "Naive source timestamps were interpreted as UTC for parseability only; timezone semantics remain unverified.",
        "excluded": [
            "status distributions",
            "sales totals or trends",
            "customer purchase frequencies or recency",
            "return/repeat labels",
            "product association metrics",
            "all record-level values and identifiers",
        ],
    }

    RESTRICTED_ROOT.mkdir(parents=True, exist_ok=True)
    output_path = RESTRICTED_ROOT / f"feasibility_{manifest['snapshot_id']}.json"
    output_path.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Snapshot verified: {manifest['snapshot_id']}")
    print(f"Order records verified: {order_count}")
    print(f"Pages/checksums verified: {len(page_records)}")
    print(f"Non-empty status-history records: {totals['nonempty_status_history']}")
    print(f"Status-history event timestamps parsed: {status_event_timestamps}/{status_event_count}")
    print(f"Orders with monotonic status-history timestamps: {status_history_monotonic_orders}")
    print(f"Orders with ascending status-history timestamps: {status_history_ascending_orders}")
    print(f"Orders with descending status-history timestamps: {status_history_descending_orders}")
    print(f"Orders where latest dated status matches current: {status_history_latest_matches_current}")
    print(f"Orders where current status appears anywhere in history: {status_history_contains_current}")
    print(f"History event timestamps with timezone offset: {status_event_timestamps_with_offset}")
    print(f"History event timestamps without timezone offset: {status_event_timestamps_without_offset}")
    print(f"Feasibility profile: {output_path.relative_to(PROJECT_ROOT)}")
    print("No customer, order, product, or free-text values were printed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
