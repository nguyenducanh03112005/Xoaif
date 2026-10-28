from __future__ import annotations

import numpy as np
import pandas as pd
import sys
from pathlib import Path

from features.holdout2_metrics import (customer_cluster_bootstrap, h4_is_testable,
                                       h4_meets_threshold, holm_step_down,
                                       precision_at_k_tie_aware, risk_ratio, roc_auc)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from evaluate_holdout2_once import _centered_bootstrap_p  # noqa: E402


def test_metrics_match_hand_calculation() -> None:
    assert roc_auc([1, 0], [.9, .1]) == 1.0
    assert risk_ratio([1, 1, 1, 0], [1, 1, 0, 0])["rr"] == 2.0
    top = precision_at_k_tie_aware([0, 1, 0, 1, 0], [3, 2, 2, 1, 0], fraction=.4)
    assert top["k"] == 2
    assert top["n_above"] == 1 and top["n_tied"] == 2
    assert top["q"] == .5
    assert top["precision"] == .25
    assert top["lift"] == .625


def test_holm_step_down_and_customer_cluster_bootstrap_are_deterministic() -> None:
    assert holm_step_down({"H1": .01, "H2": .04}) == {"H1": .02, "H2": .04}
    frame = pd.DataFrame({"customer_key": ["a", "a", "b"], "x": [0., 1., 1.]})
    first = customer_cluster_bootstrap(frame, lambda sample: sample.x.mean(), draws=100, seed=5)
    second = customer_cluster_bootstrap(frame, lambda sample: sample.x.mean(), draws=100, seed=5)
    assert first == second
    assert first["valid_draws"] == 100


def test_centered_bootstrap_p_uses_registered_effect_threshold() -> None:
    values = np.array([.52, .55, .56, .57, .60])
    assert _centered_bootstrap_p(values, .57, .55) == 2 / 6
    rr_values = np.array([2.2, 2.5, 2.7, 3.0])
    assert _centered_bootstrap_p(rr_values, 2.0, 1.5, log_scale=True) == 3 / 5


def test_h4_spearman_tolerance_handles_preregistered_synthetic_boundaries() -> None:
    from scipy.stats import spearmanr

    s6 = 0.9761904761904763
    one_swap_8 = [2, 1, 3, 4, 5, 6, 7, 8]
    two_swaps_8 = [2, 1, 4, 3, 5, 6, 7, 8]
    rho_one_8 = float(spearmanr(range(1, 9), one_swap_8).statistic)
    rho_two_8 = float(spearmanr(range(1, 9), two_swaps_8).statistic)
    assert h4_meets_threshold(rho_one_8, s6)
    assert not h4_meets_threshold(rho_two_8, s6)

    rho_identity_6 = float(spearmanr(range(1, 7), range(1, 7)).statistic)
    assert rho_identity_6 == 1.0
    assert h4_meets_threshold(rho_identity_6 - 1e-16, 1.0)
    rho_one_6 = float(spearmanr(range(1, 7), [2, 1, 3, 4, 5, 6]).statistic)
    assert not h4_meets_threshold(rho_one_6, 1.0)
    assert not h4_is_testable(3, s6)
    assert h4_is_testable(4, s6)
