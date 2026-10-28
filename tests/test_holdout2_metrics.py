from __future__ import annotations

import numpy as np
import pandas as pd

from features.holdout2_metrics import (customer_cluster_bootstrap, holm_step_down,
                                       precision_at_k_tie_aware, risk_ratio, roc_auc)


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
