from __future__ import annotations

import csv
from pathlib import Path

import pandas as pd

from scripts.sanitize_dashboard_aggregates import (
    GIFT_COUNT_COLUMNS,
    PRODUCT_OTHER_LABEL,
    PROVINCE_OTHER_LABEL,
    sanitize_aggregate_tables,
)


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"


def _read_table(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")


def test_reviewed_dashboard_aggregates_have_no_visible_counts_below_ten(tmp_path: Path) -> None:
    for name in (
        "dashboard_product_orders.csv",
        "dashboard_status_counts.csv",
        "gift_line_audit.csv",
        "dashboard_sales_province.csv",
    ):
        (tmp_path / name).write_bytes((TABLES / name).read_bytes())

    province_source = _read_table(tmp_path / "dashboard_sales_province.csv")
    source_order_total = int(province_source["orders"].astype(int).sum())
    source_revenue_total = float(province_source["recognized_revenue_vnd"].astype(float).sum())

    sanitize_aggregate_tables(tmp_path)

    products = _read_table(tmp_path / "dashboard_product_orders.csv")
    visible_product_counts = pd.to_numeric(products["order_count"], errors="coerce").dropna()
    assert (visible_product_counts >= 10).all()
    other = products.loc[products["product_name"] == PRODUCT_OTHER_LABEL]
    assert len(other) == 1
    assert other.iloc[0]["order_count"] == ""

    statuses = _read_table(tmp_path / "dashboard_status_counts.csv")
    visible_status_counts = pd.to_numeric(statuses["order_count"], errors="coerce").dropna()
    assert (visible_status_counts >= 10).all()
    assert statuses["order_count"].eq("").sum() >= 2

    gifts = _read_table(tmp_path / "gift_line_audit.csv")
    for column in GIFT_COUNT_COLUMNS:
        visible_counts = pd.to_numeric(gifts[column], errors="coerce").dropna()
        assert (visible_counts >= 10).all()

    provinces = _read_table(tmp_path / "dashboard_sales_province.csv")
    assert not provinces["province"].isin({
        "MON", "QUANG TRI", "THAI NGUYEN", "NGHE AN", "KON TUM", "QUANG NINH",
        "HA TINH", "HUNG YEN", "NINH BINH", "CHIN", "HAI PHONG", "HOA BINH",
        "PHU THO", "DONG NAI", "GIA LAI", "THANH HOA", "HAI DUONG", "THAI BINH",
        "DIEN BIEN", "LAI CHAU",
    }).any()
    other_province = provinces.loc[provinces["province"] == PROVINCE_OTHER_LABEL]
    assert len(other_province) == 1
    assert int(other_province.iloc[0]["orders"]) == 38
    assert float(other_province.iloc[0]["recognized_revenue_vnd"]) == 16_674_000
    assert int(provinces["orders"].astype(int).sum()) == source_order_total
    assert float(provinces["recognized_revenue_vnd"].astype(float).sum()) == source_revenue_total


def test_suppression_does_not_change_dashboard_csv_schemas() -> None:
    for name in (
        "dashboard_product_orders.csv",
        "dashboard_status_counts.csv",
        "gift_line_audit.csv",
        "dashboard_sales_province.csv",
    ):
        with (TABLES / name).open(encoding="utf-8-sig", newline="") as handle:
            assert next(csv.reader(handle))
