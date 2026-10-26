"""Single preregistered repurchase-feature experiment with temporal OOF inference."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

from features.day2b_data import make_repurchase_features
from models.classify import build_folds

ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP_REPEATS = 2000
BOOTSTRAP_SEED = 20261025
NUMERIC_BASE = [
    "recency_days", "frequency", "monetary", "average_order_value", "max_order_value",
    "total_quantity", "distinct_products", "mean_days_between_orders", "first_order_month",
    "first_order_month_sin", "first_order_month_cos", "nearest_holiday_distance_days",
    "adjustment_positive_rate", "adjustment_negative_rate", "no_history_after_sensitivity",
]
NUMERIC_NEW = [
    "last_order_product_count", "last_order_discount_rate", "last_order_revenue_recognized",
    "last_order_month", "last_order_month_sin", "last_order_month_cos",
    "last_order_holiday_distance_days",
]
CATEGORICAL_BASE = ["province"]
CATEGORICAL_NEW = ["last_order_primary_product_group", "last_order_channel", "last_order_province"]


def _preprocessor(numeric: list[str], categorical: list[str]) -> ColumnTransformer:
    numeric_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True)),
        ("scale", StandardScaler()),
    ])
    categorical_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="constant", fill_value="__MISSING__")),
        ("encode", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer([
        ("numeric", numeric_pipe, numeric),
        ("categorical", categorical_pipe, categorical),
    ], remainder="drop")


def _estimator(kind: str, params: dict[str, Any], seed: int):
    if kind == "logistic_regression":
        return LogisticRegression(C=float(params["C"]), class_weight="balanced", max_iter=2000, solver="lbfgs", random_state=seed)
    if kind == "decision_tree":
        return DecisionTreeClassifier(max_depth=int(params["max_depth"]), min_samples_leaf=5, class_weight="balanced", random_state=seed)
    if kind == "random_forest":
        return RandomForestClassifier(
            n_estimators=150, max_depth=params["max_depth"], min_samples_leaf=int(params["min_samples_leaf"]),
            max_features="sqrt", class_weight="balanced_subsample", n_jobs=1, random_state=seed,
        )
    raise ValueError(f"Unregistered estimator kind: {kind}")


def _pipeline(kind: str, params: dict[str, Any], numeric: list[str], categorical: list[str], seed: int) -> Pipeline:
    return Pipeline([("preprocess", _preprocessor(numeric, categorical)), ("model", _estimator(kind, params, seed))])


def _scores(model: Pipeline, frame: pd.DataFrame, feature_columns: list[str]) -> np.ndarray:
    probabilities = model.predict_proba(frame[feature_columns])
    classes = list(model.named_steps["model"].classes_)
    return probabilities[:, classes.index(1)] if 1 in classes else np.zeros(len(frame))


def _metrics(y: np.ndarray, scores: np.ndarray, threshold: float = .5) -> dict[str, Any]:
    pred = (scores >= threshold).astype(int)
    return {
        "precision": float(precision_score(y, pred, zero_division=0)),
        "recall": float(recall_score(y, pred, zero_division=0)),
        "f1": float(f1_score(y, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y, scores)) if len(np.unique(y)) == 2 else None,
        "pr_auc": float(average_precision_score(y, scores)) if len(y) else None,
        "confusion_matrix_tn_fp_fn_tp_at_threshold_0_5": confusion_matrix(y, pred, labels=[0, 1]).tolist(),
        "positive_count": int(y.sum()),
        "sample_count": int(len(y)),
    }


def _evaluate(frame: pd.DataFrame, folds: list[dict[str, Any]], kind: str, params: dict[str, Any], numeric: list[str], categorical: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[float]]:
    feature_columns = numeric + categorical
    labels = frame["label_returned"].astype(int).to_numpy()
    oof: list[dict[str, Any]] = []
    fold_metrics: list[dict[str, Any]] = []
    train_ap: list[float] = []
    for fold_index, fold in enumerate(folds):
        train = frame.iloc[fold["train"]]
        valid = frame.iloc[fold["validation"]]
        pipeline = _pipeline(kind, params, numeric, categorical, 42 + fold_index)
        pipeline.fit(train[feature_columns], labels[fold["train"]])
        valid_scores = _scores(pipeline, valid, feature_columns)
        fold_metric = _metrics(labels[fold["validation"]], valid_scores)
        fold_metric.update({
            "validation_T": str(fold["validation_t"]),
            "train_n": int(len(train)),
            "validation_n": int(len(valid)),
            "train_positive": int(labels[fold["train"]].sum()),
            "validation_positive": int(labels[fold["validation"]].sum()),
        })
        fold_metrics.append(fold_metric)
        train_scores = _scores(pipeline, train, feature_columns)
        train_ap.append(float(average_precision_score(labels[fold["train"]], train_scores)))
        oof.extend({"index": int(index), "score": float(score), "fold": fold_index} for index, score in zip(fold["validation"], valid_scores))
    return oof, fold_metrics, train_ap


def _mean(values: list[float | None]) -> float | None:
    usable = [float(value) for value in values if value is not None]
    return float(np.mean(usable)) if usable else None


def _bootstrap_intervals(y: np.ndarray, scores: np.ndarray, baseline_scores: np.ndarray) -> dict[str, Any]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    roc_values: list[float] = []
    pr_values: list[float] = []
    delta_values: list[float] = []
    n = len(y)
    for _ in range(BOOTSTRAP_REPEATS):
        indices = rng.integers(0, n, size=n)
        sampled_y = y[indices]
        if len(np.unique(sampled_y)) < 2:
            continue
        model_scores = scores[indices]
        baseline = baseline_scores[indices]
        roc_values.append(float(roc_auc_score(sampled_y, model_scores)))
        pr_values.append(float(average_precision_score(sampled_y, model_scores)))
        delta_values.append(float(average_precision_score(sampled_y, model_scores) - average_precision_score(sampled_y, baseline)))
    def interval(values: list[float]) -> list[float] | None:
        return [float(np.quantile(values, .025)), float(np.quantile(values, .975))] if values else None
    return {
        "method": "paired row bootstrap over pooled OOF predictions; each customer appears once",
        "repeats_requested": BOOTSTRAP_REPEATS,
        "repeats_used": len(roc_values),
        "seed": BOOTSTRAP_SEED,
        "roc_auc_95_ci": interval(roc_values),
        "pr_auc_95_ci": interval(pr_values),
        "pr_auc_delta_vs_majority_95_ci": interval(delta_values),
    }


def _write_depth_figure(rows: list[dict[str, Any]]) -> None:
    figures = ROOT / "outputs" / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(9, 5.5))
    axis.plot([row["max_depth"] for row in rows], [row["train_pr_auc"] for row in rows], marker="o", label="Train PR-AUC")
    axis.plot([row["max_depth"] for row in rows], [row["validation_mean_pr_auc"] for row in rows], marker="o", label="Validation mean-fold PR-AUC")
    axis.set_xticks(range(1, 21))
    axis.set_xlabel("Decision Tree max_depth")
    axis.set_ylabel("PR-AUC")
    axis.set_title("Day 2B feature set — train/validation temporal folds")
    axis.grid(alpha=.25)
    axis.legend(frameon=False)
    figure.tight_layout()
    figure.savefig(figures / "decision_tree_depth_curve_v2.png", dpi=160)
    plt.close(figure)


def run_repurchase_v2() -> dict[str, Any]:
    tables = ROOT / "outputs" / "tables"
    metrics_dir = ROOT / "outputs" / "metrics"
    models_dir = ROOT / "outputs" / "models"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)
    amendment = json.loads((metrics_dir / "dev_final_model.json").read_text(encoding="utf-8"))
    frozen_model = amendment
    import yaml
    prereg = yaml.safe_load((ROOT / "config" / "amendment_04_followup.yaml").read_bytes())
    locked_lr = prereg["frozen_reference_model"]
    old_model_path = ROOT / locked_lr["original_dev_model_path"] if locked_lr.get("original_dev_model_path") else ROOT / "outputs" / "models" / "day2_dev_final_model.joblib"
    old_hash = hashlib.sha256(old_model_path.read_bytes()).hexdigest()
    if old_hash != locked_lr["original_dev_model_sha256"]:
        raise ValueError("Original frozen LR artifact hash changed after amendment 04")
    if frozen_model.get("best_model") != "logistic_regression" or frozen_model.get("best_parameters") != {"C": 10.0}:
        raise ValueError("The amendment-03 frozen model metadata differs from the preregistration")

    base = pd.read_csv(tables / "day2_label_samples_primary.csv")
    if base.empty or base["customer_key"].duplicated().any():
        raise ValueError("Day 2B requires the existing one-sample-per-customer dev cohort")
    if "T" not in base.columns:
        base["T"] = base["as_of"]
    split = yaml.safe_load((ROOT / "config" / "split.yaml").read_bytes())
    order_features, source_audit = make_repurchase_features(base.to_dict("records"))
    frame = base.merge(pd.DataFrame(order_features).drop(columns=["label_returned"], errors="ignore"), on=["customer_key", "T"], how="left", validate="one_to_one", suffixes=("", "_new"))
    # Retain only one copy of labels/features from the original table; latest-order features are added once.
    for col in list(frame.columns):
        if col.endswith("_new"):
            frame = frame.drop(columns=[col])
    new_columns = [
        "last_order_product_count", "last_order_primary_product_group", "last_order_discount_rate",
        "last_order_revenue_recognized", "last_order_channel", "last_order_province", "last_order_month",
        "last_order_month_sin", "last_order_month_cos", "last_order_holiday_distance_days",
    ]
    # The merge may suffix existing T/label columns; the new feature rows are authoritative only for new columns.
    for column in new_columns:
        if column not in frame.columns:
            raise ValueError(f"registered feature is missing: {column}")
    if frame["customer_key"].duplicated().any() or frame["label_returned"].isna().any():
        raise ValueError("Day 2B feature join lost or duplicated a dev label sample")
    numeric = [column for column in NUMERIC_BASE + NUMERIC_NEW if column in frame.columns and frame[column].notna().any()]
    categorical = [column for column in CATEGORICAL_BASE + CATEGORICAL_NEW if column in frame.columns and frame[column].notna().any()]
    feature_columns = numeric + categorical
    folds = build_folds(frame)
    if len(folds) != 5:
        raise ValueError(f"Expected five amendment-03 temporal folds; found {len(folds)}")
    fold_summary = [{
        "validation_T": str(fold["validation_t"]),
        "train_n": int(len(fold["train"])),
        "validation_n": int(len(fold["validation"])),
        "train_positive": int(frame.iloc[fold["train"]]["label_returned"].sum()),
        "validation_positive": int(frame.iloc[fold["validation"]]["label_returned"].sum()),
        "customer_disjoint": True,
        "label_gap_days": 187,
    } for fold in folds]
    grids = {
        "logistic_regression": [{"C": value} for value in (.1, 1.0, 10.0)],
        "decision_tree": [{"max_depth": value} for value in range(1, 21)],
        "random_forest": [{"max_depth": depth, "min_samples_leaf": leaf} for depth in (None, 8, 16) for leaf in (1, 5)],
    }
    results: dict[str, Any] = {}
    depth_curve: list[dict[str, Any]] = []
    importance_rows: list[dict[str, Any]] = []
    y_all = frame["label_returned"].astype(int).to_numpy()
    for kind, candidates in grids.items():
        candidates_results = []
        for params in candidates:
            oof, per_fold, train_ap = _evaluate(frame, folds, kind, params, numeric, categorical)
            mean_ap = _mean([row["pr_auc"] for row in per_fold]) or -1.0
            mean_f1 = _mean([row["f1"] for row in per_fold]) or 0.0
            candidates_results.append({
                "parameters": params,
                "mean_fold_pr_auc": mean_ap,
                "mean_fold_f1": mean_f1,
                "oof_predictions": oof,
                "fold_metrics": per_fold,
                "train_mean_pr_auc": _mean(train_ap),
            })
            if kind == "decision_tree":
                depth_curve.append({
                    "max_depth": int(params["max_depth"]),
                    "train_pr_auc": float(_mean(train_ap) or 0.0),
                    "validation_mean_pr_auc": mean_ap,
                    "validation_mean_f1": mean_f1,
                })
        selected = max(candidates_results, key=lambda row: (row["mean_fold_pr_auc"], row["mean_fold_f1"], -int(row["parameters"].get("max_depth") or 999)))
        by_index = {row["index"]: row["score"] for row in selected["oof_predictions"]}
        idx = np.asarray(sorted(by_index), dtype=int)
        scores = np.asarray([by_index[index] for index in idx], dtype=float)
        selected_y = y_all[idx]
        results[kind] = {
            "selected_parameters": selected["parameters"],
            "mean_fold_pr_auc": selected["mean_fold_pr_auc"],
            "mean_fold_f1": selected["mean_fold_f1"],
            "out_of_fold_coverage": int(len(idx)),
            "out_of_fold_metrics": _metrics(selected_y, scores),
            "fold_metrics": selected["fold_metrics"],
            "candidate_log": [{
                "parameters": row["parameters"],
                "mean_fold_pr_auc": row["mean_fold_pr_auc"],
                "mean_fold_f1": row["mean_fold_f1"],
            } for row in candidates_results],
        }
    baseline_by_index: dict[int, float] = {}
    baseline_fold_metrics = []
    for fold in folds:
        train_y = y_all[fold["train"]]
        score = float(train_y.mean())
        for index in fold["validation"]:
            baseline_by_index[int(index)] = score
        fold_metric = _metrics(y_all[fold["validation"]], np.full(len(fold["validation"]), score))
        fold_metric.update({"validation_T": str(fold["validation_t"]), "majority_class": int(np.bincount(train_y).argmax())})
        baseline_fold_metrics.append(fold_metric)
    baseline_idx = np.asarray(sorted(baseline_by_index), dtype=int)
    baseline_scores = np.asarray([baseline_by_index[index] for index in baseline_idx])
    baseline_metrics = _metrics(y_all[baseline_idx], baseline_scores)
    results["majority_baseline"] = {
        "selected_parameters": {},
        "mean_fold_pr_auc": _mean([row["pr_auc"] for row in baseline_fold_metrics]),
        "out_of_fold_coverage": int(len(baseline_idx)),
        "out_of_fold_metrics": baseline_metrics,
        "fold_metrics": baseline_fold_metrics,
        "candidate_log": [{"parameters": {}, "selection_role": "reference only; no fitted estimator"}],
    }
    choice = max(
        ("logistic_regression", "decision_tree", "random_forest"),
        key=lambda name: (results[name]["mean_fold_pr_auc"], results[name]["mean_fold_f1"], -("logistic_regression", "decision_tree", "random_forest").index(name)),
    )
    selected_params = results[choice]["selected_parameters"]
    selected_by_index = {}
    selected_fold_metrics = []
    selected_train_ap = []
    for fold_index, fold in enumerate(folds):
        train = frame.iloc[fold["train"]]
        valid = frame.iloc[fold["validation"]]
        model = _pipeline(choice, selected_params, numeric, categorical, 42 + fold_index)
        model.fit(train[feature_columns], y_all[fold["train"]])
        scores = _scores(model, valid, feature_columns)
        selected_fold_metrics.append(_metrics(y_all[fold["validation"]], scores))
        selected_train_ap.append(float(average_precision_score(y_all[fold["train"]], _scores(model, train, feature_columns))))
        for index, score in zip(fold["validation"], scores):
            selected_by_index[int(index)] = float(score)
    oof_idx = np.asarray(sorted(selected_by_index), dtype=int)
    oof_scores = np.asarray([selected_by_index[index] for index in oof_idx])
    oof_y = y_all[oof_idx]
    baseline_aligned = np.asarray([baseline_by_index[index] for index in oof_idx])
    ci = _bootstrap_intervals(oof_y, oof_scores, baseline_aligned)
    roc_lower = ci["roc_auc_95_ci"][0] if ci["roc_auc_95_ci"] else None
    delta_lower = ci["pr_auc_delta_vs_majority_95_ci"][0] if ci["pr_auc_delta_vs_majority_95_ci"] else None
    signal = bool(roc_lower is not None and roc_lower > .55 and delta_lower is not None and delta_lower > 0)

    # Held-out-fold permutation importance for each of the three registered model families.
    for kind in ("logistic_regression", "decision_tree", "random_forest"):
        for fold_index, fold in enumerate(folds):
            train = frame.iloc[fold["train"]]
            valid = frame.iloc[fold["validation"]]
            model = _pipeline(kind, results[kind]["selected_parameters"], numeric, categorical, 42 + fold_index)
            model.fit(train[feature_columns], y_all[fold["train"]])
            importance = permutation_importance(
                model, valid[feature_columns], y_all[fold["validation"]],
                scoring="average_precision", n_repeats=5, random_state=BOOTSTRAP_SEED + fold_index, n_jobs=1,
            )
            for feature, drop in zip(feature_columns, importance.importances_mean):
                importance_rows.append({
                    "model": kind,
                    "fold": fold_index,
                    "feature": feature,
                    "permutation_ap_drop": float(drop),
                    "repeats": 5,
                })
    importance_frame = pd.DataFrame(importance_rows)
    importance_summary = importance_frame.groupby(["model", "feature"], as_index=False)["permutation_ap_drop"].mean()
    importance_summary.to_csv(tables / "repurchase_feature_importance_v2.csv", index=False, encoding="utf-8-sig")
    depth_curve.sort(key=lambda row: row["max_depth"])
    pd.DataFrame(depth_curve).to_csv(tables / "decision_tree_depth_curve_v2.csv", index=False, encoding="utf-8-sig")
    _write_depth_figure(depth_curve)

    selected_pipeline = _pipeline(choice, selected_params, numeric, categorical, 42)
    selected_pipeline.fit(frame[feature_columns], y_all)
    model_path = models_dir / "repurchase_features_v2.joblib"
    joblib.dump(selected_pipeline, model_path)
    model_hash = hashlib.sha256(model_path.read_bytes()).hexdigest()
    segment_assignments = pd.read_csv(tables / "segments_v2.csv")[["customer_key", "rule_segment_v2"]]
    oof_frame = frame.iloc[oof_idx][["customer_key", "label_returned"]].copy()
    oof_frame["score"] = oof_scores
    oof_frame = oof_frame.merge(segment_assignments, on="customer_key", how="left", validate="one_to_one")
    per_segment_metrics = {}
    for segment_name, group in oof_frame.groupby("rule_segment_v2", dropna=False):
        per_segment_metrics[str(segment_name)] = {
            **_metrics(group["label_returned"].astype(int).to_numpy(), group["score"].astype(float).to_numpy()),
            "low_support_warning": int(group["label_returned"].sum()) < 20,
        }
    result = {
        "amendment_04_sha256": hashlib.sha256((ROOT / "config" / "amendment_04_followup.yaml").read_bytes()).hexdigest(),
        "frozen_reference_model": {
            "name": "amendment-03 logistic_regression",
            "parameters": {"C": 10.0},
            "sha256": old_hash,
            "unchanged": True,
            "mean_fold_pr_auc": frozen_model["models"]["logistic_regression"]["mean_fold_pr_auc"],
            "pooled_oof_pr_auc": frozen_model["models"]["logistic_regression"]["out_of_fold_metrics"]["pr_auc"],
            "pooled_decision_tree_pr_auc": frozen_model["models"]["decision_tree"]["out_of_fold_metrics"]["pr_auc"],
        },
        "repurchase_features_v2": {
            "experiment_runs_used": 1,
            "sample_count": int(len(frame)),
            "positive_count": int(y_all.sum()),
            "positive_rate": float(y_all.mean()),
            "folds": fold_summary,
            "customer_overlap_across_train_validation": False,
            "feature_columns": feature_columns,
            "numeric_features": numeric,
            "categorical_features": categorical,
            "source_audit": source_audit,
            "models": results,
            "selected_model": choice,
            "selected_parameters": selected_params,
            "selection_rule": "highest mean PR-AUC across the five preregistered temporal folds; tie-break mean F1 then simpler model",
            "selected_oof_metrics": _metrics(oof_y, oof_scores),
            "per_rule_segment_oof_metrics": per_segment_metrics,
            "selected_model_bootstrap_ci": ci,
            "signal_rule": "lower 95% ROC-AUC bound > 0.55 AND lower 95% paired OOF PR-AUC gain over majority baseline > 0",
            "signal_supported": signal,
            "conclusion": "signal met preregistered threshold" if signal else "không đủ bằng chứng để dự đoán mua lại từ dữ liệu hiện có",
            "feature_trial_count": 1,
            "candidate_evaluations_used": 30,
            "permutation_importance_repeats_per_fold": 5,
            "final_model_path": "outputs/models/repurchase_features_v2.joblib",
            "final_model_sha256": model_hash,
            "test_labels_loaded": False,
            "test_behavior_loaded": False,
        },
        "cancel_refund": {"registered": True, "status": "gate_pending", "model_attempts": 0},
        "experiment_log": [
            {"task": "repurchase_v2", "registered_runs": 1, "runs_used": 1, "candidate_evaluations_used": 30, "post_result_retries": 0},
        ],
        "test_labels_loaded": False,
        "test_behavior_loaded": False,
    }
    (metrics_dir / "dev_final_models_v2.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Day 2B repurchase v2: model={choice}, ROC-AUC={result['repurchase_features_v2']['selected_oof_metrics']['roc_auc']:.4f}, PR-AUC={result['repurchase_features_v2']['selected_oof_metrics']['pr_auc']:.4f}, signal={signal}.")
    return result


if __name__ == "__main__":
    run_repurchase_v2()
