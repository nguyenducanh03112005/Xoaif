from datetime import date

import pandas as pd

from scripts.build_dss_cuboids_dev import (
    aggregate_cube,
    build_cuboids,
    olap_operation,
    suppress_small_cells,
)


def test_aggregate_rollup_counts_orders_but_recomputes_distinct_customers() -> None:
    rows = pd.DataFrame([
        {"month": "2024-04", "channel": "Facebook", "customer_key": "c1", "recognized_revenue_vnd": 100},
        {"month": "2024-04", "channel": "Facebook", "customer_key": "c1", "recognized_revenue_vnd": 200},
        {"month": "2024-04", "channel": "Other", "customer_key": "c2", "recognized_revenue_vnd": 300},
    ])
    detailed = aggregate_cube(rows, ["month", "channel"])
    rolled = aggregate_cube(rows, ["month"]).iloc[0]
    assert len(detailed) == 2
    assert rolled["orders"] == 3
    assert rolled["customers"] == 2
    assert rolled["recognized_revenue_vnd"] == 600


def test_suppression_hides_every_measure_for_small_order_or_customer_cell() -> None:
    cube = pd.DataFrame([
        {"segment": "large", "orders": 40, "customers": 30, "recognized_revenue_vnd": 1000, "orders_share": 1.0},
        {"segment": "small_customer_group", "orders": 40, "customers": 29, "recognized_revenue_vnd": 900, "orders_share": 1.0},
        {"segment": "small_orders", "orders": 29, "customers": 40, "recognized_revenue_vnd": 700, "orders_share": 1.0},
    ])
    result = suppress_small_cells(cube)
    assert result.loc[0, "suppressed"] is False or not result.loc[0, "suppressed"]
    for index in (1, 2):
        assert result.loc[index, "suppressed"]
        assert pd.isna(result.loc[index, "orders"])
        assert pd.isna(result.loc[index, "customers"])
        assert pd.isna(result.loc[index, "recognized_revenue_vnd"])
        assert pd.isna(result.loc[index, "orders_share"])


def test_slice_dice_and_pivot_follow_requested_dimensions() -> None:
    rows = pd.DataFrame([
        {"month": "2024-04", "channel": "Facebook", "customer_segment": "repeat", "customer_key": f"c{i}", "recognized_revenue_vnd": 10}
        for i in range(40)
    ] + [
        {"month": "2024-04", "channel": "Other", "customer_segment": "repeat", "customer_key": f"d{i}", "recognized_revenue_vnd": 20}
        for i in range(40)
    ])
    sliced = olap_operation(rows, dimensions=["month", "channel"], filters={"month": "2024-04", "customer_segment": "repeat"})
    assert set(sliced.channel) == {"Facebook", "Other"}
    pivoted = olap_operation(
        rows, dimensions=["month", "channel"], filters={"customer_segment": "repeat"},
        pivot=("month", "channel", "orders"),
    )
    assert "Facebook" in pivoted.columns
    assert "Other" in pivoted.columns
    empty = olap_operation(rows, dimensions=["month", "channel"], filters={"month": "2099-01"})
    assert empty.empty


def test_dss_join_reconciles_and_cuboids_never_export_keys() -> None:
    source = []
    facts = []
    for index in range(40):
        key, customer = f"order-{index}", f"customer-{index}"
        source.append({
            "order_key": key, "date": date(2024, 4, 1), "order_sequence": index,
            "customer_key": customer, "is_gift": False, "order_channel": "Facebook",
            "province": "UNKNOWN", "revenue_recognized": 830_000.0,
            "monetary_contribution": 830_000.0,
            "items": [], "total_discount_at_snapshot": 0, "total_price_at_snapshot": 830_000,
            "gift_line_records": [{
                "product_key": f"product-{index}", "product_name": "Example", "retail_price": 830_000,
                "quantity": 1, "bonus_flag": False, "discount_each_product": 0,
                "is_discount_percent": False, "line_total_discount": 0, "variation_key": None,
                "category_ids": [],
            }],
        })
        facts.append({
            "order_key": key, "customer_key": customer, "local_date": date(2024, 4, 1),
            "status_code": 3, "distinct_product_count": 1,
        })
    cuboids, meta = build_cuboids(pd.DataFrame(facts), source, order_keys=[f"order-{i}" for i in range(40)])
    assert meta["warehouse_status3_joined"] == 40
    assert meta["physical_warehouse_unchanged"] is True
    assert meta["olap_operations_executed"]["roll_up_orders_reconcile"] is True
    assert "order_key" not in set().union(*(set(frame.columns) for frame in cuboids.values()))
    assert "customer_key" not in set().union(*(set(frame.columns) for frame in cuboids.values()))
    assert len(cuboids["province"]) == 1
