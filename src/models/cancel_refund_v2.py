"""Optional order cancellation/refund model; one preregistered fold-support gate."""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import average_precision_score

from features.day2b_data import cancel_validation_windows, load_cancel_refund_orders
from models.classify_v2 import _metrics, _pipeline, _scores

ROOT = Path(__file__).resolve().parents[2]
NUMERIC = ["item_count", "order_value_at_creation", "order_month", "nearest_holiday_distance_days"]
CATEGORICAL = ["channel", "province", "customer_new_or_returning"]


def run_cancel_refund_v2() -> dict[str, Any]:
    rows, audit = load_cancel_refund_orders()
    import yaml
    config = yaml.safe_load((ROOT / "config" / "split.yaml").read_bytes())
    start = date.fromisoformat("2024-04-01")
    test_start = date.fromisoformat(str(config["test_start"]))
    windows = cancel_validation_windows(start, test_start)
    fold_records = []
    fold_indices = []
    for fold_id, (window_start, window_end) in enumerate(windows):
        train = [i for i, row in enumerate(rows) if row["local_date"] < window_start]
        valid = [i for i, row in enumerate(rows) if window_start <= row["local_date"] < window_end]
        positive = sum(rows[i]["label_cancel_or_return"] for i in valid)
        train_positive = sum(rows[i]["label_cancel_or_return"] for i in train)
        fold_records.append({
            "fold": fold_id,
            "validation_start": window_start.isoformat(),
            "validation_end_exclusive": window_end.isoformat(),
            "train_count": len(train),
            "train_positive_count": train_positive,
            "validation_count": len(valid),
            "validation_positive_count": positive,
        })
        fold_indices.append({"train": train, "validation": valid})
    gate_pass = len(fold_records) == 5 and all(row["validation_positive_count"] >= 20 for row in fold_records)
    train_support_pass = all(row["train_count"] > 0 and 0 < row["train_positive_count"] < row["train_count"] for row in fold_records)
    gate_pass = gate_pass and train_support_pass
    metric: dict[str, Any] = {
        "amendment_04_sha256": hashlib.sha256((ROOT / "config" / "amendment_04_followup.yaml").read_bytes()).hexdigest(),
        "data_audit": audit,
        "label": "status 5/6=1 vs non-gift status 3=0; statuses 0/1/4 excluded",
        "fold_plan": "180-day train-only warm-up, then five contiguous equal-width time windows; train on earlier orders only",
        "folds": fold_records,
        "gate_each_validation_fold_positive_at_least_20": gate_pass,
        "experiment_runs_used": 0,
        "model_attempts": 0,
        "test_labels_loaded": False,
        "test_behavior_loaded": False,
    }
    metrics_path = ROOT / "outputs" / "metrics" / "day2b_cancel_model.json"
    if not gate_pass:
        metric.update({
            "status": "skipped_preregistered_positive_support_gate",
            "reason": "At least one temporal validation fold has fewer than 20 positive status-5/6 orders or lacks both classes in its training data.",
            "candidate_evaluations_used": 0,
        })
        metrics_path.write_text(json.dumps(metric, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        _update_final_registry(metric)
        return metric

    frame = pd.DataFrame(rows)
    y = frame["label_cancel_or_return"].astype(int).to_numpy()
    numeric = [column for column in NUMERIC if frame[column].notna().any()]
    categorical = [column for column in CATEGORICAL if frame[column].notna().any()]
    columns = numeric + categorical
    grids = {
        "logistic_regression": [{"C": c} for c in (.1, 1.0, 10.0)],
        "decision_tree": [{"max_depth": depth} for depth in range(1, 21)],
        "random_forest": [{"max_depth": depth, "min_samples_leaf": leaf} for depth in (None, 8, 16) for leaf in (1, 5)],
    }
    results = {}
    depth_rows = []
    permutation_rows = []
    for kind, candidates in grids.items():
        scored_candidates = []
        for params in candidates:
            oof_y, oof_scores, fold_metrics, train_aps = [], [], [], []
            for fold_id, fold in enumerate(fold_indices):
                train = frame.iloc[fold["train"]]
                valid = frame.iloc[fold["validation"]]
                model = _pipeline(kind, params, numeric, categorical, 42 + fold_id)
                model.fit(train[columns], y[fold["train"]])
                score = _scores(model, valid, columns)
                fold_metrics.append(_metrics(y[fold["validation"]], score))
                train_scores = _scores(model, train, columns)
                train_aps.append(float(average_precision_score(y[fold["train"]], train_scores)))
                oof_y.extend(y[fold["validation"]].tolist())
                oof_scores.extend(score.tolist())
            mean_ap = float(np.mean([item["pr_auc"] for item in fold_metrics]))
            mean_f1 = float(np.mean([item["f1"] for item in fold_metrics]))
            scored_candidates.append({"parameters": params, "mean_pr_auc": mean_ap, "mean_f1": mean_f1, "oof_y": oof_y, "oof_scores": oof_scores, "fold_metrics": fold_metrics})
            if kind == "decision_tree":
                depth_rows.append({"max_depth": params["max_depth"], "train_pr_auc": float(np.mean(train_aps)), "validation_mean_pr_auc": mean_ap})
        selected = max(scored_candidates, key=lambda item: (item["mean_pr_auc"], item["mean_f1"], -int(item["parameters"].get("max_depth") or 999)))
        results[kind] = {
            "selected_parameters": selected["parameters"],
            "mean_fold_pr_auc": selected["mean_pr_auc"],
            "mean_fold_f1": selected["mean_f1"],
            "out_of_fold_metrics": _metrics(np.asarray(selected["oof_y"]), np.asarray(selected["oof_scores"])),
            "fold_metrics": selected["fold_metrics"],
            "candidate_log": [{"parameters": row["parameters"], "mean_fold_pr_auc": row["mean_pr_auc"], "mean_fold_f1": row["mean_f1"]} for row in scored_candidates],
        }
    baseline_oof_y = []
    baseline_oof_scores = []
    baseline_folds = []
    for fold in fold_indices:
        train_y = y[fold["train"]]
        score = float(train_y.mean())
        valid_y = y[fold["validation"]]
        baseline_oof_y.extend(valid_y.tolist())
        baseline_oof_scores.extend([score] * len(valid_y))
        baseline_folds.append(_metrics(valid_y, np.full(len(valid_y), score)))
    results["majority_baseline"] = {
        "selected_parameters": {},
        "mean_fold_pr_auc": float(np.mean([row["pr_auc"] for row in baseline_folds])),
        "out_of_fold_metrics": _metrics(np.asarray(baseline_oof_y), np.asarray(baseline_oof_scores)),
        "fold_metrics": baseline_folds,
        "candidate_log": [{"parameters": {}, "selection_role": "reference only; no fitted estimator"}],
    }
    selected_kind = max(("logistic_regression", "decision_tree", "random_forest"), key=lambda kind: (results[kind]["mean_fold_pr_auc"], results[kind]["mean_fold_f1"]))
    selected_params = results[selected_kind]["selected_parameters"]
    for fold_id, fold in enumerate(fold_indices):
        train = frame.iloc[fold["train"]]
        valid = frame.iloc[fold["validation"]]
        model = _pipeline(selected_kind, selected_params, numeric, categorical, 42 + fold_id)
        model.fit(train[columns], y[fold["train"]])
        importance = permutation_importance(model, valid[columns], y[fold["validation"]], scoring="average_precision", n_repeats=5, random_state=20261025 + fold_id, n_jobs=1)
        permutation_rows.extend({"fold": fold_id, "feature": feature, "ap_drop": float(value)} for feature, value in zip(columns, importance.importances_mean))
    tables = ROOT / "outputs" / "tables"
    pd.DataFrame(depth_rows).sort_values("max_depth").to_csv(tables / "cancel_tree_depth_curve_v2.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(permutation_rows).to_csv(tables / "cancel_feature_importance_v2.csv", index=False, encoding="utf-8-sig")
    figure, axis = plt.subplots(figsize=(9, 5.5))
    depth_frame = pd.DataFrame(depth_rows).sort_values("max_depth")
    axis.plot(depth_frame["max_depth"], depth_frame["train_pr_auc"], marker="o", label="Train PR-AUC")
    axis.plot(depth_frame["max_depth"], depth_frame["validation_mean_pr_auc"], marker="o", label="Validation mean-fold PR-AUC")
    axis.set_xticks(range(1, 21))
    axis.set_xlabel("Decision Tree max_depth")
    axis.set_ylabel("PR-AUC")
    axis.set_title("Cancel/refund — train/validation temporal folds")
    axis.grid(alpha=.25)
    axis.legend(frameon=False)
    figure.tight_layout()
    figure.savefig(ROOT / "outputs" / "figures" / "cancel_tree_depth_curve_v2.png", dpi=160)
    plt.close(figure)
    model = _pipeline(selected_kind, selected_params, numeric, categorical, 42)
    model.fit(frame[columns], y)
    model_path = ROOT / "outputs" / "models" / "cancel_refund_dev_v2.joblib"
    joblib.dump(model, model_path)
    metric.update({
        "status": "modeled_once",
        "experiment_runs_used": 1,
        "model_attempts": 1,
        "candidate_evaluations_used": 30,
        "features_used": columns,
        "features_forbidden": ["status_history", "updated_at", "cash", "cod", "prepaid", "transfer_money", "money_to_collect", "all payment fields", "direct identifiers", "free text", "post-creation fields"],
        "models": results,
        "selected_model": selected_kind,
        "selected_parameters": selected_params,
        "selected_final_model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
        "selected_final_model_path": "outputs/models/cancel_refund_dev_v2.joblib",
        "feature_fit_scope": "training fold only for validation; all eligible development orders for frozen final artifact",
    })
    metrics_path.write_text(json.dumps(metric, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _update_final_registry(metric)
    return metric


def _update_final_registry(cancel_metric: dict[str, Any]) -> None:
    path = ROOT / "outputs" / "metrics" / "dev_final_models_v2.json"
    registry = json.loads(path.read_text(encoding="utf-8"))
    registry["cancel_refund"] = {
        "registered": True,
        "status": cancel_metric["status"],
        "model_attempts": cancel_metric["model_attempts"],
        "candidate_evaluations_used": cancel_metric.get("candidate_evaluations_used", 0),
        "selected_model": cancel_metric.get("selected_model"),
        "selected_parameters": cancel_metric.get("selected_parameters"),
        "final_model_path": cancel_metric.get("selected_final_model_path"),
        "final_model_sha256": cancel_metric.get("selected_final_model_sha256"),
        "features_used": cancel_metric.get("features_used"),
        "reason": cancel_metric.get("reason"),
    }
    registry["experiment_log"].append({
        "task": "cancel_refund_optional",
        "registered_runs": 1,
        "runs_used": cancel_metric["experiment_runs_used"],
        "candidate_evaluations_used": cancel_metric.get("candidate_evaluations_used", 0),
        "post_result_retries": 0,
    })
    path.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
