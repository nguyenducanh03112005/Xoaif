from datetime import date, timedelta

import pandas as pd

from scripts.analyze_product_journey_dev import (
    MIN_N,
    _bootstrap_product_stats,
    combo_metrics,
    customer_first_baskets,
    prepare_baskets,
)


def test_prepare_baskets_removes_order_gifts_and_flagged_gift_lines() -> None:
    orders = [
        {
            "date": date(2024, 4, 1), "order_sequence": 1, "customer_key": "c1", "is_gift": False,
            "revenue_recognized": 100,
            "gift_line_records": [
                {"product_key": "p1", "product_name": "Plant", "bonus_flag": False},
                {"product_key": "p2", "product_name": "Gift", "bonus_flag": True},
            ],
        },
        {"date": date(2024, 4, 2), "order_sequence": 2, "customer_key": "c2", "is_gift": True,
         "gift_line_records": [{"product_key": "p1", "product_name": "Plant", "bonus_flag": False}]},
    ]
    baskets, names = prepare_baskets(orders)
    assert len(baskets) == 1
    assert baskets[0]["items"] == {"p1"}
    assert names["p1"] == "Plant"


def test_first_basket_sequence_uses_later_local_date_and_180_day_followup() -> None:
    rows = [
        {"customer_key": "c1", "date": date(2025, 1, 1), "order_sequence": 1, "items": {"a"}},
        {"customer_key": "c1", "date": date(2025, 1, 1), "order_sequence": 2, "items": {"b"}},
        {"customer_key": "c1", "date": date(2025, 1, 10), "order_sequence": 3, "items": {"c"}},
        {"customer_key": "c2", "date": date(2025, 4, 25), "order_sequence": 4, "items": {"a"}},
    ]
    first, second = customer_first_baskets(rows)
    assert len(first) == 1
    assert first[0]["items"] == {"a"}
    assert len(second) == 1
    assert second[0]["gap_days"] == 9
    assert second[0]["second_items"] == {"c"}


def test_first_basket_group_suppresses_estimates_if_comparator_is_small() -> None:
    rows = [{"items": {"p"}, "repeat_180d": 1, "month": "2024-04"} for _ in range(MIN_N)]
    rows += [{"items": set(), "repeat_180d": 0, "month": "2024-04"} for _ in range(MIN_N - 1)]
    result = _bootstrap_product_stats(rows, "p", draws=20)
    assert result["n_product_first_basket"] == MIN_N
    assert result["n_without_product"] == MIN_N - 1
    assert result["suppressed"] is True
    assert "repeat_rate_with_product" not in result


def test_frozen_combo_metrics_compute_balanced_measures() -> None:
    baskets = [
        {"items": {"a", "b"}, "month": "2024-04", "recognized_revenue": 120},
        {"items": {"a", "b"}, "month": "2024-04", "recognized_revenue": 180},
        {"items": {"a", "c"}, "month": "2024-05", "recognized_revenue": 220},
        {"items": {"c", "d"}, "month": "2024-05", "recognized_revenue": 90},
    ]
    frozen = pd.DataFrame([{
        "combo_name": "A + B", "product_a_key_hmac": "a", "product_b_key_hmac": "b",
        "product_a": "A", "product_b": "B", "combined_nonzero_listed_price_vnd": 50,
        "test_eligible_baskets": 100, "pair_occurrences": 8, "support": .08, "lift": 1.2,
    }])
    test_agg = pd.DataFrame([{
        "combo_name": "A + B", "test_eligible_baskets": 100, "pair_occurrences": 8,
        "support": .08, "lift": 1.2,
    }])
    result = combo_metrics(baskets, {"a": "A", "b": "B"}, frozen, test_agg).iloc[0]
    assert result["dev_eligible_baskets"] == 4
    assert result["dev_pair_occurrences"] == 2
    assert result["dev_support"] == 0.5
    assert result["dev_kulczynski"] == (2 / 3 + 1) / 2
    assert result["dev_all_confidence"] == 2 / 3
    assert result["dev_imbalance_ratio"] == 1 / 3
    assert result["median_recognized_basket_revenue_vnd"] == 150
    assert result["test_eligible_baskets_committed"] == 100
    assert result["test_support_committed"] == .08
    assert result["test_lift_committed"] == 1.2
