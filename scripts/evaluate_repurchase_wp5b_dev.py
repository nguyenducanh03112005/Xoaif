"""Evaluate preregistered interpretable repurchase strategies on DEV only."""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier, export_text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from features.day2_data import LABEL_T_CANDIDATES, load_dev_orders  # noqa: E402
from features.repurchase_v3 import build_multisnapshot_folds, build_multisnapshot_samples  # noqa: E402
from models.repurchase_v3 import (  # noqa: E402
    BOOTSTRAP_DRAWS, MODEL_FEATURES, SEED, _metric_bundle, _new_model,
    _ranking_tables, _bootstrap_ci,
)

OUTER_STRATEGIES = ("S1_frequency_rule", "S2_frequency_recency_rule", "S3_shallow_tree", "S4_unweighted_sigmoid", "S5_logistic_v3")
THRESHOLDS = (30, 60, 90, 180)


def _lr(*, balanced: bool) -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(
            C=10, class_weight="balanced" if balanced else None,
            solver="lbfgs", max_iter=2000, random_state=SEED,
        )),
    ])


def _rule(frame: pd.DataFrame, threshold: int | None = None) -> np.ndarray:
    pred = frame["frequency"].to_numpy(dtype=float) >= 2
    if threshold is not None:
        pred &= frame["recency_days"].to_numpy(dtype=float) <= threshold
    return pred.astype(float)


def _inner_oof(train: pd.DataFrame, *, balanced: bool) -> tuple[np.ndarray, np.ndarray]:
    folds = build_multisnapshot_folds(train.reset_index(drop=True), minimum_train_rows=30)
    scores: list[float] = []
    labels: list[int] = []
    for fold in folds:
        part_train = train.iloc[fold["train"]]
        part_valid = train.iloc[fold["validation"]]
        y_train = part_train["label_returned"].astype(int).to_numpy()
        if len(np.unique(y_train)) < 2:
            continue
        model = _lr(balanced=balanced)
        model.fit(part_train[MODEL_FEATURES], y_train)
        scores.extend(model.predict_proba(part_valid[MODEL_FEATURES])[:, 1].tolist())
        labels.extend(part_valid["label_returned"].astype(int).tolist())
    return np.asarray(scores, dtype=float), np.asarray(labels, dtype=int)


def _calibration_coefficients(y: np.ndarray, score: np.ndarray) -> tuple[float | None, float | None]:
    valid = np.isfinite(score) & (score >= 0) & (score <= 1)
    if valid.sum() < 30 or len(np.unique(y[valid])) < 2 or np.unique(score[valid]).size < 3:
        return None, None
    clipped = np.clip(score[valid], 1e-8, 1 - 1e-8)
    logits = np.log(clipped / (1 - clipped)).reshape(-1, 1)
    calibration = LogisticRegression(C=1e6, solver="lbfgs", max_iter=2000, random_state=SEED)
    calibration.fit(logits, y[valid])
    return float(calibration.intercept_[0]), float(calibration.coef_[0, 0])


