import numpy as np
import pandas as pd

from scripts.evaluate_repurchase_wp5b_dev import (
    _calibration_coefficients,
    _rule,
    _select_candidate,
)
from models.repurchase_v3 import _ranking_tables


def test_frequency_recency_rule_has_registered_cutoffs():
    frame = pd.DataFrame({"frequency": [1, 2, 3, 2], "recency_days": [2, 10, 45, 91]})
    assert _rule(frame).tolist() == [0.0, 1.0, 1.0, 1.0]
    assert _rule(frame, 30).tolist() == [0.0, 1.0, 0.0, 0.0]


def test_selection_uses_only_complete_monotonic_strategies_and_registered_tie_order():
    folds = pd.DataFrame([
        {"strategy": "S1_frequency_rule", "average_precision": 0.10},
        {"strategy": "S1_frequency_rule", "average_precision": 0.10},
        {"strategy": "S2_frequency_recency_rule", "average_precision": 0.50},
    ])
    monotonicity = {
        "S1_frequency_rule": {"monotonic_descending": True},
        "S2_frequency_recency_rule": {"monotonic_descending": True},
    }
    # S2 has the higher partial-fold mean but cannot qualify because it failed one fold.
    assert _select_candidate(folds, monotonicity, 2) == "S1_frequency_rule"
    assert _select_candidate(folds, {}, 2) is None


def test_calibration_coefficients_return_none_for_binary_rule_scores():
    y = np.array([0, 1] * 30)
    intercept, slope = _calibration_coefficients(y, np.tile([0.0, 1.0], 30))
    assert intercept is None
    assert slope is None


def test_calibration_coefficients_include_zero_probability_tree_leaves_after_clipping():
    y = np.array([0, 1] * 60)
    score = np.tile([0.0, 0.02, 0.08, 0.25], 30)
    intercept, slope = _calibration_coefficients(y, score)
    assert intercept is not None
    assert slope is not None


def test_ranking_table_has_one_pooled_decile_set_plus_fold_sets():
    pred = pd.DataFrame({
        "strategy": ["candidate"] * 40,
        "as_of": ["fold_1"] * 20 + ["fold_2"] * 20,
        "customer_key": [f"k{i:02d}" for i in range(40)],
        "label_returned": [0, 1] * 20,
        "score": np.linspace(0.01, 0.99, 40),
    })
    deciles, top_k = _ranking_tables(pred)
    assert len(deciles[deciles.fold_or_pooled == "pooled"]) == 10
    assert len(deciles[deciles.fold_or_pooled != "pooled"]) == 20
    assert len(top_k[top_k.fold_or_pooled == "pooled"]) == 3
