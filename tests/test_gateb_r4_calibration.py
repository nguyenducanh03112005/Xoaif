from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from calibrate_gateb_r4_dev import calibrate  # noqa: E402


def test_gateb_r4_calibration_uses_registered_cells_and_counts_dev_combo_filter(tmp_path: Path) -> None:
    rows = []
    anchors = pd.date_range("2024-05-01", periods=12, freq="MS")
    for half, dates in enumerate((anchors[:6], anchors[6:])):
        for i, anchor in enumerate(dates):
            for group_n in range(30):
                returned = int((group_n % 10) < (i + 1 if half == 0 else i + 2))
                rows.append({"customer_key": f"{half}-{i}-{group_n}", "as_of": anchor,
                             "frequency": 2, "recency_days": 10 + i,
                             "monetary": 1000.0, "label_returned": returned})
    combos = pd.DataFrame({
        "dev_lift": [1.1] + [0.9] * 23,
        "dev_kulczynski": [0.6] * 24,
        "dev_imbalance_ratio": [0.4] * 24,
    })
    combo_path = tmp_path / "frozen.csv"
    combos.to_csv(combo_path, index=False)

    result = calibrate(pd.DataFrame(rows), combo_path)

    assert result["status"] == "exploratory_dev_only_not_confirmed_out_of_sample"
    assert result["test_raw_or_labels_read"] is False
    assert result["dev_half_reference"]["s6"]["groups_n"] == 1
    assert result["h5"]["k_dev"] == 1
    assert result["s1_score_one_snapshots"] == len(rows)