def _bootstrap_calibration_ci(pred: pd.DataFrame, draws: int = BOOTSTRAP_DRAWS, seed: int = SEED) -> dict:
    """Customer-cluster bootstrap CIs for pooled calibration intercept/slope."""
    result: dict[str, dict] = {}
    rng = np.random.default_rng(seed)
    for strategy, group in pred.groupby("strategy", sort=True):
        original_score = group.score.to_numpy(dtype=float)
        if np.unique(original_score[np.isfinite(original_score)]).size < 3:
            result[strategy] = {"intercept_lower_95": None, "intercept_upper_95": None,
                                "slope_lower_95": None, "slope_upper_95": None, "valid_draws": 0}
            continue
        ids = group.customer_key.drop_duplicates().to_numpy()
        customer_idx = pd.Index(ids).get_indexer(group.customer_key)
        y = group.label_returned.to_numpy(dtype=float)
        p = np.clip(group.score.to_numpy(dtype=float), 1e-8, 1 - 1e-8)
        x = np.log(p / (1 - p))
        valid = np.isfinite(x)
        x, y, customer_idx = x[valid], y[valid], customer_idx[valid]
        if np.unique(p[valid]).size < 2 or np.unique(y).size < 2:
            result[strategy] = {"intercept_lower_95": None, "intercept_upper_95": None,
                                "slope_lower_95": None, "slope_upper_95": None, "valid_draws": 0}
            continue
        estimates_i: list[float] = []
        estimates_s: list[float] = []
        design = np.column_stack([np.ones(len(x)), x])
        for _ in range(draws):
            multiplicity = rng.multinomial(len(ids), np.full(len(ids), 1 / len(ids)))
            weights = multiplicity[customer_idx].astype(float)
            if np.dot(weights, y) <= 0 or np.dot(weights, 1 - y) <= 0:
                continue
            beta = np.zeros(2, dtype=float)
            for _step in range(40):
                eta = np.clip(design @ beta, -30, 30)
                prob = 1 / (1 + np.exp(-eta))
                grad = design.T @ (weights * (y - prob))
                curvature = weights * prob * (1 - prob)
                hessian = (design.T * curvature) @ design + np.eye(2) * 1e-8
                try:
                    update = np.linalg.solve(hessian, grad)
                except np.linalg.LinAlgError:
                    break
                beta += update
                if np.max(np.abs(update)) < 1e-7:
                    break
            if np.all(np.isfinite(beta)) and np.max(np.abs(beta)) < 100:
                estimates_i.append(float(beta[0]))
                estimates_s.append(float(beta[1]))
        result[strategy] = {
            "intercept_lower_95": float(np.quantile(estimates_i, 0.025)) if estimates_i else None,
            "intercept_upper_95": float(np.quantile(estimates_i, 0.975)) if estimates_i else None,
            "slope_lower_95": float(np.quantile(estimates_s, 0.025)) if estimates_s else None,
            "slope_upper_95": float(np.quantile(estimates_s, 0.975)) if estimates_s else None,
            "valid_draws": len(estimates_i),
        }
    return result


