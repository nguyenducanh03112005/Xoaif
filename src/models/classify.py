"""Leakage-aware temporal validation and development-only classifiers."""

from __future__ import annotations
from collections import defaultdict
from datetime import date, timedelta
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
    average_precision_score, confusion_matrix, f1_score, precision_score,
    recall_score, roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[2]
N_DAYS = 180
L_DAYS = 7
ID_COLUMNS = {"customer_key", "as_of", "first_purchase_date", "last_purchase_date", "label_returned"}
NUMERIC_COLUMNS = [
    "recency_days", "frequency", "monetary", "average_order_value", "max_order_value",
    "total_quantity", "distinct_products", "mean_days_between_orders", "first_order_month",
    "first_order_month_sin", "first_order_month_cos", "nearest_holiday_distance_days",
    "adjustment_positive_rate", "adjustment_negative_rate", "no_history_after_sensitivity",
]
CATEGORICAL_COLUMNS = ["province"]


def build_folds(frame: pd.DataFrame) -> list[dict[str, np.ndarray]]:
    y = frame["label_returned"].astype(int).to_numpy()
    t_dates = pd.to_datetime(frame["as_of"]).dt.date.to_numpy()
    customer_keys = frame["customer_key"].to_numpy()
    folds = []
    for validation_t in sorted(set(t_dates)):
        valid_idx = np.flatnonzero(t_dates == validation_t)
        train_idx = np.array([
            index for index, train_t in enumerate(t_dates)
            if train_t + timedelta(days=N_DAYS + L_DAYS) < validation_t
        ], dtype=int)
        if len(train_idx) < 30 or len(set(y[train_idx])) < 2 or not len(valid_idx):
            continue
        if set(customer_keys[train_idx]) & set(customer_keys[valid_idx]):
            raise ValueError("customer overlap across temporal train/validation split")
        folds.append({"train": train_idx, "validation": valid_idx, "validation_t": validation_t})
    return folds


def _preprocessor() -> ColumnTransformer:
    numeric = Pipeline([
        ("impute", SimpleImputer(strategy="median", add_indicator=True)),
        ("scale", StandardScaler()),
    ])
    categorical = Pipeline([
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("encode", OneHotEncoder(handle_unknown="ignore")),
    ])
    return ColumnTransformer([
        ("numeric", numeric, NUMERIC_COLUMNS),
        ("categorical", categorical, CATEGORICAL_COLUMNS),
    ], remainder="drop")


def _estimator(kind: str, params: dict[str, Any], seed: int = 42):
    if kind == "logistic_regression":
        return LogisticRegression(C=float(params["C"]), class_weight="balanced", max_iter=2000, solver="lbfgs", random_state=seed)
    if kind == "decision_tree":
        return DecisionTreeClassifier(max_depth=params["max_depth"], min_samples_leaf=5, class_weight="balanced", random_state=seed)
    if kind == "random_forest":
        return RandomForestClassifier(
            n_estimators=150, max_depth=params["max_depth"], min_samples_leaf=int(params["min_samples_leaf"]),
            max_features="sqrt", class_weight="balanced_subsample", n_jobs=-1, random_state=seed,
        )
    raise ValueError(f"unknown estimator kind: {kind}")


def _pipeline(kind: str, params: dict[str, Any], seed: int = 42) -> Pipeline:
    return Pipeline([("preprocess", _preprocessor()), ("model", _estimator(kind, params, seed))])


def _scores(model: Pipeline, frame: pd.DataFrame) -> np.ndarray:
    probabilities = model.predict_proba(frame[NUMERIC_COLUMNS + CATEGORICAL_COLUMNS])
    classes = list(model.named_steps["model"].classes_)
    return probabilities[:, classes.index(1)] if 1 in classes else np.zeros(len(frame))


def _metric_bundle(y_true: np.ndarray, score: np.ndarray, threshold: float = 0.5) -> dict[str, Any]:
    pred = (score >= threshold).astype(int)
    cm = confusion_matrix(y_true, pred, labels=[0, 1]).tolist()
    return {
        "precision": float(precision_score(y_true, pred, zero_division=0)),
        "recall": float(recall_score(y_true, pred, zero_division=0)),
        "f1": float(f1_score(y_true, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, score)) if len(set(y_true)) == 2 else None,
        "pr_auc": float(average_precision_score(y_true, score)) if len(y_true) else None,
        "confusion_matrix_tn_fp_fn_tp": cm,
        "positive_count": int(np.sum(y_true)),
        "sample_count": int(len(y_true)),
    }


