from datetime import date

from features.repurchase_v3 import build_multisnapshot_folds, build_multisnapshot_samples
from models.repurchase_v3 import _weighted_metric_bundle
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
import numpy as np


def _order(customer: str, day: date, value: float) -> dict:
    return {
        "customer_key": customer,
        "date": day,
        "is_gift": False,
        "monetary_contribution": value,
        "quantity_total": 1,
        "product_keys": ["p1"],
        "province": "UNKNOWN",
        "price_adjustment": None,
        "adj_unexplained": False,
    }


def test_multisnapshot_features_are_point_in_time_and_labels_are_bounded():
    orders = [
        _order("a", date(2024, 4, 1), 100),
        _order("a", date(2024, 6, 1), 200),
        _order("a", date(2024, 11, 30), 300),
        _order("a", date(2025, 4, 1), 400),
        _order("a", date(2025, 9, 29), 500),  # beyond the Apr snapshot's 180-day label
        _order("b", date(2024, 4, 10), 100),
        _order("b", date(2024, 12, 15), 100),
        _order("c", date(2024, 12, 1), 100),  # not prior to this T
    ]
    frame = build_multisnapshot_samples(
        orders,
        test_start=date(2025, 10, 22),
        candidates=(date(2024, 5, 1), date(2024, 12, 1), date(2025, 4, 1)),
    )
    a_may = frame[(frame.customer_key == "a") & (frame.as_of == "2024-05-01")].iloc[0]
    assert a_may.recency_days == 30
    assert a_may.frequency == 1
    assert a_may.monetary == 100
    assert a_may.label_returned == 1
    a_april = frame[(frame.customer_key == "a") & (frame.as_of == "2025-04-01")].iloc[0]
    assert a_april.label_returned == 0
    assert frame.groupby("customer_key").size()["a"] == 3


def test_temporal_folds_allow_same_customer_when_train_label_is_mature():
    orders = [
        _order("a", date(2024, 4, 1), 100),
        _order("b", date(2024, 4, 2), 100),
        _order("a", date(2024, 6, 1), 100),
        _order("b", date(2024, 12, 10), 100),
        _order("a", date(2024, 12, 15), 100),
    ]
    frame = build_multisnapshot_samples(
        orders,
        test_start=date(2025, 10, 22),
        candidates=(date(2024, 5, 1), date(2024, 12, 1)),
    )
    folds = build_multisnapshot_folds(frame, minimum_train_rows=1)
    december = next(fold for fold in folds if str(fold["validation_t"]) == "2024-12-01")
    train_keys = set(frame.iloc[december["train"]].customer_key)
    valid_keys = set(frame.iloc[december["validation"]].customer_key)
    assert train_keys & valid_keys
    assert all(
        (frame.iloc[index].as_of == "2024-05-01")
        for index in december["train"]
    )


def test_weighted_bootstrap_metrics_match_sklearn_with_tied_scores():
    y = np.array([0, 1, 0, 1, 1, 0])
    score = np.array([0.1, 0.5, 0.1, 0.5, 0.8, 0.2])
    weight = np.array([2, 1, 3, 2, 1, 4])
    actual = _weighted_metric_bundle(y, score, weight)
    assert actual["roc_auc"] == roc_auc_score(y, score, sample_weight=weight)
    assert actual["average_precision"] == average_precision_score(y, score, sample_weight=weight)
    assert actual["brier"] == brier_score_loss(y, score, sample_weight=weight)