def _calibration_table(pred: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for strategy, group in pred.groupby("strategy", sort=True):
        if group["score"].nunique() < 2:
            rows.append({"strategy": strategy, "bin": "all", "n": len(group),
                         "mean_predicted": float(group.score.mean()),
                         "observed_rate": float(group.label_returned.mean())})
            continue
        bins = pd.qcut(group["score"].rank(method="first"), q=min(10, len(group)),
                       labels=False, duplicates="drop") + 1
        for bin_id, part in group.assign(bin=bins).groupby("bin", sort=True):
            rows.append({"strategy": strategy, "bin": int(bin_id), "n": len(part),
                         "mean_predicted": float(part.score.mean()),
                         "observed_rate": float(part.label_returned.mean())})
    return pd.DataFrame(rows)


def _select_candidate(fold_frame: pd.DataFrame, monotonicity: dict, fold_count: int) -> str | None:
    means = fold_frame.groupby("strategy").average_precision.mean().to_dict()
    eligible = [s for s in OUTER_STRATEGIES
                if monotonicity.get(s, {}).get("monotonic_descending")
                and s in means and int((fold_frame.strategy == s).sum()) == fold_count]
    if not eligible:
        return None
    best = max(float(means[s]) for s in eligible)
    tied = [s for s in eligible if best - float(means[s]) <= 0.001]
    return min(tied, key=list(OUTER_STRATEGIES).index)


def run_wp5b(frame: pd.DataFrame, folds: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    prediction_rows: list[dict] = []
    fold_rows: list[dict] = []
    failures: list[dict] = []
    tree_rules: list[dict] = []
    threshold_choices: list[dict] = []

    for fold_no, fold in enumerate(folds, start=1):
        train = frame.iloc[fold["train"]].reset_index(drop=True)
        valid = frame.iloc[fold["validation"]]
        y_train = train.label_returned.astype(int).to_numpy()
        y_valid = valid.label_returned.astype(int).to_numpy()
        scores_by_strategy: dict[str, np.ndarray] = {"S1_frequency_rule": _rule(valid)}

        inner_folds = build_multisnapshot_folds(train, minimum_train_rows=30)
        threshold_scores: dict[int, list[float]] = {t: [] for t in THRESHOLDS}
        for inner in inner_folds:
            inner_valid = train.iloc[inner["validation"]]
            iy = inner_valid.label_returned.astype(int).to_numpy()
            if len(np.unique(iy)) < 2:
                continue
            for threshold in THRESHOLDS:
                threshold_scores[threshold].append(average_precision_score(iy, _rule(inner_valid, threshold)))
        eligible = {t: vals for t, vals in threshold_scores.items() if vals}
        if eligible:
            chosen = min(eligible, key=lambda t: (-float(np.mean(eligible[t])), t))
            scores_by_strategy["S2_frequency_recency_rule"] = _rule(valid, chosen)
            threshold_choices.append({"fold": fold_no, "validation_T": str(fold["validation_t"]),
                                      "selected_days": chosen,
                                      "inner_mean_ap": float(np.mean(eligible[chosen])),
                                      "inner_fold_count": len(eligible[chosen])})
        else:
            failures.append({"strategy": "S2_frequency_recency_rule", "fold": fold_no,
                             "reason": "no eligible inner temporal validation fold"})

        tree = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("classifier", DecisionTreeClassifier(max_depth=3, min_samples_leaf=50, random_state=SEED)),
        ])
        tree.fit(train[MODEL_FEATURES], y_train)
        scores_by_strategy["S3_shallow_tree"] = tree.predict_proba(valid[MODEL_FEATURES])[:, 1]
        tree_rules.append({"fold": fold_no, "validation_T": str(fold["validation_t"]),
                           "if_then": export_text(tree.named_steps["classifier"], feature_names=MODEL_FEATURES)})

        inner_score, inner_y = _inner_oof(train, balanced=False)
        if len(inner_score) == 0 or len(np.unique(inner_y)) < 2:
            failures.append({"strategy": "S4_unweighted_sigmoid", "fold": fold_no,
                             "reason": "no usable inner temporal OOF scores with both classes"})
        else:
            base = _lr(balanced=False)
            base.fit(train[MODEL_FEATURES], y_train)
            raw_inner = np.clip(inner_score, 1e-8, 1 - 1e-8)
            calibrator = LogisticRegression(C=1e6, solver="lbfgs", max_iter=2000, random_state=SEED)
            calibrator.fit(np.log(raw_inner / (1 - raw_inner)).reshape(-1, 1), inner_y)
            raw_valid = np.clip(base.predict_proba(valid[MODEL_FEATURES])[:, 1], 1e-8, 1 - 1e-8)
            scores_by_strategy["S4_unweighted_sigmoid"] = calibrator.predict_proba(
                np.log(raw_valid / (1 - raw_valid)).reshape(-1, 1)
            )[:, 1]

        reference = _new_model()
        reference.fit(train[MODEL_FEATURES], y_train)
        scores_by_strategy["S5_logistic_v3"] = reference.predict_proba(valid[MODEL_FEATURES])[:, 1]

        for strategy, score in scores_by_strategy.items():
            values = _metric_bundle(y_valid, score)
            fold_rows.append({"strategy": strategy, "fold": fold_no,
                              "validation_T": str(fold["validation_t"]), "train_n": len(train),
                              "validation_n": len(valid), "train_customers": int(train.customer_key.nunique()),
                              "validation_customers": int(valid.customer_key.nunique()),
                              "positive_n": int(y_valid.sum()), "prevalence": float(y_valid.mean()), **values})
            for ix, (_, row) in enumerate(valid.iterrows()):
                prediction_rows.append({"strategy": strategy, "customer_key": row.customer_key,
                                        "label_returned": int(row.label_returned), "score": float(score[ix]),
                                        "fold": fold_no, "as_of": str(row.as_of)})

    pred = pd.DataFrame(prediction_rows)
    pooled_rows = []
    for strategy, group in pred.groupby("strategy", sort=True):
        pooled_rows.append({"strategy": strategy, "n": len(group),
                            "customers": int(group.customer_key.nunique()),
                            "positive_n": int(group.label_returned.sum()),
                            "prevalence": float(group.label_returned.mean()),
                            **_metric_bundle(group.label_returned.to_numpy(), group.score.to_numpy())})
    # This helper already emits both per-fold and pooled tables in one call.
    deciles, top_k = _ranking_tables(pred.drop(columns="as_of").rename(columns={"fold": "as_of"}))
    pooled_decile = deciles[deciles.fold_or_pooled == "pooled"]
    monotonicity = {}
    for strategy, group in pooled_decile.groupby("strategy"):
        rates = group.sort_values("decile_from_top").positive_rate.to_numpy(dtype=float)
        violations = int(np.sum(np.diff(rates) > 1e-12))
        monotonicity[strategy] = {"adjacent_violations": violations,
                                  "monotonic_descending": violations == 0,
                                  "score_ties_may_split_across_deciles": True}
    calibration_rows = []
    for strategy, group in pred.groupby("strategy", sort=True):
        intercept, slope = _calibration_coefficients(group.label_returned.to_numpy(), group.score.to_numpy())
        calibration_rows.append({"strategy": strategy, "scope": "pooled_oof",
                                 "calibration_intercept": intercept, "calibration_slope": slope,
                                 "brier": _metric_bundle(group.label_returned.to_numpy(), group.score.to_numpy())["brier"]})
        for fold_no, part in group.groupby("fold"):
            fi, fs = _calibration_coefficients(part.label_returned.to_numpy(), part.score.to_numpy())
            calibration_rows.append({"strategy": strategy, "scope": f"fold_{fold_no}",
                                     "calibration_intercept": fi, "calibration_slope": fs,
                                     "brier": _metric_bundle(part.label_returned.to_numpy(), part.score.to_numpy())["brier"]})
    ci = _bootstrap_ci(pred[["strategy", "customer_key", "label_returned", "score"]],
                       draws=BOOTSTRAP_DRAWS, seed=SEED)
    calibration_ci = _bootstrap_calibration_ci(
        pred[["strategy", "customer_key", "label_returned", "score"]], draws=BOOTSTRAP_DRAWS, seed=SEED)
    fold_frame = pd.DataFrame(fold_rows)
    fold_means = fold_frame.groupby("strategy").average_precision.mean().to_dict()
    selected = _select_candidate(fold_frame, monotonicity, len(folds))
    summary = {
        "status": "completed", "scope": "DEV-only, khám phá, chưa xác nhận ngoài mẫu",
        "snapshot": "20261024T052943Z", "outer_fold_count": len(folds),
        "protocol_sha256": hashlib.sha256((ROOT / "docs/analysis_plan_wp5b.md").read_bytes()).hexdigest(),
        "seed": SEED, "bootstrap_draws": BOOTSTRAP_DRAWS,
        "selection_rule": "highest mean outer-fold AP among complete strategies with monotonic pooled decile rates; ties within 0.001 choose simpler registered order",
        "mean_fold_ap": {str(k): float(v) for k, v in fold_means.items()},
        "monotonicity": monotonicity, "candidate_for_later_review": selected,
        "failures": failures, "threshold_choices": threshold_choices,
        "bootstrap_95": ci, "calibration": calibration_rows,
        "calibration_bootstrap_95": calibration_ci,
        "pooled": pooled_rows, "comparison_count": 5, "threshold_search_count": len(THRESHOLDS),
        "notes": ["No test records or labels accessed.",
                  "Brier for raw binary rules/tree outputs is descriptive and not directly comparable as calibrated probability quality.",
                  "Bootstrap resamples customers and carries all of each sampled customer's snapshots."]
    }
    return pred, fold_frame, deciles, {"summary": summary, "top_k": top_k,
                                      "calibration_table": _calibration_table(pred),
                                      "tree_rules": tree_rules}


