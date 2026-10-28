from datetime import date

import pandas as pd

from scripts.analyze_revenue_scenarios_f5 import customer_cohort_rows, analyze


def test_same_day_order_contributes_transaction_value_but_not_repeat_event():
    rows = [
        {"customer_key": "a", "is_gift": False, "date": date(2024, 4, 1), "order_sequence": 0,
         "revenue_recognized": 100, "monetary_contribution": 100},
        {"customer_key": "a", "is_gift": False, "date": date(2024, 4, 1), "order_sequence": 1,
         "revenue_recognized": 50, "monetary_contribution": 50},
        {"customer_key": "a", "is_gift": False, "date": date(2024, 4, 2), "order_sequence": 2,
         "revenue_recognized": 75, "monetary_contribution": 75},
    ]
    result = customer_cohort_rows(rows).iloc[0]
    assert result.revenue_180d == 225
    assert result.repeat_180d == 1


def test_sensitivity_rows_are_labeled_as_assumptions():
    frame = pd.DataFrame({"cohort_month": ["2024-04"] * 4,
                          "revenue_180d": [100, 200, 300, 400],
                          "first_order_revenue": [80, 160, 240, 320],
                          "orders_180d": [1, 2, 1, 2],
                          "repeat_180d": [0, 1, 0, 1],
                          "high_value": [0, 1, 0, 1]})
    _, scenarios, _ = analyze(frame)
    assert len(scenarios) == 6
    assert scenarios.label.str.contains("giả định minh họa").all()
