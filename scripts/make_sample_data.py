"""Generate deterministic, fully synthetic Xoaif-shaped demonstration CSVs."""

from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path
import random
import re


ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "data" / "sample"
SEED = 20261026
ORDER_COUNT = 200
DEV_START = date(2024, 4, 1)
DEV_END_EXCLUSIVE = date(2025, 10, 22)
SYNTHETIC_REVENUE_PER_STATUS_3_ORDER_VND = 100_000

FACT_ORDERS_FIELDS = (
    "order_key",
    "customer_key",
    "local_date",
    "status_code",
    "distinct_product_count",
)
FACT_ORDER_ITEMS_SAMPLE_FIELDS = ("order_key", "product_key", "is_gift_line")
MONTHLY_FIELDS = ("month", "recognized_revenue_vnd", "orders")
HMAC_LIKE = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{64}(?![0-9A-Fa-f])")


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _month_range() -> list[str]:
    months: list[str] = []
    year, month = DEV_START.year, DEV_START.month
    final_year, final_month = (DEV_END_EXCLUSIVE - timedelta(days=1)).year, (
        DEV_END_EXCLUSIVE - timedelta(days=1)
    ).month
    while (year, month) <= (final_year, final_month):
        months.append(f"{year:04d}-{month:02d}")
        if month == 12:
            year, month = year + 1, 1
        else:
            month += 1
    return months


def _generate_rows() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    rng = random.Random(SEED)
    date_span = (DEV_END_EXCLUSIVE - DEV_START).days
    product_catalog = [f"SAMPLE-PRD-{number:03d}" for number in range(1, 25)]
    orders: list[dict[str, object]] = []
    order_items: list[dict[str, object]] = []
    monthly_order_counts = {month: 0 for month in _month_range()}

    for order_number in range(1, ORDER_COUNT + 1):
        order_key = f"SAMPLE-ORD-{order_number:04d}"
        customer_key = f"SAMPLE-CUS-{rng.randint(1, 50):04d}"
        local_date = DEV_START + timedelta(days=rng.randrange(date_span))
        status_code = rng.choices((3, 5, 6), weights=(70, 10, 20), k=1)[0]
        product_count = rng.randint(2, 6)
        product_keys = sorted(rng.sample(product_catalog, product_count))

        orders.append(
            {
                "order_key": order_key,
                "customer_key": customer_key,
                "local_date": local_date.isoformat(),
                "status_code": status_code,
                "distinct_product_count": product_count,
            }
        )
        if status_code == 3:
            monthly_order_counts[local_date.strftime("%Y-%m")] += 1

        for line_number, product_key in enumerate(product_keys, start=1):
            is_gift_line = (order_number * 11 + line_number * 7) % 37 == 0
            order_items.append(
                {
                    "order_key": order_key,
                    "product_key": product_key,
                    "is_gift_line": str(is_gift_line).lower(),
                }
            )

    monthly = [
        {
            "month": month,
            "recognized_revenue_vnd": count * SYNTHETIC_REVENUE_PER_STATUS_3_ORDER_VND,
            "orders": count,
        }
        for month, count in monthly_order_counts.items()
    ]
    return orders, order_items, monthly