def _evaluate_candidate(frame: pd.DataFrame, folds: list[dict[str, np.ndarray]], kind: str, params: dict[str, Any]) -> tuple[list[dict], list[dict]]:
    y = frame["label_returned"].astype(int).to_numpy()
    out_of_fold = []
    fold_metrics = []
    for fold_idx, fold in enumerate(folds):
        train = frame.iloc[fold["train"]]
        valid = frame.iloc[fold["validation"]]
        model = _pipeline(kind, params, seed=42 + fold_idx)
        model.fit(train[NUMERIC_COLUMNS + CATEGORICAL_COLUMNS], y[fold["train"]])
        score = _scores(model, valid)
        metric = _metric_bundle(y[fold["validation"]], score)
        metric.update({"validation_T": fold["validation_t"].isoformat(), "train_n": len(train), "validation_n": len(valid)})
        fold_metrics.append(metric)
        for index, probability in zip(fold["validation"], score):
            out_of_fold.append({"index": int(index), "score": float(probability), "fold": fold_idx})
    return out_of_fold, fold_metrics


def _mean_metric(fold_metrics: list[dict], name: str) -> float | None:
    values = [row[name] for row in fold_metrics if row.get(name) is not None]
    return float(np.mean(values)) if values else None


def _segment_name(row: pd.Series, monetary_threshold: float, order_threshold: float) -> str:
    if int(row["frequency"]) <= 1:
        return "Khách mua một lần"
    if int(row["frequency"]) <= 2 and (float(row["monetary"]) >= monetary_threshold or float(row["max_order_value"]) >= order_threshold):
        return "Giá trị lớn, tần suất thấp"
    return "Khách mua lặp lại"


def _bootstrap_ci(y: np.ndarray, scores: np.ndarray, seed: int = 2025, repeats: int = 1000) -> dict[str, list[float] | None]:
    rng = np.random.default_rng(seed)
    pr_values = []
    f1_values = []
    for _ in range(repeats):
        idx = rng.integers(0, len(y), len(y))
        if len(set(y[idx])) < 2:
            continue
        pr_values.append(average_precision_score(y[idx], scores[idx]))
        f1_values.append(f1_score(y[idx], (scores[idx] >= .5).astype(int), zero_division=0))
    def interval(values):
        return [float(np.quantile(values, .025)), float(np.quantile(values, .975))] if values else None
    return {"pr_auc_95_percentile_ci": interval(pr_values), "f1_95_percentile_ci": interval(f1_values), "bootstrap_repeats_requested": repeats, "bootstrap_repeats_used": len(pr_values)}


