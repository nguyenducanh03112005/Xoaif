"""Estimate DEV-only repeat risk ratio for the preregistered Gate B R2 plan."""
from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from features.day2_data import LABEL_T_CANDIDATES, load_dev_orders  # noqa: E402
from features.repurchase_v3 import build_multisnapshot_samples  # noqa: E402

SEED = 20261028
BOOTSTRAP_DRAWS = 2000
DEV_END = date(2025, 10, 22)


def group_summary(frame: pd.DataFrame, group_mask: np.ndarray) -> dict[str, int | float]:
    group = frame.loc[group_mask]
    return {
        "snapshots": int(len(group)),
        "customers": int(group.customer_key.nunique()),
        "positive_snapshots": int(group.label_returned.sum()),
        "repeat_rate": float(group.label_returned.mean()) if len(group) else float("nan"),
    }


def bootstrap_rr(frame: pd.DataFrame, *, draws: int = BOOTSTRAP_DRAWS, seed: int = SEED) -> dict:
    ids = frame.customer_key.drop_duplicates().to_numpy()
    customer_index = pd.Index(ids).get_indexer(frame.customer_key)
    freq2 = frame.frequency.to_numpy(dtype=int) >= 2
    y = frame.label_returned.to_numpy(dtype=int)
    n2 = int(freq2.sum())
    n1 = len(freq2) - n2
    if n1 == 0 or n2 == 0:
        raise ValueError("Both frequency groups must be present")
    rng = np.random.default_rng(seed)
    estimates: list[float] = []
    invalid = 0
    for _ in range(draws):
        multiplicity = rng.multinomial(len(ids), np.full(len(ids), 1 / len(ids)))
        weight = multiplicity[customer_index]
        w2, w1 = weight[freq2].sum(), weight[~freq2].sum()
        p2 = np.dot(weight[freq2], y[freq2]) / w2 if w2 else float("nan")
        p1 = np.dot(weight[~freq2], y[~freq2]) / w1 if w1 else float("nan")
        if not np.isfinite(p1) or not np.isfinite(p2) or p1 <= 0:
            invalid += 1
            continue
        estimates.append(float(p2 / p1))
    if not estimates:
        raise ValueError("No valid bootstrap draws for RR")
    return {
        "rr": float(group_summary(frame, freq2)["repeat_rate"] / group_summary(frame, ~freq2)["repeat_rate"]),
        "ci95_lower": float(np.quantile(estimates, 0.025)),
        "ci95_upper": float(np.quantile(estimates, 0.975)),
        "bootstrap_draws_requested": draws,
        "bootstrap_draws_valid": len(estimates),
        "bootstrap_draws_invalid": invalid,
        "bootstrap_seed": seed,
        "bootstrap_unit": "customer cluster; all snapshots of a sampled customer move together",
    }


def calculate(orders: list[dict]) -> dict:
    split = yaml.safe_load((ROOT / "config/split.yaml").read_text(encoding="utf-8"))
    t_end = date.fromisoformat(str(split["test_start"]))
    frame = build_multisnapshot_samples(
        orders,
        test_start=t_end,
        n_days=int(split["primary_n_days"]),
        l_days=int(split["l_candidates_days"][0]),
        candidates=LABEL_T_CANDIDATES,
    )
    frequency_ge2 = frame.frequency.astype(int).to_numpy() >= 2
    result = {
        "status": "exploratory_dev_only_not_confirmed_out_of_sample",
        "preregistration": "docs/analysis_plan_gateb_r2.md",
        "snapshot_id": split["snapshot_id"],
        "cohort": "DEV multi-snapshot; T+180+7 strictly before DEV end 2025-10-22",
        "label_definition": "valid status-3 non-gift purchase in (T,T+180d], consistent with F1 later-local-date repeat definition",
        "weighting": "snapshot-weighted group rates; customer-cluster bootstrap",
        "n_snapshots": int(len(frame)),
        "n_unique_customers": int(frame.customer_key.nunique()),
        "frequency_eq_1": group_summary(frame, ~frequency_ge2),
        "frequency_ge_2": group_summary(frame, frequency_ge2),
        "rr_frequency_ge_2_vs_eq_1": bootstrap_rr(frame),
        "test_rows_loaded": False,
        "test_labels_or_behavior_used": False,
    }
    return result


def rounded(value):
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, dict):
        return {key: rounded(item) for key, item in value.items()}
    if isinstance(value, list):
        return [rounded(item) for item in value]
    return value


def main() -> int:
    orders, scope, _ = load_dev_orders()
    if scope.get("test_labels_loaded") or scope.get("test_behavior_loaded"):
        raise RuntimeError("DEV loader reported test access")
    result = calculate(orders)
    target = ROOT / "outputs/metrics/gateb_r2_rr_dev.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    result = rounded(result)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
