"""Evaluate registered S6 frequency-recency empirical rate table on DEV folds."""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from features.day2_data import LABEL_T_CANDIDATES, load_dev_orders  # noqa: E402
from features.repurchase_v3 import build_multisnapshot_folds, build_multisnapshot_samples  # noqa: E402
from models.repurchase_v3 import _metric_bundle, _ranking_tables, _bootstrap_ci, SEED, BOOTSTRAP_DRAWS  # noqa: E402

FREQS = ("1", "2", ">=3")
RECENCY_BANDS = ("<=30", "31-90", "91-180", ">180")
MIN_TRAIN = 100


def _bins(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    f = out.frequency.astype(int)
    out["freq_bin"] = np.select([f == 1, f == 2, f >= 3], FREQS, default="1")
    r = out.recency_days.astype(int)
    out["recency_bin"] = np.select([r <= 30, r <= 90, r <= 180], RECENCY_BANDS[:3], default=RECENCY_BANDS[3])
    return out


def _train_mapping(train: pd.DataFrame) -> tuple[dict, list[dict]]:
    b = _bins(train)
    mapping: dict[str, dict] = {}
    audit: list[dict] = []
    frequency_groups = [{"members": [freq], "n": int((b.freq_bin == freq).sum())} for freq in FREQS]
    while len(frequency_groups) > 1:
        small = [i for i, g in enumerate(frequency_groups) if g["n"] < MIN_TRAIN]
        if not small:
            break
        idx = min(small, key=lambda i: (frequency_groups[i]["n"], min(FREQS.index(x) for x in frequency_groups[i]["members"])))
        neighbors = [j for j in (idx - 1, idx + 1) if 0 <= j < len(frequency_groups)]
        target = max(neighbors, key=lambda j: (frequency_groups[j]["n"], -min(FREQS.index(x) for x in frequency_groups[j]["members"])))
        lo, hi = sorted((idx, target))
        merged = {"members": frequency_groups[lo]["members"] + frequency_groups[hi]["members"],
                  "n": frequency_groups[lo]["n"] + frequency_groups[hi]["n"]}
        frequency_groups[lo:hi + 1] = [merged]
    for fg in frequency_groups:
        freq = "+".join(fg["members"])
        row = b[b.freq_bin.isin(fg["members"])]
        groups = [{"bands": [band], "n": int((row.recency_bin == band).sum()),
                   "positive": int(row.loc[row.recency_bin == band, "label_returned"].sum())}
                  for band in RECENCY_BANDS]
        while len(groups) > 1:
            small = [i for i, g in enumerate(groups) if g["n"] < MIN_TRAIN]
            if not small:
                break
            idx = min(small, key=lambda i: (groups[i]["n"], min(RECENCY_BANDS.index(x) for x in groups[i]["bands"])))
            adjacent = [j for j in (idx - 1, idx + 1) if 0 <= j < len(groups)]
            target = max(adjacent, key=lambda j: (groups[j]["n"], -min(RECENCY_BANDS.index(x) for x in groups[j]["bands"])))
            lo, hi = sorted((idx, target))
            merged = {"bands": groups[lo]["bands"] + groups[hi]["bands"],
                      "n": groups[lo]["n"] + groups[hi]["n"],
                      "positive": groups[lo]["positive"] + groups[hi]["positive"]}
            groups[lo:hi + 1] = [merged]
        mapping[freq] = {band: group for group in groups for band in group["bands"]}
        for group in groups:
            fallback = group["n"] < MIN_TRAIN
            rate = float(b.label_returned.mean()) if fallback and len(b) else (group["positive"] / group["n"] if group["n"] else float(b.label_returned.mean()))
            group_out = {**group, "frequency_bin": freq, "original_frequency_bins": fg["members"],
                         "fallback_full_train": fallback, "rate": rate}
            audit.append(group_out)
    return mapping, audit


def _score_validation(valid: pd.DataFrame, mapping: dict, audit: list[dict], train_prevalence: float) -> np.ndarray:
    b = _bins(valid)
    lookup = {}
    freq_merge = {}
    freq_alias = {}
    for item in audit:
        for original in item["original_frequency_bins"]:
            freq_alias[original] = item["frequency_bin"]
        for band in item["bands"]:
            lookup[(item["frequency_bin"], band)] = float(item["rate"])
    scores = []
    for row in b.itertuples(index=False):
        freq = freq_alias.get(row.freq_bin, row.freq_bin)
        score = lookup.get((freq, row.recency_bin), train_prevalence)
        scores.append(score)
    return np.asarray(scores, dtype=float)


def evaluate(frame: pd.DataFrame, folds: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    pred_rows, metric_rows, rates_rows = [], [], []
    for fold_no, fold in enumerate(folds, 1):
        train = frame.iloc[fold["train"]].reset_index(drop=True)
        valid = frame.iloc[fold["validation"]]
        mapping, audit = _train_mapping(train)
        scores = _score_validation(valid, mapping, audit, float(train.label_returned.mean()))
        y = valid.label_returned.astype(int).to_numpy()
        metrics = _metric_bundle(y, scores)
        metric_rows.append({"strategy": "S6_frequency_recency_rate", "fold": fold_no,
                            "validation_T": str(fold["validation_t"]), "train_n": len(train),
                            "validation_n": len(valid), "train_customers": int(train.customer_key.nunique()),
                            "validation_customers": int(valid.customer_key.nunique()),
                            "positive_n": int(y.sum()), "prevalence": float(y.mean()), **metrics})
        for ix, (_, row) in enumerate(valid.iterrows()):
            pred_rows.append({"strategy": "S6_frequency_recency_rate", "customer_key": row.customer_key,
                              "label_returned": int(row.label_returned), "score": float(scores[ix]),
                              "fold": fold_no, "as_of": str(row.as_of)})
        for record in audit:
            val_bins = _bins(valid)
            val_rows = val_bins[
                val_bins.freq_bin.isin(record["original_frequency_bins"])
                & val_bins.recency_bin.isin(record["bands"])
            ]
            val_n = len(val_rows)
            rate_record = {"fold": fold_no, "validation_T": str(fold["validation_t"]),
                           **record, "validation_n": val_n,
                           "validation_positive_n": int(val_rows.label_returned.sum()) if val_n >= 30 else None,
                           "validation_observed_rate": float(val_rows.label_returned.mean()) if val_n >= 30 else None,
                           "validation_suppressed": bool(val_n < 30)}
            rates_rows.append(rate_record)
    pred = pd.DataFrame(pred_rows)
    pooled = [{"strategy": s, "n": len(g), "customers": int(g.customer_key.nunique()),
               "positive_n": int(g.label_returned.sum()), "prevalence": float(g.label_returned.mean()),
               **_metric_bundle(g.label_returned.to_numpy(), g.score.to_numpy())}
              for s, g in pred.groupby("strategy", sort=True)]
    deciles, topk = _ranking_tables(pred.drop(columns="as_of").rename(columns={"fold": "as_of"}))
    calibration = []
    for fold_or_pooled, group in [(f"fold_{f}", g) for f, g in pred.groupby("fold")]:
        calibration.append({"fold_or_pooled": fold_or_pooled, "n": len(group),
                            "mean_predicted": float(group.score.mean()),
                            "observed_rate": float(group.label_returned.mean()),
                            "brier": _metric_bundle(group.label_returned.to_numpy(), group.score.to_numpy())["brier"]})
    calibration.append({"fold_or_pooled": "pooled", "n": len(pred),
                        "mean_predicted": float(pred.score.mean()),
                        "observed_rate": float(pred.label_returned.mean()),
                        "brier": _metric_bundle(pred.label_returned.to_numpy(), pred.score.to_numpy())["brier"]})
    ci = _bootstrap_ci(pred[["strategy", "customer_key", "label_returned", "score"]], draws=BOOTSTRAP_DRAWS, seed=SEED)
    # Paired customer-cluster bootstrap for top-decile lift (ratio within each draw).
    rng = np.random.default_rng(SEED)
    ids = pred.customer_key.drop_duplicates().to_numpy()
    customer_index = pd.Index(ids).get_indexer(pred.customer_key)
    y = pred.label_returned.to_numpy(dtype=int)
    scores = pred.score.to_numpy(dtype=float)
    order = np.lexsort((pred.customer_key.astype(str).to_numpy(), -scores))
    lifts = []
    for _ in range(BOOTSTRAP_DRAWS):
        multiplicity = rng.multinomial(len(ids), np.full(len(ids), 1 / len(ids)))
        weights = multiplicity[customer_index]
        total = weights.sum()
        positives = np.dot(weights, y)
        if total <= 0 or positives <= 0:
            continue
        target = total * .10
        sorted_weights, sorted_y = weights[order], y[order]
        cumulative = np.cumsum(sorted_weights)
        positive_mass = 0.0
        remaining = target
        for w, value in zip(sorted_weights, sorted_y):
            take = min(float(w), remaining)
            positive_mass += take * value
            remaining -= take
            if remaining <= 0:
                break
        precision = positive_mass / target
        lifts.append(float(precision / (positives / total)))
    ci["S6_frequency_recency_rate"]["top_decile_lift"] = {
        "lower_95": float(np.quantile(lifts, .025)) if lifts else None,
        "upper_95": float(np.quantile(lifts, .975)) if lifts else None,
        "valid_draws": len(lifts),
    }
    return pd.DataFrame(metric_rows), rates_rows, deciles, {"predictions": pred, "top_k": topk,
        "calibration": calibration, "pooled": pooled, "bootstrap_95": ci}


def main() -> int:
    orders, scope, _ = load_dev_orders()
    if scope.get("test_labels_loaded") or scope.get("test_behavior_loaded"):
        raise RuntimeError("DEV loader reported test access")
    frame = build_multisnapshot_samples(orders, test_start=date(2025, 10, 22), candidates=LABEL_T_CANDIDATES)
    folds = build_multisnapshot_folds(frame)
    fold_metrics, rates, deciles, extra = evaluate(frame, folds)
    plan_hash = hashlib.sha256((ROOT / "docs/analysis_plan_wp5c.md").read_bytes()).hexdigest()
    metrics = {"status": "exploratory_dev_only_not_confirmed_out_of_sample",
               "test_raw_or_labels_read": False, "plan_sha256": plan_hash,
               "fold_count": len(folds), "snapshots": len(frame), "customers": int(frame.customer_key.nunique()),
               "pooled": extra["pooled"], "bootstrap_95": extra["bootstrap_95"],
               "calibration": extra["calibration"], "seed": SEED, "bootstrap_draws": BOOTSTRAP_DRAWS}
    (ROOT / "outputs/metrics/repurchase_wp5c_dev.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fold_metrics.to_csv(ROOT / "outputs/tables/repurchase_wp5c_fold_metrics.csv", index=False, float_format="%.6f")
    pd.DataFrame(rates).to_csv(ROOT / "outputs/tables/repurchase_wp5c_train_rates.csv", index=False, float_format="%.6f")
    pd.DataFrame(rates).to_csv(ROOT / "outputs/tables/repurchase_wp5c_calibration_cells.csv", index=False, float_format="%.6f")
    deciles.to_csv(ROOT / "outputs/tables/repurchase_wp5c_deciles.csv", index=False, float_format="%.6f")
    extra["top_k"].to_csv(ROOT / "outputs/tables/repurchase_wp5c_top_k.csv", index=False, float_format="%.6f")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