def run_classification() -> dict[str, Any]:
    tables = ROOT / "outputs" / "tables"
    metrics_dir = ROOT / "outputs" / "metrics"
    figures = ROOT / "outputs" / "figures"
    models_dir = ROOT / "outputs" / "models"
    for path in (metrics_dir, figures, models_dir):
        path.mkdir(parents=True, exist_ok=True)
    variants = {name: pd.read_csv(tables / f"day2_label_samples_{name}.csv") for name in ("primary", "A", "B")}
    primary = variants["primary"]
    if primary.empty or primary["customer_key"].duplicated().any():
        raise ValueError("label input is empty or repeats a customer")
    if any(not set(frame["customer_key"]) == set(primary["customer_key"]) for frame in variants.values()):
        raise ValueError("sensitivity label cohorts differ from the primary customer set")
    folds = build_folds(primary)
    if not folds:
        raise ValueError("pre-registered temporal split has no eligible validation folds")
    fold_summary = [{
        "validation_T": fold["validation_t"].isoformat(),
        "train_n": int(len(fold["train"])),
        "validation_n": int(len(fold["validation"])),
        "train_positive": int(primary.iloc[fold["train"]]["label_returned"].sum()),
        "validation_positive": int(primary.iloc[fold["validation"]]["label_returned"].sum()),
        "customer_disjoint": True,
        "label_gap_days": N_DAYS + L_DAYS,
    } for fold in folds]

    candidate_specs: dict[str, list[dict[str, Any]]] = {
        "logistic_regression": [{"C": c} for c in (.1, 1.0, 10.0)],
        "decision_tree": [{"max_depth": depth} for depth in range(1, 21)],
        "random_forest": [
            {"max_depth": depth, "min_samples_leaf": leaf}
            for depth in (None, 8, 16) for leaf in (1, 5)
        ],
    }
    selected: dict[str, dict[str, Any]] = {}
    results: dict[str, Any] = {}
    tree_curve = []
    for kind, candidates in candidate_specs.items():
        candidate_scores = []
        for params in candidates:
            oof, fold_metrics = _evaluate_candidate(primary, folds, kind, params)
            mean_pr = _mean_metric(fold_metrics, "pr_auc")
            mean_f1 = _mean_metric(fold_metrics, "f1")
            candidate_scores.append((mean_pr if mean_pr is not None else -1.0, mean_f1 or 0.0, params, oof, fold_metrics))
            if kind == "decision_tree":
                train_pr = []
                for fold_idx, fold in enumerate(folds):
                    train = primary.iloc[fold["train"]]
                    valid = primary.iloc[fold["validation"]]
                    y = primary["label_returned"].astype(int).to_numpy()
                    model = _pipeline(kind, params, seed=42 + fold_idx)
                    model.fit(train[NUMERIC_COLUMNS + CATEGORICAL_COLUMNS], y[fold["train"]])
                    train_pr.append(float(average_precision_score(y[fold["train"]], _scores(model, train))))
                tree_curve.append({"max_depth": params["max_depth"], "train_pr_auc": float(np.mean(train_pr)), "validation_pr_auc": mean_pr, "validation_f1": mean_f1})
        best = max(candidate_scores, key=lambda row: (row[0], row[1], -int(row[2].get("max_depth") or 999)))
        selected[kind] = best[2]
        out_by_index = {row["index"]: row["score"] for row in best[3]}
        idx = np.asarray(sorted(out_by_index), dtype=int)
        y_oof = primary.iloc[idx]["label_returned"].astype(int).to_numpy()
        scores = np.asarray([out_by_index[i] for i in idx], dtype=float)
        pooled = _metric_bundle(y_oof, scores)
        results[kind] = {
            "selected_parameters": best[2],
            "mean_fold_pr_auc": best[0],
            "mean_fold_f1": best[1],
            "out_of_fold_metrics": pooled,
            "fold_metrics": best[4],
            "out_of_fold_coverage": int(len(idx)),
        }

    # Majority-class baseline scored on exactly the same validation rows.
    baseline_oof: dict[int, float] = {}
    baseline_folds = []
    y_all = primary["label_returned"].astype(int).to_numpy()
    for fold in folds:
        train_y = y_all[fold["train"]]
        majority = int(np.bincount(train_y).argmax())
        probability = float(np.mean(train_y))
        for idx in fold["validation"]:
            baseline_oof[int(idx)] = probability
        metric = _metric_bundle(y_all[fold["validation"]], np.full(len(fold["validation"]), probability))
        metric.update({"validation_T": fold["validation_t"].isoformat(), "majority_class": majority})
        baseline_folds.append(metric)
    baseline_idx = np.asarray(sorted(baseline_oof), dtype=int)
    baseline_scores = np.asarray([baseline_oof[i] for i in baseline_idx])
    results["majority_baseline"] = {
        "selected_parameters": {},
        "mean_fold_pr_auc": _mean_metric(baseline_folds, "pr_auc"),
        "mean_fold_f1": _mean_metric(baseline_folds, "f1"),
        "out_of_fold_metrics": _metric_bundle(y_all[baseline_idx], baseline_scores),
        "fold_metrics": baseline_folds,
        "out_of_fold_coverage": int(len(baseline_idx)),
    }

    best_kind = max(selected, key=lambda kind: results[kind]["mean_fold_pr_auc"] or -1)
    best_params = selected[best_kind]
    oof, best_fold_metrics = _evaluate_candidate(primary, folds, best_kind, best_params)
    best_scores_by_index = {row["index"]: row["score"] for row in oof}
    oof_idx = np.asarray(sorted(best_scores_by_index), dtype=int)
    oof_y = primary.iloc[oof_idx]["label_returned"].astype(int).to_numpy()
    oof_scores = np.asarray([best_scores_by_index[i] for i in oof_idx])
    overall_oof = _metric_bundle(oof_y, oof_scores)

    sensitivity = {}
    for variant in ("A", "B"):
        frame = variants[variant]
        variant_oof, variant_folds = _evaluate_candidate(frame, folds, best_kind, best_params)
        scores_by_index = {row["index"]: row["score"] for row in variant_oof}
        same_idx = np.asarray(sorted(scores_by_index), dtype=int)
        variant_y = frame.iloc[same_idx]["label_returned"].astype(int).to_numpy()
        variant_scores = np.asarray([scores_by_index[i] for i in same_idx])
        bundle = _metric_bundle(variant_y, variant_scores)
        sensitivity[variant] = {
            "selected_model": best_kind,
            "parameters_held_at_primary_selection": best_params,
            "out_of_fold_metrics": bundle,
            "delta_vs_primary": {
                metric: (bundle[metric] - overall_oof[metric]) if bundle.get(metric) is not None and overall_oof.get(metric) is not None else None
                for metric in ("precision", "recall", "f1", "roc_auc", "pr_auc")
            },
            "fold_metrics": variant_folds,
        }

    # Report metrics by transparent rule-based segments, with thresholds derived from each train fold.
    segment_rows: dict[str, list[tuple[int, float]]] = defaultdict(list)
    for fold in folds:
        train = primary.iloc[fold["train"]]
        valid = primary.iloc[fold["validation"]].copy()
        money_p99 = float(train["monetary"].quantile(.99))
        order_p99 = float(train["max_order_value"].quantile(.99))
        valid["rule_segment"] = valid.apply(lambda row: _segment_name(row, money_p99, order_p99), axis=1)
        for idx, segment, label, score in zip(fold["validation"], valid["rule_segment"], valid["label_returned"], [best_scores_by_index[i] for i in fold["validation"]]):
            segment_rows[segment].append((int(label), float(score)))
    segment_metrics = {}
    for segment, items in segment_rows.items():
        y = np.asarray([row[0] for row in items])
        score = np.asarray([row[1] for row in items])
        segment_metrics[segment] = _metric_bundle(y, score)

    # Permutation importance runs on held-out folds only. It measures validation AP change.
    permutation: dict[str, list[float]] = defaultdict(list)
    model_importance: dict[str, list[float]] = defaultdict(list)
    for fold_idx, fold in enumerate(folds):
        train = primary.iloc[fold["train"]]
        valid = primary.iloc[fold["validation"]]
        model = _pipeline(best_kind, best_params, seed=42 + fold_idx)
        model.fit(train[NUMERIC_COLUMNS + CATEGORICAL_COLUMNS], y_all[fold["train"]])
        raw_importance = permutation_importance(
            model, valid[NUMERIC_COLUMNS + CATEGORICAL_COLUMNS], y_all[fold["validation"]],
            scoring="average_precision", n_repeats=5, random_state=2025 + fold_idx, n_jobs=1,
        )
        for name, mean_value in zip(NUMERIC_COLUMNS + CATEGORICAL_COLUMNS, raw_importance.importances_mean):
            permutation[name].append(float(mean_value))
        estimator = model.named_steps["model"]
        names = model.named_steps["preprocess"].get_feature_names_out()
        if hasattr(estimator, "feature_importances_"):
            values = estimator.feature_importances_
        elif hasattr(estimator, "coef_"):
            values = np.mean(np.abs(estimator.coef_), axis=0)
        else:
            values = np.zeros(len(names))
        for feature in NUMERIC_COLUMNS:
            grouped_value = sum(
                float(value) for name, value in zip(names, values)
                if name == f"numeric__{feature}" or name == f"numeric__missingindicator_{feature}"
            )
            model_importance[feature].append(grouped_value)
        model_importance["province"].append(sum(
            float(value) for name, value in zip(names, values) if name.startswith("categorical__province_")
        ))

    model_hash_input = primary[NUMERIC_COLUMNS + CATEGORICAL_COLUMNS].copy()
    final_pipeline = _pipeline(best_kind, best_params, seed=42)
    final_pipeline.fit(model_hash_input, y_all)
    model_path = models_dir / "day2_dev_final_model.joblib"
    joblib.dump(final_pipeline, model_path)
    model_sha = hashlib.sha256(model_path.read_bytes()).hexdigest()

    importance_rows = [
        {
            "feature": feature,
            "model_importance_mean": float(np.mean(model_importance.get(feature, [0.0]))),
            "permutation_ap_drop_mean": float(np.mean(permutation.get(feature, [0.0]))),
        }
        for feature in NUMERIC_COLUMNS + CATEGORICAL_COLUMNS
    ]
    importance_rows.sort(key=lambda row: row["permutation_ap_drop_mean"], reverse=True)
    (tables / "classifier_feature_importance.json").write_text(json.dumps(importance_rows, indent=2) + "\n", encoding="utf-8")
    tree_curve.sort(key=lambda row: row["max_depth"])
    deepest_gap = max(tree_curve, key=lambda row: row["train_pr_auc"] - (row["validation_pr_auc"] or 0.0)) if tree_curve else None
    chosen_tree_depth = selected["decision_tree"]["max_depth"]
    chosen_tree_point = next((row for row in tree_curve if row["max_depth"] == chosen_tree_depth), None)
    tree_diagnostics = {
        "selected_depth": chosen_tree_depth,
        "selected_train_pr_auc": chosen_tree_point["train_pr_auc"] if chosen_tree_point else None,
        "selected_validation_pr_auc": chosen_tree_point["validation_pr_auc"] if chosen_tree_point else None,
        "selected_train_validation_gap": (chosen_tree_point["train_pr_auc"] - chosen_tree_point["validation_pr_auc"]) if chosen_tree_point and chosen_tree_point["validation_pr_auc"] is not None else None,
        "largest_train_validation_gap_depth": deepest_gap["max_depth"] if deepest_gap else None,
        "largest_train_validation_gap": (deepest_gap["train_pr_auc"] - (deepest_gap["validation_pr_auc"] or 0.0)) if deepest_gap else None,
        "reading_guide": "A widening train-validation gap at high max_depth indicates overfitting; low train and validation curves together indicate underfitting.",
    }
    pd.DataFrame(tree_curve).to_csv(tables / "decision_tree_depth_curve.csv", index=False, encoding="utf-8-sig")
    fig, ax = plt.subplots(figsize=(9, 5.5))
    depths = [row["max_depth"] for row in tree_curve]
    ax.plot(depths, [row["train_pr_auc"] for row in tree_curve], marker="o", label="Train PR-AUC")
    ax.plot(depths, [row["validation_pr_auc"] for row in tree_curve], marker="o", label="Validation PR-AUC")
    ax.set_xlabel("Decision Tree max_depth")
    ax.set_ylabel("PR-AUC")
    ax.set_title("Decision Tree — train/validation theo temporal folds")
    ax.set_xticks(range(1, 21))
    ax.grid(alpha=.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(figures / "decision_tree_depth_curve.png", dpi=160)
    plt.close(fig)

    label_metrics = json.loads((metrics_dir / "day2_label_audit.json").read_text(encoding="utf-8"))
    if label_metrics["label_threshold_decision"]["under_100_positive_or_under_5_percent"]:
        results["selected_model_bootstrap_ci"] = _bootstrap_ci(oof_y, oof_scores)
        results["reliability_note"] = "Fewer than 100 positives or below 5%; temporal CV and bootstrap intervals; no strong claim."
    else:
        results["selected_model_bootstrap_ci"] = None
        results["reliability_note"] = "Positive support meets preregistered minimum; development-only temporal CV, still limited by current-status labels and short history."
    metrics = {
        "sample_count": int(len(primary)),
        "positive_count": int(y_all.sum()),
        "positive_rate": float(y_all.mean()),
        "temporal_folds": fold_summary,
        "customer_overlap_across_train_validation": False,
        "all_preprocessing_fit_inside_train_folds": True,
        "models": results,
        "best_model": best_kind,
        "best_parameters": best_params,
        "best_model_oof_metrics": overall_oof,
        "per_rule_segment_metrics": segment_metrics,
        "sensitivity_A_B": sensitivity,
        "tree_depth_curve": tree_curve,
        "tree_depth_diagnostics": tree_diagnostics,
        "top_features_by_permutation_importance": importance_rows[:20],
        "final_model_path": "outputs/models/day2_dev_final_model.joblib",
        "final_model_sha256": model_sha,
        "final_model_fit_scope": "all labeled development examples only; no reserved/test rows",
        "test_labels_loaded": False,
        "test_behavior_loaded": False,
        "reliability_note": results["reliability_note"],
    }
    (metrics_dir / "dev_final_model.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Classification: samples={len(primary)}, positives={int(y_all.sum())}, folds={len(folds)}, best={best_kind}, PR-AUC={overall_oof['pr_auc']:.3f}.")
    return metrics


if __name__ == "__main__":
    run_classification()
