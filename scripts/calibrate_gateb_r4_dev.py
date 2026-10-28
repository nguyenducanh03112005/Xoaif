"""DEV-only calibration for the preregistered Gate B R4 criteria."""

from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from features.day2_data import LABEL_T_CANDIDATES, load_dev_orders  # noqa: E402
from features.repurchase_v3 import build_multisnapshot_samples  # noqa: E402
from analyze_customer_value_dev import rfm_action_group  # noqa: E402

DEV_END = date(2025, 10, 22)
MIN_CELL_N = 30
HIGH_VALUE_CUT_VND = 830_000


def _cell(frame: pd.DataFrame, group: pd.Series) -> dict[str, tuple[int, int]]:
    out = {}
    for key in sorted(group.unique()):
        rows = frame.loc[group == key, "label_returned"]
        out[str(key)] = (int(len(rows)), int(rows.sum()))
    return out


def _rho(first: dict[str, tuple[int, int]], second: dict[str, tuple[int, int]]) -> dict:
    common = [key for key in sorted(first) if first[key][0] >= MIN_CELL_N and second.get(key, (0, 0))[0] >= MIN_CELL_N]
    if len(common) < 2:
        return {"rho": None, "groups_n": len(common), "groups_used": common}
    r = spearmanr([first[k][1] / first[k][0] for k in common],
                  [second[k][1] / second[k][0] for k in common]).statistic
    return {"rho": None if not np.isfinite(r) else float(r), "groups_n": len(common), "groups_used": common}


def _s6_key(frame: pd.DataFrame) -> pd.Series:
    frequency = pd.to_numeric(frame.frequency)
    recency = pd.to_numeric(frame.recency_days)
    f = np.select([frequency == 1, frequency == 2, frequency >= 3], ["1", "2", ">=3"], default="1")
    r = np.select([recency <= 30, recency <= 90, recency <= 180], ["<=30", "31-90", "91-180"], default=">180")
    return pd.Series([f"{a}|{b}" for a, b in zip(f, r)], index=frame.index)


def _dev_halves(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    anchors = sorted(pd.to_datetime(frame.as_of).drop_duplicates())
    if len(anchors) != 12:
        raise ValueError(f"Expected 12 preregistered DEV anchors, found {len(anchors)}")
    first = frame[pd.to_datetime(frame.as_of).isin(anchors[:6])].copy()
    second = frame[pd.to_datetime(frame.as_of).isin(anchors[6:])].copy()
    return first, second


def calibrate(frame: pd.DataFrame, combo_path: Path) -> dict:
    first, second = _dev_halves(frame)
    s6 = _rho(_cell(first, _s6_key(first)), _cell(second, _s6_key(second)))
    rfm_first = first.apply(lambda row: rfm_action_group(row.recency_days, row.frequency,
                                                         row.monetary, HIGH_VALUE_CUT_VND), axis=1)
    rfm_second = second.apply(lambda row: rfm_action_group(row.recency_days, row.frequency,
                                                           row.monetary, HIGH_VALUE_CUT_VND), axis=1)
    rfm = _rho(_cell(first, rfm_first), _cell(second, rfm_second))
    selected = pd.read_csv(combo_path, usecols=["dev_lift", "dev_kulczynski", "dev_imbalance_ratio"])
    if len(selected) != 24:
        raise ValueError(f"Expected 24 frozen combos, found {len(selected)}")
    passed = ((selected.dev_lift > 1) & (selected.dev_kulczynski >= .5)
              & (selected.dev_imbalance_ratio <= .5))
    point_rate = float(frame.loc[frame.frequency >= 2, "label_returned"].mean())
    return {
        "status": "exploratory_dev_only_not_confirmed_out_of_sample",
        "test_raw_or_labels_read": False,
        "cohort": "DEV multi-snapshot; 12 monthly anchors; N=180; L=7",
        "snapshots": int(len(frame)), "customers": int(frame.customer_key.nunique()),
        "s1_score_one_rate": point_rate,
        "s1_score_one_snapshots": int((frame.frequency >= 2).sum()),
        "s1_snapshot_n": int(len(frame)),
        "dev_half_reference": {"first_anchors": [str(x.date()) for x in sorted(pd.to_datetime(first.as_of).unique())],
                                "second_anchors": [str(x.date()) for x in sorted(pd.to_datetime(second.as_of).unique())],
                                "minimum_cell_n_each_half": MIN_CELL_N,
                                "s6": s6, "rfm": rfm,
                                "rfm_high_value_cut_vnd": HIGH_VALUE_CUT_VND},
        "h5": {"frozen_combo_count": 24, "k_dev": int(passed.sum()),
               "criteria": "DEV lift>1 AND Kulczynski>=0.5 AND imbalance_ratio<=0.5"},
    }


def main() -> int:
    orders, scope, _ = load_dev_orders()
    if scope.get("test_labels_loaded") or scope.get("test_behavior_loaded"):
        raise RuntimeError("DEV loader reported test access")
    frame = build_multisnapshot_samples(orders, test_start=DEV_END, candidates=LABEL_T_CANDIDATES)
    metrics = calibrate(frame, ROOT / "outputs/tables/combo_recommendation_screen_f3.csv")
    path = ROOT / "outputs/metrics/gateb_r4_dev_calibration.json"
    path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
