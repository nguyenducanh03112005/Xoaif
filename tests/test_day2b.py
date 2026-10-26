from datetime import date, timedelta
from decimal import Decimal

import numpy as np
import pandas as pd

from features import day2b_data
from features.basket_v2 import _mine
from models.cancel_refund_v2 import NUMERIC, CATEGORICAL
from models import classify_v2
from models.classify_v2 import _bootstrap_intervals
from models.segment_v2 import _rule_segments


def test_cancel_validation_windows_are_contiguous_and_stop_before_test():
    start = date(2024, 4, 1)
    test_start = date(2025, 10, 22)
    windows = day2b_data.cancel_validation_windows(start, test_start)
    assert len(windows) == 5
    assert windows[0][0] == start + timedelta(days=180)
    assert all(left[1] == right[0] for left, right in zip(windows, windows[1:]))
    assert windows[-1][1] == test_start


def test_repurchase_latest_order_features_stay_before_each_t(monkeypatch):
    orders = [{
        "customer_key": "hmac-a",
        "is_gift": False,
        "date": date(2025, 1, 10),
        "order_sequence": 1,
        "product_keys": ["p1", "p2"],
        "items": [{"category": "plants"}, {"category": "plants"}],
        "total_price_at_snapshot": Decimal("100"),
        "total_discount_at_snapshot": Decimal("10"),
        "revenue_recognized": Decimal("90"),
        "order_channel": "web",
        "province": "HANOI",
    }, {
        "customer_key": "hmac-a",
        "is_gift": False,
        "date": date(2025, 2, 5),
        "order_sequence": 2,
        "product_keys": ["p3"],
        "items": [{"category": "plants"}],
        "total_price_at_snapshot": Decimal("50"),
        "total_discount_at_snapshot": Decimal("0"),
        "revenue_recognized": Decimal("50"),
        "order_channel": None,
        "province": "HANOI",
    }]
    monkeypatch.setattr(day2b_data, "load_dev_orders", lambda: (orders, {}, {}))
    result, audit = day2b_data.make_repurchase_features([{"customer_key": "hmac-a", "T": "2025-02-01", "label_returned": 0}])
    assert result[0]["last_order_product_count"] == 2
    assert result[0]["last_order_revenue_recognized"] == 90
    assert audit["all_feature_dates_strictly_before_T"] is True


def test_zero_filter_basket_rule_mining_reports_leverage():
    transactions = []
    for left, right in (("a", "b"), ("c", "d"), ("e", "f")):
        transactions.extend([[left, right] for _ in range(30)])
        transactions.extend([[left] for _ in range(10)])
        transactions.extend([[right] for _ in range(10)])
    rules, trials, support = _mine(transactions)
    assert not rules.empty
    assert "leverage" in rules
    assert support in {0.005, 0.01, 0.02, 0.03, 0.05}
    assert len(trials) == 5


def test_rule_segments_use_explicit_business_names_and_cover_customers():
    frame = pd.DataFrame({
        "customer_key": [f"hmac-{i}" for i in range(8)],
        "frequency": [1, 1, 1, 1, 2, 2, 3, 18],
        "recency_days": [10, 20, 40, 80, 15, 25, 5, 3],
        "monetary": [100, 200, 300, 400, 500, 600, 700, 100000],
        "max_order_value": [100, 200, 300, 400, 250, 300, 300, 100000],
    })
    labels, thresholds = _rule_segments(frame)
    assert len(labels) == len(frame)
    assert labels.str.startswith("Theo quy tắc nghiệp vụ — ").all()
    assert "one_order_recency_p50" in thresholds
    assert not labels.str.contains("nguy cơ|rời bỏ", case=False).any()


def test_bootstrap_returns_requested_paired_intervals(monkeypatch):
    monkeypatch.setattr(classify_v2, "BOOTSTRAP_REPEATS", 100)
    y = np.asarray([0, 1] * 30)
    scores = np.asarray([0.2, 0.8] * 30)
    baseline = np.full(60, float(y.mean()))
    result = _bootstrap_intervals(y, scores, baseline)
    assert result["repeats_requested"] == 100
    assert result["roc_auc_95_ci"] is not None
    assert result["pr_auc_delta_vs_majority_95_ci"] is not None


def test_cancel_feature_lists_exclude_post_creation_fields():
    forbidden = {"status_history", "updated_at", "cod", "cash", "prepaid", "transfer_money", "money_to_collect"}
    assert set(NUMERIC) == {"item_count", "order_value_at_creation", "order_month", "nearest_holiday_distance_days"}
    assert set(CATEGORICAL) == {"channel", "province", "customer_new_or_returning"}
    assert forbidden.isdisjoint(set(NUMERIC) | set(CATEGORICAL))
