from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from freeze_gateb_strategies_dev import _sign_fit  # noqa: E402


def test_gateb_r5_univariate_direction_comes_from_dev_fit() -> None:
    frame = pd.DataFrame({
        "recency_days": list(range(99, -1, -1)),
        "frequency": list(range(100)),
        "label_returned": [int(i >= 50) for i in range(100)],
    })
    recency = _sign_fit(frame, "recency_days")
    frequency = _sign_fit(frame, "frequency")
    assert recency["direction"] == -1
    assert frequency["direction"] == 1
    assert recency["scoring_rule"] == "standardize(recency_days) * sign(coef)"