def main() -> int:
    orders, metadata, _ = load_dev_orders()
    test_start = date.fromisoformat(metadata["test_start_exclusive"])
    frame = build_multisnapshot_samples(orders, test_start=test_start, candidates=LABEL_T_CANDIDATES)
    folds = build_multisnapshot_folds(frame)
    pred, fold_metrics, deciles, extra = run_wp5b(frame, folds)
    out = ROOT / "outputs"
    (out / "metrics").mkdir(parents=True, exist_ok=True)
    (out / "tables").mkdir(parents=True, exist_ok=True)
    (out / "metrics" / "repurchase_wp5b_dev.json").write_text(
        json.dumps({**extra["summary"], "sample_snapshots": int(len(frame)),
                    "sample_customers": int(frame.customer_key.nunique())}, ensure_ascii=False, indent=2), encoding="utf-8")
    fold_metrics.to_csv(out / "tables" / "repurchase_wp5b_fold_metrics.csv", index=False)
    deciles.to_csv(out / "tables" / "repurchase_wp5b_deciles.csv", index=False)
    extra["top_k"].to_csv(out / "tables" / "repurchase_wp5b_top_k.csv", index=False)
    extra["calibration_table"].to_csv(out / "tables" / "repurchase_wp5b_calibration.csv", index=False)
    pd.DataFrame(extra["tree_rules"]).to_csv(out / "tables" / "repurchase_wp5b_tree_rules.csv", index=False)
    pd.DataFrame(extra["summary"]["threshold_choices"]).to_csv(out / "tables" / "repurchase_wp5b_thresholds.csv", index=False)
    print(json.dumps({"folds": len(folds), "snapshots": len(frame), "customers": frame.customer_key.nunique(),
                      "pooled": extra["summary"]["pooled"], "failures": extra["summary"]["failures"],
                      "candidate": extra["summary"]["candidate_for_later_review"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