def _read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def _self_check() -> tuple[int, int, int]:
    order_headers, orders = _read_csv(SAMPLE_DIR / "sample_orders.csv")
    item_headers, items = _read_csv(SAMPLE_DIR / "sample_order_items.csv")
    monthly_headers, monthly = _read_csv(SAMPLE_DIR / "sample_aggregates_monthly.csv")

    if order_headers != list(FACT_ORDERS_FIELDS):
        raise ValueError("sample_orders.csv columns do not match the published fact_orders schema")
    if item_headers != list(FACT_ORDER_ITEMS_SAMPLE_FIELDS):
        raise ValueError("sample_order_items.csv columns do not match the declared sample schema")
    if monthly_headers != list(MONTHLY_FIELDS):
        raise ValueError("sample_aggregates_monthly.csv columns do not match dashboard_sales_monthly.csv")
    if len(orders) != ORDER_COUNT:
        raise ValueError(f"Expected {ORDER_COUNT} sample orders, found {len(orders)}")

    order_keys: set[str] = set()
    item_counts: dict[str, int] = {}
    allowed_statuses = {3, 5, 6}
    for row in orders:
        order_key = row["order_key"]
        if not re.fullmatch(r"SAMPLE-ORD-\d{4}", order_key):
            raise ValueError("Sample order key has an unexpected format")
        if not re.fullmatch(r"SAMPLE-CUS-\d{4}", row["customer_key"]):
            raise ValueError("Sample customer key has an unexpected format")
        if order_key in order_keys:
            raise ValueError("Duplicate sample order key")
        order_keys.add(order_key)

        try:
            order_date = date.fromisoformat(row["local_date"])
            status_code = int(row["status_code"])
            product_count = int(row["distinct_product_count"])
        except ValueError as exc:
            raise ValueError("A sample fact_orders value has the wrong type") from exc
        if not DEV_START <= order_date < DEV_END_EXCLUSIVE:
            raise ValueError("A sample order date falls outside the DEV interval")
        if order_date >= date(2025, 10, 22):
            raise ValueError("A sample order date is on or after 2025-10-22")
        if status_code not in allowed_statuses:
            raise ValueError("A sample status_code is outside {3, 5, 6}")
        if not 2 <= product_count <= 6:
            raise ValueError("A sample distinct_product_count is outside 2–6")

    gifts = 0
    for row in items:
        if row["order_key"] not in order_keys:
            raise ValueError("An item row refers to an unknown sample order")
        if not re.fullmatch(r"SAMPLE-PRD-\d{3}", row["product_key"]):
            raise ValueError("Sample product key has an unexpected format")
        if row["is_gift_line"] not in {"true", "false"}:
            raise ValueError("Sample is_gift_line must be a boolean string")
        item_counts[row["order_key"]] = item_counts.get(row["order_key"], 0) + 1
        gifts += row["is_gift_line"] == "true"
    if set(item_counts) != order_keys or any(not 2 <= count <= 6 for count in item_counts.values()):
        raise ValueError("Each sample order must have between 2 and 6 item rows")
    if gifts == 0:
        raise ValueError("Expected several sample gift lines")

    status_3_orders = sum(int(row["status_code"]) == 3 for row in orders)
    monthly_orders = 0
    for row in monthly:
        if not re.fullmatch(r"\d{4}-\d{2}", row["month"]):
            raise ValueError("Monthly sample month must use YYYY-MM")
        try:
            month_start = date.fromisoformat(f"{row['month']}-01")
            revenue = int(row["recognized_revenue_vnd"])
            order_count = int(row["orders"])
        except ValueError as exc:
            raise ValueError("A monthly aggregate value has the wrong type") from exc
        if not DEV_START <= month_start < DEV_END_EXCLUSIVE:
            raise ValueError("A monthly sample date falls outside the DEV interval")
        if month_start >= date(2025, 10, 22):
            raise ValueError("A monthly sample date is on or after 2025-10-22")
        if revenue != order_count * SYNTHETIC_REVENUE_PER_STATUS_3_ORDER_VND:
            raise ValueError("Monthly synthetic revenue is inconsistent with its sample order count")
        monthly_orders += order_count
    if monthly_orders != status_3_orders:
        raise ValueError("Monthly sample orders do not match status-3 sample orders")

    for path in (
        SAMPLE_DIR / "sample_orders.csv",
        SAMPLE_DIR / "sample_order_items.csv",
        SAMPLE_DIR / "sample_aggregates_monthly.csv",
    ):
        contents = path.read_text(encoding="utf-8")
        if HMAC_LIKE.search(contents):
            raise ValueError(f"HMAC-shaped 64-hex value found in {path.name}")

    return len(orders), len(items), gifts


def main() -> int:
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    orders, items, monthly = _generate_rows()
    _write_csv(SAMPLE_DIR / "sample_orders.csv", FACT_ORDERS_FIELDS, orders)
    _write_csv(SAMPLE_DIR / "sample_order_items.csv", FACT_ORDER_ITEMS_SAMPLE_FIELDS, items)
    _write_csv(SAMPLE_DIR / "sample_aggregates_monthly.csv", MONTHLY_FIELDS, monthly)
    order_count, item_count, gift_count = _self_check()
    print(
        "Synthetic sample self-check passed: "
        f"{order_count} orders, {item_count} item rows, {gift_count} gift lines, "
        f"{len(monthly)} monthly rows."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
