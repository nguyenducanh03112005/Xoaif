import json
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[1]


def _evidence():
    return json.loads((ROOT / "outputs/tables/cohort_bridge_verified.json").read_text(encoding="utf-8"))


def test_dev_order_funnel_partitions_orders():
    db = _evidence()["duckdb"]
    assert db["dev_orders"] == db["dev_status3_orders"] + db["dev_other_status_orders"]


def test_documented_customer_bridge_matches_aggregate_evidence():
    evidence = _evidence()["t1"]
    canonical = (ROOT / "docs/canonical_numbers.md").read_text(encoding="utf-8")
    reconciliation = (ROOT / "docs/cohort_reconciliation.md").read_text(encoding="utf-8")
    fmt = lambda value: f"{value:,}".replace(",", ".")
    assert evidence["A_all_status3_before_T"] - evidence["A_minus_B_only_pre_analysis"] == evidence["B_status3_in_DEV"]
    assert evidence["B_status3_in_DEV"] - evidence["B_customers_with_only_gift_status3_orders"] == evidence["B_after_non_gift_customer_filter"]
    assert "phần dư chưa giải thích: 0" in reconciliation
    for value in (
        evidence["A_all_status3_before_T"], evidence["A_minus_B_only_pre_analysis"],
        evidence["B_status3_in_DEV"], evidence["B_customers_with_only_gift_status3_orders"],
        evidence["B_after_non_gift_customer_filter"],
    ):
        assert fmt(value) in canonical and fmt(value) in reconciliation


def test_verified_aggregate_has_consistent_units_and_totals():
    payload = _evidence()
    t1, t2 = payload["t1"], payload["t2"]
    assert t1["unit"] == "distinct_customers_with_nonnull_id"
    assert t2["unit"] == "orders"
    assert t1["A_all_status3_before_T"] == t1["A_minus_B_only_pre_analysis"] + t1["B_status3_in_DEV"]
    assert t1["B_status3_in_DEV"] == t1["B_customers_with_only_gift_status3_orders"] + t1["B_after_non_gift_customer_filter"]
    assert t2["status3_dev_orders"] == sum(row["orders"] for row in t2["province_and_revenue_groups"])
    assert sum(row["revenue_vnd"] for row in t2["province_and_revenue_groups"]) == t2["revenue_recognized_total_vnd"]
    for details in t2["source_channel_group_distributions"].values():
        for row in details["groups"] + details["province_missing_intersection"]:
            if row["suppressed"]:
                assert row["orders"] is None and row["revenue_vnd"] is None
            else:
                assert row["orders"] >= 5
    assert payload["test_labels_loaded"] is False and payload["test_behavior_loaded"] is False


def test_dev_duckdb_counts_match_canonical_when_available():
    database = ROOT / "data/restricted/xoaif_dev.duckdb"
    if not database.is_file():
        pytest.skip("clone mode: restricted DEV DuckDB is not present")
    con = duckdb.connect(str(database), read_only=True)
    values = con.execute("""
        SELECT
          COUNT(DISTINCT order_key),
          COUNT(DISTINCT order_key) FILTER (WHERE status_code = 3),
          COUNT(DISTINCT order_key) FILTER (WHERE status_code <> 3),
          COUNT(DISTINCT customer_key),
          COUNT(DISTINCT customer_key) FILTER (WHERE status_code = 3),
          COUNT(DISTINCT customer_key) FILTER (WHERE status_code <> 3),
          (SELECT COUNT(*) FROM (
             SELECT customer_key FROM fact_orders WHERE customer_key IS NOT NULL GROUP BY customer_key
             HAVING BOOL_OR(status_code = 3) AND BOOL_OR(status_code <> 3)
           ) AS overlap),
          COUNT(DISTINCT customer_key) FILTER (WHERE status_code = 3 AND customer_key IS NOT NULL),
          COUNT(DISTINCT order_key) FILTER (WHERE status_code <> 3 AND customer_key IS NULL),
          COUNT(DISTINCT order_key) FILTER (WHERE status_code = 3 AND customer_key IS NULL)
        FROM fact_orders
    """).fetchone()
    con.close()
    db = _evidence()["duckdb"]
    assert tuple(map(int, values)) == (
        db["dev_orders"], db["dev_status3_orders"], db["dev_other_status_orders"],
        db["dev_customers_nonnull"], db["dev_customers_status3"],
        db["dev_customers_other_status"], db["dev_customers_status3_other_status_intersection"],
        db["dev_customers_status3_nonnull"], db["other_status_null_customer_orders"],
        db["status3_null_customer_orders"],
    )
