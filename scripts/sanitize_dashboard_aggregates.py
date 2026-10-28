"""Suppress low-count cells in reviewed dashboard aggregate tables only."""

from __future__ import annotations

import csv
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
THRESHOLD = 10
PRODUCT_OTHER_LABEL = "Khác — từng sản phẩm dưới 10 lượt đơn"
PROVINCE_OTHER_LABEL = "Các tỉnh khác — từng tỉnh dưới 10 đơn"
GIFT_COUNT_COLUMNS = ("line_count", "distinct_order_count", "gift_line_count")


def _read_rows(path: Path, required: set[str]) -> tuple[list[str], list[dict[str, str]]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError(f"{path.name} has an unexpected schema.")
        return reader.fieldnames, list(reader)


def _integer(row: dict[str, str], column: str) -> int | None:
    value = row.get(column, "").strip()
    if not value:
        return None
    numeric = float(value)
    if not numeric.is_integer() or numeric < 0:
        raise ValueError(f"{column} must contain a non-negative integer.")
    return int(numeric)


def _sum_column(rows: list[dict[str, str]], column: str) -> str:
    values = [_integer(row, column) for row in rows]
    if any(value is None for value in values):
        raise ValueError(f"{column} is required to aggregate low-volume products.")
    return str(sum(value for value in values if value is not None))


def _write_rows(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    temporary_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="raise")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def _sanitize_products(tables: Path) -> int:
    path = tables / "dashboard_product_orders.csv"
    columns, rows = _read_rows(path, {"product_name", "line_count", "order_count", "quantity"})
    small: list[dict[str, str]] = []
    other_rows: list[dict[str, str]] = []
    visible: list[dict[str, str]] = []
    for row in rows:
        if row["product_name"] == PRODUCT_OTHER_LABEL:
            other_rows.append(row)
            continue
        count = _integer(row, "order_count")
        if count is None:
            raise ValueError("Product order count must be present before suppression.")
        (small if count < THRESHOLD else visible).append(row)

    grouped = small + other_rows
    if grouped:
        other = {
            "product_name": PRODUCT_OTHER_LABEL,
            "line_count": _sum_column(grouped, "line_count"),
            "order_count": "",
            "quantity": _sum_column(grouped, "quantity"),
        }
        visible.append(other)
    _write_rows(path, columns, visible)
    return len(small)


def _sanitize_statuses(tables: Path) -> int:
    path = tables / "dashboard_status_counts.csv"
    columns, rows = _read_rows(path, {"period", "status_code", "order_count"})
    by_period: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_period.setdefault(row["period"], []).append(row)

    suppressed = 0
    for period_rows in by_period.values():
        small = [
            row for row in period_rows
            if (count := _integer(row, "order_count")) is not None and count < THRESHOLD
        ]
        for row in small:
            row["order_count"] = ""
        suppressed += len(small)
        if len(small) == 1:
            companions = [
                (count, row) for row in period_rows
                if row not in small
                if (count := _integer(row, "order_count")) is not None and count >= THRESHOLD
            ]
            if companions:
                _, companion = min(companions, key=lambda item: item[0])
                companion["order_count"] = ""
                suppressed += 1
    _write_rows(path, columns, rows)
    return suppressed


def _sanitize_gift_audit(tables: Path) -> int:
    path = tables / "gift_line_audit.csv"
    columns, rows = _read_rows(path, set(GIFT_COUNT_COLUMNS))
    suppressed = 0
    for row in rows:
        values = {column: _integer(row, column) for column in GIFT_COUNT_COLUMNS}
        low_columns = {
            column for column, value in values.items()
            if value is not None and value < THRESHOLD
        }
        if _integer(row, "distinct_order_count") is not None and _integer(
            row, "distinct_order_count"
        ) < THRESHOLD:
            low_columns.update(GIFT_COUNT_COLUMNS)
        for column in low_columns:
            row[column] = ""
        suppressed += len(low_columns)

    for column in GIFT_COUNT_COLUMNS:
        low_rows = [
            row for row in rows
            if (count := _integer(row, column)) is not None and count < THRESHOLD
        ]
        if len(low_rows) == 1:
            companions = [
                (count, row) for row in rows
                if row not in low_rows
                if (count := _integer(row, column)) is not None and count >= THRESHOLD
            ]
            if companions:
                _, companion = min(companions, key=lambda item: item[0])
                companion[column] = ""
                suppressed += 1
    _write_rows(path, columns, rows)
    return suppressed


def _sanitize_provinces(tables: Path) -> int:
    """Group low-volume province rows without changing the locked source metrics."""
    path = tables / "dashboard_sales_province.csv"
    columns, rows = _read_rows(path, {"province", "recognized_revenue_vnd", "orders"})
    low: list[dict[str, str]] = []
    visible: list[dict[str, str]] = []
    for row in rows:
        if row["province"] == PROVINCE_OTHER_LABEL:
            low.append(row)
            continue
        count = _integer(row, "orders")
        if count is None:
            raise ValueError("Province order count must be present before grouping.")
        (low if row["province"] != "UNKNOWN" and count < THRESHOLD else visible).append(row)

    if low:
        revenue = sum(float(row["recognized_revenue_vnd"]) for row in low)
        orders = sum(_integer(row, "orders") or 0 for row in low)
        visible.append({
            "province": PROVINCE_OTHER_LABEL,
            "recognized_revenue_vnd": f"{revenue:.1f}",
            "orders": str(orders),
        })
    _write_rows(path, columns, visible)
    return len(low)


def sanitize_aggregate_tables(tables: Path = TABLES) -> dict[str, int]:
    """Transform only the three aggregate CSVs approved for small-cell handling."""
    for name in (
        "dashboard_product_orders.csv",
        "dashboard_status_counts.csv",
        "gift_line_audit.csv",
        "dashboard_sales_province.csv",
    ):
        if not (tables / name).is_file():
            raise FileNotFoundError(name)
    return {
        "product_rows_grouped": _sanitize_products(tables),
        "status_count_cells_suppressed": _sanitize_statuses(tables),
        "gift_count_cells_suppressed": _sanitize_gift_audit(tables),
        "province_rows_grouped": _sanitize_provinces(tables),
    }


def main() -> int:
    result = sanitize_aggregate_tables()
    print(
        "Aggregate suppression applied: "
        f"product rows grouped={result['product_rows_grouped']}; "
        f"status count cells suppressed={result['status_count_cells_suppressed']}; "
        f"gift count cells suppressed={result['gift_count_cells_suppressed']}; "
        f"province rows grouped={result['province_rows_grouped']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
