"""Build suppression-safe OLAP cuboids from the read-only DEV warehouse."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
import hashlib
import json
from pathlib import Path
import sys

import duckdb
import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from features.day2_data import load_dev_orders, local_day, safe_status  # noqa: E402
from features.gift_lines import classify_orders  # noqa: E402
from analyze_customer_value_dev import rfm_action_group  # noqa: E402
from analyze_seasonality_dev import channel_group  # noqa: E402
from ingest.identifiers import pseudonymize_id  # noqa: E402
from ingest.settings import load_analytics_hmac_key  # noqa: E402

DEV_START = date(2024, 4, 1)
DEV_END = date(2025, 10, 22)
MIN_N = 30
RFM_HIGH_VALUE_CUT_VND = 830_000.0  # A1 preregistered DEV p90 threshold


def _date_gated_order_keys() -> list[str]:
    """Derive ephemeral HMAC order keys after a strict DEV date gate.

    Kept in this A4 script so the sealed `day2_data.py` remains byte-identical.
    Original order IDs are never returned, logged, or persisted.
    """
    split = yaml.safe_load((ROOT / "config" / "split.yaml").read_bytes())
    snapshot_id = str(split["snapshot_id"])
    snapshot_root = (ROOT / "data" / "raw" / "pancake_orders" / snapshot_id).resolve()
    manifest_path = snapshot_root / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != split.get("snapshot_manifest_sha256"):
        raise ValueError("snapshot manifest differs from locked split")
    manifest = json.loads(manifest_bytes)
    hmac_key = load_analytics_hmac_key(ROOT / "xoaif.env")
    keys: list[str] = []
    for page_no, page_record in enumerate(manifest["pages"], start=1):
        page_path = (snapshot_root / page_record["file"]).resolve()
        if not page_path.is_relative_to(snapshot_root):
            raise ValueError("snapshot page path escaped its directory")
        page_bytes = page_path.read_bytes()
        if hashlib.sha256(page_bytes).hexdigest() != page_record.get("sha256"):
            raise ValueError("snapshot page checksum mismatch")
        payload = json.loads(page_bytes)
        if payload.get("page_number") != page_no or len(payload.get("data", [])) != page_record.get("rows"):
            raise ValueError("snapshot page metadata or row count mismatch")
        for source_order in payload.get("data", []):
            if not isinstance(source_order, dict):
                continue
            # No other row field is accessed before `inserted_at` establishes DEV.
            day = local_day(source_order.get("inserted_at"))
            if day is None or day < DEV_START or day >= DEV_END:
                continue
            if safe_status(source_order.get("status")) != 3:
                continue
            source_id = source_order.get("id")
            if source_id is None or not str(source_id).strip():
                raise ValueError("date-gated DEV status-3 order has no stable ID")
            keys.append(pseudonymize_id(source_id, key=hmac_key, namespace="xoaif/order/v1"))
    if len(keys) != 6400 or len(set(keys)) != len(keys):
        raise ValueError("date-gated order-key scan did not reconcile to DEV status-3 count")
    return keys


def aggregate_cube(rows: pd.DataFrame, dimensions: list[str]) -> pd.DataFrame:
    """Aggregate order facts; distinct-customer measure is non-additive."""
    if rows.empty:
        return pd.DataFrame(columns=[*dimensions, "orders", "customers", "recognized_revenue_vnd"])
    if not dimensions:
        groups = [((), rows)]
    else:
        groups = rows.groupby(dimensions, dropna=False, sort=True)
    result = []
    for key, frame in groups:
        if not isinstance(key, tuple):
            key = (key,)
        record = dict(zip(dimensions, key))
        record["orders"] = int(len(frame))
        record["customers"] = int(frame["customer_key"].dropna().nunique())
        record["recognized_revenue_vnd"] = float(frame["recognized_revenue_vnd"].sum())
        result.append(record)
    return pd.DataFrame(result)


def suppress_small_cells(cube: pd.DataFrame, *, min_n: int = MIN_N, count_basis: str = "orders") -> pd.DataFrame:
    """Hide measures below n threshold after the requested OLAP operation."""
    result = cube.copy()
    if result.empty:
        result["suppressed"] = pd.Series(dtype=bool)
        result["suppression_note"] = pd.Series(dtype=str)
        return result
    counts = result[count_basis].astype(int)
    small = counts < min_n
    if "customers" in result:
        small |= result["customers"].fillna(0).astype(int) < min_n
    result["suppressed"] = small
    for column in ("orders", "customers", "recognized_revenue_vnd"):
        if column in result:
            result.loc[small, column] = np.nan
    if "orders_share" in result:
        result.loc[small, "orders_share"] = np.nan
    result["suppression_note"] = np.where(small, f"n<{min_n}; measures hidden", "")
    return result


def olap_operation(
    rows: pd.DataFrame,
    *,
    dimensions: list[str],
    filters: dict[str, object] | None = None,
    pivot: tuple[str, str, str] | None = None,
    min_n: int = MIN_N,
) -> pd.DataFrame:
    """Run slice/dice, roll-up/drill-down via requested dimensions, then pivot."""
    selected = rows.copy()
    for column, value in (filters or {}).items():
        if isinstance(value, (set, list, tuple)):
            selected = selected[selected[column].isin(value)]
        else:
            selected = selected[selected[column] == value]
    result = aggregate_cube(selected, dimensions)
    if pivot:
        index, columns, values = pivot
        result = suppress_small_cells(result, min_n=min_n)
        result = result.pivot_table(index=index, columns=columns, values=values, aggfunc="sum", dropna=False).reset_index()
        return result
    return suppress_small_cells(result, min_n=min_n)


def _customer_segments(orders: list[dict]) -> dict[str, str]:
    by_customer: dict[str, list[dict]] = defaultdict(list)
    for row in orders:
        if row.get("customer_key") and not row["is_gift"] and row["date"] < DEV_END:
            by_customer[str(row["customer_key"])].append(row)
    monetary = {
        key: sum(float(row["monetary_contribution"] or 0) for row in rows)
        for key, rows in by_customer.items()
    }
    p90 = float(np.quantile(list(monetary.values()), .90)) if monetary else 0.0
    if not np.isclose(p90, RFM_HIGH_VALUE_CUT_VND):
        raise ValueError(f"A1 RFM cut changed: expected {RFM_HIGH_VALUE_CUT_VND}, got {p90}")
    labels = {}
    for key, rows in by_customer.items():
        rows.sort(key=lambda row: (row["date"], row["order_sequence"]))
        recency = (DEV_END - rows[-1]["date"]).days
        labels[key] = rfm_action_group(recency, len(rows), monetary[key], RFM_HIGH_VALUE_CUT_VND)
    return labels


def build_cuboids(
    warehouse_orders: pd.DataFrame, source_orders: list[dict], *, order_keys: list[str] | None = None,
) -> tuple[dict[str, pd.DataFrame], dict]:
    ephemeral_keys = order_keys if order_keys is not None else _date_gated_order_keys()
    if len(ephemeral_keys) != len(source_orders):
        raise ValueError("DEV source orders and ephemeral HMAC key counts differ")
    source_enriched = [{**row, "order_key": key} for row, key in zip(source_orders, ephemeral_keys)]
    source = pd.DataFrame(source_enriched)
    if not (source["order_sequence"].to_numpy() == np.arange(len(source))).all():
        raise ValueError("DEV loader order sequence is not contiguous")
    if source["order_key"].isna().any() or source["order_key"].duplicated().any():
        raise ValueError("In-memory DEV join keys are missing or duplicated")
    warehouse = warehouse_orders[warehouse_orders["status_code"] == 3].copy()
    warehouse["local_date"] = pd.to_datetime(warehouse["local_date"]).dt.date
    source = source.rename(columns={"date": "source_date", "customer_key": "source_customer_key"})
    joined = warehouse.merge(source, left_on="order_key", right_on="order_key", how="left", validate="one_to_one")
    if len(joined) != len(warehouse) or joined["source_date"].isna().any():
        raise ValueError("DEV warehouse/status-3 source join did not reconcile one-to-one")
    if not (joined["local_date"] == joined["source_date"]).all():
        raise ValueError("DEV warehouse and date-gated source dates differ")
    warehouse_customer = joined["customer_key"].fillna("")
    source_customer = joined["source_customer_key"].fillna("")
    if not (warehouse_customer == source_customer).all():
        raise ValueError("DEV warehouse and source customer keys differ")
    classified, gift_audit = classify_orders(source_enriched)
    line_products = {
        row["order_key"]: {line["product_key"] for line in row["gift_line_records"] if line.get("product_key") and not line.get("gift_line")}
        for row in classified
    }
    segments = _customer_segments(source_orders)
    joined["month"] = pd.to_datetime(joined["local_date"]).dt.strftime("%Y-%m")
    joined["year"] = pd.to_datetime(joined["local_date"]).dt.year.astype(str)
    joined["quarter"] = pd.to_datetime(joined["local_date"]).dt.quarter.map(lambda value: f"Q{value}")
    joined["channel_group"] = joined["order_channel"].map(channel_group)
    joined["province_group"] = joined["province"].fillna("UNKNOWN")
    joined["customer_segment"] = joined["source_customer_key"].map(segments).fillna("Không phân khúc")
    joined["clean_product_count"] = joined["order_key"].map(lambda key: len(line_products.get(key, set())))
    joined["basket_size"] = pd.cut(
        joined["clean_product_count"], bins=[-1, 1, 2, np.inf], labels=["0–1", "2", "3+"], right=False
    ).astype(str)
    sales = joined[(~joined["is_gift"]) & (joined["source_date"] < DEV_END)].copy()
    sales["customer_key"] = sales["source_customer_key"]
    sales["recognized_revenue_vnd"] = sales["revenue_recognized"].map(float)
    channel_cube = aggregate_cube(sales, ["month", "channel_group", "customer_segment"])
    basket_cube = aggregate_cube(sales, ["month", "basket_size", "customer_segment"])

    # Execute registered OLAP roll-up, drill-down, slice, dice, and pivot
    # examples on the full in-memory facts before suppression.
    annual = aggregate_cube(sales, ["year"])
    quarterly = aggregate_cube(sales, ["year", "quarter"])
    monthly = aggregate_cube(sales, ["month"])
    if annual["orders"].sum() != quarterly["orders"].sum() or quarterly["orders"].sum() != monthly["orders"].sum():
        raise ValueError("OLAP roll-up order totals do not reconcile")
    slice_result = olap_operation(sales, dimensions=["channel_group", "customer_segment"], filters={"month": "2024-04"})
    dice_result = olap_operation(sales, dimensions=["channel_group", "customer_segment"], filters={
        "month": "2024-04", "channel_group": "Facebook",
    })
    pivot_result = olap_operation(
        sales, dimensions=["month", "channel_group"], filters={"customer_segment": "Một đơn đã lâu"},
        pivot=("month", "channel_group", "orders"),
    )

    # Region cube: group provinces with <30 DEV non-gift orders before output.
    region_summary = aggregate_cube(sales, ["province_group"])
    small_regions = set(region_summary.loc[
        (region_summary["orders"] < MIN_N) | (region_summary["customers"] < MIN_N), "province_group"
    ])
    sales["province_group"] = sales["province_group"].map(lambda value: "Tỉnh khác (gộp)" if value in small_regions else value)
    province_cube = aggregate_cube(sales, ["province_group"])
    province_cube["orders_share"] = province_cube["orders"] / province_cube["orders"].sum()

    # Physical fact table provides status/month counts, without asserting revenue for other statuses.
    all_facts = warehouse_orders.copy()
    all_facts["month"] = pd.to_datetime(all_facts["local_date"]).dt.strftime("%Y-%m")
    status_cube = all_facts.groupby(["month", "status_code"], as_index=False).agg(
        orders=("order_key", "size"), customers=("customer_key", "nunique")
    )
    status_cube["recognized_revenue_vnd"] = np.nan

    cuboids = {
        "month_channel_segment": suppress_small_cells(channel_cube, count_basis="orders"),
        "month_basket_segment": suppress_small_cells(basket_cube, count_basis="orders"),
        "province": suppress_small_cells(province_cube, count_basis="orders"),
        "month_status": suppress_small_cells(status_cube, count_basis="orders"),
    }
    meta = {
        "status": "exploratory_dev_only_not_confirmed_out_of_sample",
        "test_raw_or_labels_read": False,
        "warehouse_orders_scanned": int(len(warehouse_orders)),
        "warehouse_status3_joined": int(len(joined)),
        "status3_dev_non_gift_sales": int(len(sales)),
        "eligible_sales_customers": int(sales["customer_key"].nunique()),
        "unknown_region_orders": int((sales["province_group"] == "UNKNOWN").sum()),
        "province_order_coverage": float(sales["province"].notna().mean()),
        "channel_order_coverage": float(sales["order_channel"].notna().mean()),
        "suppression_threshold": MIN_N,
        "province_groups_pooled": int(len(small_regions)),
        "gift_line_audit": gift_audit,
        "cuboid_rows_before_suppression": {key: int(len(frame)) for key, frame in {
            "month_channel_segment": channel_cube, "month_basket_segment": basket_cube,
            "province": province_cube, "month_status": status_cube,
        }.items()},
        "cuboid_rows_suppressed": {key: int(frame["suppressed"].sum()) for key, frame in cuboids.items()},
        "physical_warehouse_unchanged": True,
        "order_keys_ephemeral_hmac_only": True,
        "olap_operations_executed": {
            "roll_up_year_rows": int(len(annual)), "roll_up_quarter_rows": int(len(quarterly)),
            "drill_down_month_rows": int(len(monthly)), "slice_month_2024_04_rows": int(len(slice_result)),
            "dice_month_2024_04_facebook_rows": int(len(dice_result)), "pivot_month_by_channel_columns": int(len(pivot_result.columns)),
            "roll_up_orders_reconcile": True,
        },
    }
    return cuboids, meta


def main() -> int:
    db_path = ROOT / "data" / "restricted" / "xoaif_dev.duckdb"
    if not db_path.is_file():
        raise FileNotFoundError("Restricted DEV DuckDB is required locally; no database is copied or committed")
    with duckdb.connect(str(db_path), read_only=True) as con:
        table_names = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
        required = {"fact_orders", "fact_order_items", "dim_date", "dim_order_status", "dim_customer", "dim_product"}
        if not required.issubset(table_names):
            raise ValueError(f"Warehouse schema missing required tables: {sorted(required - table_names)}")
        warehouse = con.execute(
            "SELECT order_key, customer_key, local_date, status_code, distinct_product_count FROM fact_orders WHERE local_date >= ? AND local_date < ?",
            [DEV_START, DEV_END],
        ).df()
    source_orders, _, _ = load_dev_orders()
    cuboids, meta = build_cuboids(warehouse, source_orders)
    plan_hash = hashlib.sha256((ROOT / "docs" / "analysis_plan_wp_olap.md").read_bytes()).hexdigest()
    meta["analysis_plan_sha256"] = plan_hash
    output_map = {
        "month_channel_segment": "cube_month_channel_segment_dev.csv",
        "month_basket_segment": "cube_month_basket_segment_dev.csv",
        "province": "cube_province_dev.csv",
        "month_status": "cube_month_status_dev.csv",
    }
    for key, filename in output_map.items():
        cuboids[key].to_csv(ROOT / "outputs" / "tables" / filename, index=False, float_format="%.6f")
    (ROOT / "outputs" / "metrics" / "dss_cuboids_dev.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
