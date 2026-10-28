"""Metric helpers for the preregistered, single-open HO2 evaluator."""

from __future__ import annotations

import math
from typing import Callable

import numpy as np
from sklearn.metrics import roc_auc_score

H4_SPEARMAN_ABS_TOLERANCE = 1e-9
H4_MIN_COMMON_GROUPS = 4


def h4_is_testable(common_group_count: int, threshold: float | None) -> bool:
    """Keep the preregistered four-group floor and reference-threshold guard."""
    return common_group_count >= H4_MIN_COMMON_GROUPS and threshold is not None and threshold >= .50


def h4_meets_threshold(rho: float | None, threshold: float | None) -> bool:
    """Compare Spearman rho with the locked threshold, allowing only FP noise."""
    if rho is None or threshold is None or not np.isfinite(rho) or not np.isfinite(threshold):
        return False
    return float(rho) >= float(threshold) - H4_SPEARMAN_ABS_TOLERANCE


def precision_at_k_tie_aware(y_true, scores, fraction: float = 0.10) -> dict:
    y = np.asarray(y_true, dtype=int)
    s = np.asarray(scores, dtype=float)
    if len(y) != len(s) or not len(y) or not np.isfinite(s).all():
        raise ValueError("y/scores must be non-empty, finite, and the same length")
    k = int(math.ceil(fraction * len(y)))
    cutoff = np.sort(s)[::-1][k - 1]
    above, tied = s > cutoff, s == cutoff
    n_above = int(above.sum())
    n_tie = int(tied.sum())
    q = (k - n_above) / n_tie
    precision = (int(y[above].sum()) + q * int(y[tied].sum())) / k
    prevalence = float(y.mean())
    return {"k": k, "cutoff": float(cutoff), "n_above": n_above, "n_tied": n_tie,
            "q": float(q), "precision": float(precision),
            "prevalence": prevalence,
            "lift": float(precision / prevalence) if prevalence else None}


def risk_ratio(y_true, groups) -> dict:
    y = np.asarray(y_true, dtype=int)
    g = np.asarray(groups, dtype=bool)
    pos_a, n_a = int(y[g].sum()), int(g.sum())
    pos_b, n_b = int(y[~g].sum()), int((~g).sum())
    if min(n_a, n_b) == 0 or pos_a == 0 or pos_b == 0:
        return {"rr": None, "positive_group": pos_a, "n_group": n_a,
                "positive_reference": pos_b, "n_reference": n_b}
    return {"rr": (pos_a / n_a) / (pos_b / n_b),
            "positive_group": pos_a, "n_group": n_a,
            "positive_reference": pos_b, "n_reference": n_b,
            "rate_group": pos_a / n_a, "rate_reference": pos_b / n_b}


def roc_auc(y_true, scores) -> float | None:
    y = np.asarray(y_true, dtype=int)
    s = np.asarray(scores, dtype=float)
    return float(roc_auc_score(y, s)) if len(np.unique(y)) == 2 else None


def customer_cluster_bootstrap(frame, statistic: Callable, *, draws: int = 2000,
                               seed: int = 20261028, customer_col: str = "customer_key") -> dict:
    """Percentile bootstrap sampling customers with all rows/snapshots together."""
    ids = frame[customer_col].drop_duplicates().to_numpy()
    if not len(ids):
        raise ValueError("no customers to bootstrap")
    groups = [frame.index[frame[customer_col] == key].to_numpy() for key in ids]
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(draws):
        picked = rng.integers(0, len(ids), size=len(ids))
        indices = np.concatenate([groups[i] for i in picked])
        estimate = statistic(frame.loc[indices])
        if estimate is not None and np.isfinite(estimate):
            values.append(float(estimate))
    return {"lower_95": float(np.quantile(values, .025)) if values else None,
            "upper_95": float(np.quantile(values, .975)) if values else None,
            "valid_draws": len(values), "requested_draws": draws, "seed": seed}


def holm_step_down(p_values: dict[str, float]) -> dict:
    if not p_values:
        return {}
    ordered = sorted(p_values.items(), key=lambda item: (item[1], item[0]))
    m = len(ordered)
    adjusted = {}
    running = 0.0
    for rank, (name, p) in enumerate(ordered):
        running = max(running, min(1.0, (m - rank) * float(p)))
        adjusted[name] = running
    return adjusted
