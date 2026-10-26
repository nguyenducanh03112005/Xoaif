"""Profile the opening-date amendment and candidate money fields without labels/test behavior."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any
from zoneinfo import ZoneInfo

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ingest.analysis_amendment import load_analysis_amendment

RAW_ROOT = PROJECT_ROOT / "data" / "raw" / "pancake_orders"
TZ = ZoneInfo("Asia/Ho_Chi_Minh")
MONEY_WORDS = ("price", "amount", "discount", "shipping", "fee", "cash", "cod", "paid", "transfer", "collect", "refund")
ORDER_MONEY_FIELDS = {
    "advanced_platform_fee", "buyer_total_amount", "cash", "cod", "customer_pay_fee",
    "fee_marketplace", "money_to_collect", "partner_fee", "prepaid", "prepaid_by_point",
    "return_fee", "shipping_fee", "total_discount", "total_price",
    "total_price_after_sub_discount", "transfer_money",
}
TEST_NAME_PATTERN = re.compile(r"\b(test|sample|demo|init(?:ial)?|thử|mẫu|khởi\s*tạo)\b", re.IGNORECASE)


def parse_local_date(value: Any) -> date | None:
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
    return parsed.astimezone(TZ).date()


def status_code(value: Any) -> str:
    if isinstance(value, bool):
        return "<UNMAPPED>"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str) and value.strip().isdigit():
        return str(int(value.strip()))
    return "<UNMAPPED>"


def decimal_value(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float, Decimal)):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None
    if isinstance(value, str) and value.strip():
        try:
            return Decimal(value.strip().replace(",", ""))
        except InvalidOperation:
            return None
    return None


def present(value: Any) -> bool:
    return value is not None and value != ""


def iter_months(start: date, end_exclusive: date):
    current = date(start.year, start.month, 1)
    final = date(end_exclusive.year, end_exclusive.month, 1)
    while current <= final:
        yield current
        current = date(current.year + (current.month == 12), current.month % 12 + 1, 1)


def write_csv(path: Path, headers: list[str], rows: list[list[Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        writer.writerows(rows)


def main() -> int:
    try:
        split_path = PROJECT_ROOT / "config" / "split.yaml"
        split = yaml.safe_load(split_path.read_bytes())
        amendment, amendment_hash, split_lock_hash = load_analysis_amendment(PROJECT_ROOT)
        analysis_start = date.fromisoformat(str(amendment["analysis_start"]))
        test_start = date.fromisoformat(str(split["test_start"]))
        snapshot_id = str(split["snapshot_id"])
        snapshot_dir = RAW_ROOT / snapshot_id
        manifest_bytes = (snapshot_dir / "manifest.json").read_bytes()
        manifest = json.loads(manifest_bytes)
        if hashlib.sha256(manifest_bytes).hexdigest() != split["snapshot_manifest_sha256"]:
            raise ValueError("snapshot manifest does not match the locked digest")
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
        print(f"Analysis-start profile stopped ({type(exc).__name__}).")
        return 2

    monthly = Counter()
    effective_status = Counter()
    pre_status: dict[str, Counter[str]] = defaultdict(Counter)
    pre_dates: dict[str, list[date]] = defaultdict(list)
    pre_items = Counter()
    pre_customer = Counter()
    pre_zero_fields: dict[str, Counter[str]] = defaultdict(Counter)
    pre_name_hits = Counter()
    pre_money_field_names: set[str] = set()
    effective_money_field_names: set[str] = set()
    line_field_names: set[str] = set()
    values: dict[str, list[Decimal]] = defaultdict(list)
    field_presence: Counter[str] = Counter()
    pair_counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    line_reconcile: dict[str, Counter[str]] = defaultdict(Counter)
    rows_seen = 0
    pre_rows = 0
    effective_rows = 0
    effective_dates: list[date] = []

    try:
        for page_no, page_record in enumerate(manifest["pages"], start=1):
            page_path = (snapshot_dir / page_record["file"]).resolve()
            if not page_path.is_relative_to(snapshot_dir.resolve()):
                raise ValueError("snapshot page path escaped its directory")
            page_bytes = page_path.read_bytes()
            if hashlib.sha256(page_bytes).hexdigest() != page_record["sha256"]:
                raise ValueError("snapshot page checksum mismatch")
            payload = json.loads(page_bytes)
            if payload.get("page_number") != page_no or len(payload.get("data", [])) != page_record["rows"]:
                raise ValueError("snapshot page metadata or row count mismatch")
            for order in payload["data"]:
                rows_seen += 1
                if not isinstance(order, dict):
                    continue
                # Timestamp is the only order value inspected before deciding whether a row is pre-test.
                order_date = parse_local_date(order.get("inserted_at"))
                if order_date is None or order_date >= test_start:
                    continue
                month = date(order_date.year, order_date.month, 1)
                monthly[month] += 1

                if order_date < analysis_start:
                    pre_rows += 1
                    code = status_code(order.get("status"))
                    pre_status[code]["orders"] += 1
                    pre_dates[code].append(order_date)
                    customer = order.get("customer")
                    customer_id = customer.get("customer_id") if isinstance(customer, dict) else None
                    pre_customer[code + ("_present" if present(customer_id) else "_missing")] += 1
                    items = order.get("items")
                    item_rows = items if isinstance(items, list) else []
                    pre_items[code] += len(item_rows)

                    money_keys = set(order).intersection(ORDER_MONEY_FIELDS)
                    pre_money_field_names.update(money_keys)
                    for key in money_keys:
                        raw_money = order.get(key)
                        value = decimal_value(raw_money)
                        if value == 0:
                            pre_zero_fields[code][key] += 1
                    name_match = False
                    for item in item_rows:
                        if not isinstance(item, dict):
                            continue
                        item_names = [v for k, v in item.items() if "name" in k.lower() and isinstance(v, str)]
                        if any(TEST_NAME_PATTERN.search(v) for v in item_names):
                            name_match = True
                    if name_match:
                        pre_name_hits[code] += 1
                    continue

                effective_rows += 1
                effective_dates.append(order_date)
                code = status_code(order.get("status"))
                effective_status[code] += 1
                if code != "3":
                    continue

                keys = set(order).intersection(ORDER_MONEY_FIELDS)
                effective_money_field_names.update(keys)
                values_for_order: dict[str, Decimal] = {}
                for key in keys:
                    raw_money = order.get(key)
                    if present(raw_money):
                        field_presence[key] += 1
                    value = decimal_value(raw_money)
                    if value is not None:
                        values[key].append(value)
                        values_for_order[key] = value

                for left, right in (
                    ("total_price", "total_price_after_sub_discount"),
                    ("total_price", "total_discount"),
                    ("money_to_collect", "cash"),
                    ("money_to_collect", "cod"),
                    ("cash", "cod"),
                ):
                    if left in values_for_order and right in values_for_order:
                        pair_counts[(left, right)]["comparable"] += 1
                        a, b = values_for_order[left], values_for_order[right]
                        pair_counts[(left, right)]["equal"] += int(a == b)
                        pair_counts[(left, right)]["left_greater"] += int(a > b)
                        pair_counts[(left, right)]["left_less"] += int(a < b)
                for formula, target, candidate in (
                    (
                        "total_price_minus_total_discount",
                        "total_price_after_sub_discount",
                        values_for_order.get("total_price") - values_for_order.get("total_discount")
                        if "total_price" in values_for_order and "total_discount" in values_for_order else None,
                    ),
                    (
                        "total_price_after_sub_discount_plus_shipping",
                        "money_to_collect",
                        values_for_order.get("total_price_after_sub_discount") + values_for_order.get("shipping_fee")
                        if "total_price_after_sub_discount" in values_for_order and "shipping_fee" in values_for_order else None,
                    ),
                ):
                    if candidate is not None and target in values_for_order:
                        target_value = values_for_order[target]
                        pair_counts[(formula, target)]["comparable"] += 1
                        pair_counts[(formula, target)]["equal"] += int(candidate == target_value)
                        pair_counts[(formula, target)]["left_greater"] += int(candidate > target_value)
                        pair_counts[(formula, target)]["left_less"] += int(candidate < target_value)

                items = order.get("items")
                if not isinstance(items, list):
                    continue
                numeric_line_items: dict[str, Decimal] = defaultdict(Decimal)
                complete_formula: dict[str, bool] = {"price_x_quantity": True, "retail_price_x_quantity": True}
                formula_fields = {
                    "price_x_quantity": ("price", "quantity"),
                    "retail_price_x_quantity": ("retail_price", "quantity"),
                }
                for item in items:
                    if not isinstance(item, dict):
                        for formula in complete_formula:
                            complete_formula[formula] = False
                        continue
                    line_field_names.update(k for k in item if any(word in k.lower() for word in MONEY_WORDS + ("quantity", "return")))
                    for formula, (price_field, quantity_field) in formula_fields.items():
                        price = decimal_value(item.get(price_field))
                        quantity = decimal_value(item.get(quantity_field))
                        if price is None or quantity is None:
                            complete_formula[formula] = False
                        else:
                            numeric_line_items[formula] += price * quantity
                for formula, (price_field, quantity_field) in formula_fields.items():
                    target = "total_price_after_sub_discount" if "total_price_after_sub_discount" in values_for_order and formula == "price_x_quantity" else "total_price"
                    if complete_formula[formula] and target in values_for_order:
                        line_reconcile[formula + "_vs_" + target]["comparable"] += 1
                        line_reconcile[formula + "_vs_" + target]["equal"] += int(numeric_line_items[formula] == values_for_order[target])
                        line_reconcile[formula + "_vs_" + target]["different"] += int(numeric_line_items[formula] != values_for_order[target])

        if rows_seen != manifest.get("row_count"):
            raise ValueError("snapshot row reconciliation failed")
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"Analysis-start profile stopped ({type(exc).__name__}).")
        return 2

    table_dir = PROJECT_ROOT / "outputs" / "tables"
    ordered_months = list(iter_months(min(monthly), test_start)) if monthly else []
    write_csv(
        table_dir / "day1_monthly_orders_all_status.csv",
        ["month", "all_status_orders"],
        [[month.isoformat()[:7], monthly.get(month, 0)] for month in ordered_months],
    )

    pre_rows_out = []
    for code in sorted(pre_status, key=lambda value: (value == "<UNMAPPED>", value)):
        dates = pre_dates[code]
        row_count = pre_status[code]["orders"]
        pre_rows_out.append([
            code, row_count, min(dates).isoformat(), max(dates).isoformat(), pre_items[code],
            pre_customer[code + "_present"], pre_customer[code + "_missing"],
            "; ".join(f"{key}={n}" for key, n in sorted(pre_zero_fields[code].items())),
            pre_name_hits[code],
        ])
    write_csv(
        table_dir / "pre_analysis_orders_by_status.csv",
        ["status_code", "orders", "date_min", "date_max", "item_rows", "orders_with_customer_id", "orders_without_customer_id", "orders_with_zero_money_fields", "orders_with_test_like_product_name"],
        pre_rows_out,
    )

    money_fields = sorted(effective_money_field_names)
    money_rows = []
    status3_count = effective_status.get("3", 0)
    for field in money_fields:
        nums = values.get(field, [])
        zeros = sum(value == 0 for value in nums)
        negatives = sum(value < 0 for value in nums)
        present_count = field_presence[field]
        missing_count = max(status3_count - present_count, 0)
        nonnumeric_count = max(present_count - len(nums), 0)
        money_rows.append([field, present_count, len(nums), missing_count, nonnumeric_count, zeros, negatives])
    write_csv(
        table_dir / "money_candidate_profile_status3.csv",
        ["field", "present_values", "numeric_values", "missing_values", "non_numeric_values", "zero_values", "negative_values"],
        money_rows,
    )
    relation_rows = []
    for (left, right), counts in sorted(pair_counts.items()):
        relation_rows.append([left, right, counts["comparable"], counts["equal"], counts["left_greater"], counts["left_less"]])
    for formula, counts in sorted(line_reconcile.items()):
        relation_rows.append([formula, "order_field", counts["comparable"], counts["equal"], "", counts["different"]])
    write_csv(
        table_dir / "money_candidate_relationships_status3.csv",
        ["left_or_formula", "right_or_target", "comparable_orders", "equal_orders", "left_greater_orders", "left_less_or_different_orders"],
        relation_rows,
    )

    summary = {
        "snapshot_id": snapshot_id,
        "snapshot_order_count": rows_seen,
        "analysis_start": analysis_start.isoformat(),
        "development_exclusive_end": test_start.isoformat(),
        "pre_analysis_order_count": pre_rows,
        "pre_analysis_status_counts": {code: counts["orders"] for code, counts in sorted(pre_status.items())},
        "pre_analysis_date_min": min((d for values_for_status in pre_dates.values() for d in values_for_status), default=None).isoformat() if pre_rows else None,
        "pre_analysis_date_max": max((d for values_for_status in pre_dates.values() for d in values_for_status), default=None).isoformat() if pre_rows else None,
        "effective_development_order_count": effective_rows,
        "effective_development_status_counts": dict(sorted(effective_status.items())),
        "effective_development_status3_count": status3_count,
        "effective_development_date_min": min(effective_dates).isoformat() if effective_dates else None,
        "effective_development_date_max": max(effective_dates).isoformat() if effective_dates else None,
        "pre_analysis_item_rows": sum(pre_items.values()),
        "pre_analysis_customer_id_present_orders": sum(v for k, v in pre_customer.items() if k.endswith("_present")),
        "pre_analysis_customer_id_missing_orders": sum(v for k, v in pre_customer.items() if k.endswith("_missing")),
        "pre_analysis_orders_with_test_like_product_name": sum(pre_name_hits.values()),
        "money_candidate_order_fields": money_fields,
        "line_item_candidate_fields": sorted(line_field_names),
        "test_labels_loaded": False,
        "analysis_amendment_sha256": amendment_hash,
        "split_lock_sha256": split_lock_hash,
    }
    summary_path = table_dir / "day1_analysis_start_profile.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Profiled {rows_seen} timestamp-screened snapshot rows; no fields other than inserted_at were accessed at/after test_start.")
    print(f"Pre-analysis orders: {pre_rows}; effective development orders [{analysis_start}, {test_start}): {effective_rows}; status-3: {status3_count}.")
    print(f"Candidate money fields profiled on effective-development status-3 orders: {len(money_fields)}; test labels were not loaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
