from datetime import date

import pandas as pd

from scripts.analyze_prevalence_drift_f2 import cohort_rates, trend_bootstrap


def test_cohort_rate_requires_later_local_date_and_mature_window():
    orders = [
        {"customer_key": "a", "is_gift": False, "date": date(2024, 4, 1), "order_sequence": 0},
        {"customer_key": "a", "is_gift": False, "date": date(2024, 4, 1), "order_sequence": 1},
        {"customer_key": "a", "is_gift": False, "date": date(2024, 4, 10), "order_sequence": 2},
        {"customer_key": "b", "is_gift": False, "date": date(2025, 8, 1), "order_sequence": 3},
    ]
    frame = cohort_rates(orders)
    assert frame.to_dict("records") == [{"customer_key": "a", "cohort_month": "2024-04", "returned_180d": 1}]


def test_bootstrap_trend_is_reproducible_and_in_pp_per_month():
    frame = pd.DataFrame({
        "customer_key": [f"c{i}" for i in range(120)],
        "cohort_month": ["2024-01"] * 60 + ["2024-02"] * 60,
        "returned_180d": [1] * 30 + [0] * 30 + [1] * 15 + [0] * 45,
    })
    left = trend_bootstrap(frame)
    right = trend_bootstrap(frame)
    assert left == right
    assert left["slope_pp_per_month"] < 0
