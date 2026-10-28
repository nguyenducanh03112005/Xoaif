"""Run the preregistered multi-snapshot repurchase analysis on DEV only."""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from features.day2_data import LABEL_T_CANDIDATES, load_dev_orders  # noqa: E402
from features.repurchase_v3 import build_multisnapshot_folds, build_multisnapshot_samples  # noqa: E402
from models.repurchase_v3 import evaluate_fixed_models, summarize_predictions  # noqa: E402
from models.classify import build_folds as build_legacy_folds  # noqa: E402
from models.repurchase_v3 import _metric_bundle  # noqa: E402


def _read_test_aggregate() -> dict[str, float | int | None]:
    """Read only precommitted segment aggregates; never test rows or labels."""
    path = ROOT / "outputs" / "tables" / "test_segment_profiles.csv"
    table = pd.read_csv(
        path,
        usecols=["scheme", "cohort", "customers", "mean_recency_days", "mean_frequency"],
    )
    groups = table[(table["scheme"] == "K=2") & (table["cohort"] == "test_pre_T")]
    customers = int(groups["customers"].sum())
    return {
        "n_customers": customers,
        "mean_recency_days": float(np.average(groups["mean_recency_days"], weights=groups["customers"])),
        "mean_frequency": float(np.average(groups["mean_frequency"], weights=groups["customers"])),
        "distribution_quantiles_available": False,
        "source": "outputs/tables/test_segment_profiles.csv; K=2, test_pre_T rows only",
    }


def _cluster_mean_ci(frame: pd.DataFrame, columns: list[str], *, draws: int = 2000, seed: int = 20261028) -> dict[str, dict[str, float]]:
    rng = np.random.default_rng(seed)
    grouped = frame.groupby("customer_key", sort=False)[columns].agg(["sum", "count"])
    keys_n = len(grouped)
    result = {}
    for column in columns:
        sums = grouped[(column, "sum")].to_numpy(dtype=float)
        counts = grouped[(column, "count")].to_numpy(dtype=float)
        values = []
        for _ in range(draws):
            multiplicity = rng.multinomial(keys_n, np.full(keys_n, 1 / keys_n))
            values.append(float(np.dot(multiplicity, sums) / np.dot(multiplicity, counts)))
        result[column] = {
            "lower_95": float(np.quantile(values, 0.025)),
            "upper_95": float(np.quantile(values, 0.975)),
            "draws": draws,
        }
    return result


def _legacy_baseline_diagnostic() -> dict:
    frame = pd.read_csv(ROOT / "outputs" / "tables" / "day2_label_samples_primary.csv")
    folds = build_legacy_folds(frame)
    y_all = frame["label_returned"].astype(int).to_numpy()
    oof = np.full(len(frame), np.nan)
    fold_rows = []
    for fold in folds:
        p = float(y_all[fold["train"]].mean())
        oof[fold["validation"]] = p
        y = y_all[fold["validation"]]
        fold_rows.append({
            "validation_T": str(fold["validation_t"]),
            "train_n": int(len(fold["train"])),
            "validation_n": int(len(fold["validation"])),
            "validation_positive_n": int(y.sum()),
            "train_prevalence_score": p,
            **_metric_bundle(y, np.full(len(y), p)),
        })
    valid = np.isfinite(oof)
    pooled = _metric_bundle(y_all[valid], oof[valid])
    return {
        "folds": fold_rows,
        "pooled": pooled,
        "pooled_oof_n": int(valid.sum()),
        "interpretation": "Each fold score is constant within that fold; pooled ROC-AUC can exceed 0.5 only from score differences across folds.",
    }


def _distribution(name: str, frame: pd.DataFrame, *, include_ci: bool = True) -> dict:
    result: dict = {
        "universe": name,
        "snapshot_rows": int(len(frame)),
        "unique_customers": int(frame["customer_key"].nunique()),
    }
    for col in ("recency_days", "frequency"):
        result[col] = {
            "mean": float(frame[col].mean()),
            "p25": float(frame[col].quantile(0.25)),
            "median": float(frame[col].median()),
            "p75": float(frame[col].quantile(0.75)),
            "min": float(frame[col].min()),
            "max": float(frame[col].max()),
        }
    if include_ci:
        result["cluster_bootstrap_mean_95"] = _cluster_mean_ci(frame, ["recency_days", "frequency"])
    return result


def main() -> int:
    split = yaml.safe_load((ROOT / "config" / "split.yaml").read_text(encoding="utf-8"))
    test_start = date.fromisoformat(str(split["test_start"]))
    # load_dev_orders gates on local inserted_at before accessing any other order field;
    # all feature/label construction below receives only status-3 DEV orders.
    orders, order_scope, _products = load_dev_orders()
    if order_scope.get("test_labels_loaded") or order_scope.get("test_behavior_loaded"):
        raise RuntimeError("DEV loader reported test access")
    frame = build_multisnapshot_samples(
        orders,
        test_start=test_start,
        n_days=int(split["primary_n_days"]),
        l_days=int(split["l_candidates_days"][0]),
        candidates=LABEL_T_CANDIDATES,
    )
    folds = build_multisnapshot_folds(
        frame,
        n_days=int(split["primary_n_days"]),
        l_days=int(split["l_candidates_days"][0]),
    )
    predictions, fold_metrics, baseline_info = evaluate_fixed_models(frame, folds)
    pooled_metrics, deciles, top_k, diagnostics = summarize_predictions(predictions)
    for row in deciles.to_dict("records"):
        if row["fold_or_pooled"] == "pooled":
            interval = diagnostics["bootstrap_95"][row["strategy"]][f"top_decile_rate_{row['decile_from_top']}"]
            deciles.loc[
                (deciles["strategy"] == row["strategy"])
                & (deciles["fold_or_pooled"] == "pooled")
                & (deciles["decile_from_top"] == row["decile_from_top"]),
                ["rate_lower_95", "rate_upper_95"],
            ] = [interval["lower_95"], interval["upper_95"]]
    for row in top_k.to_dict("records"):
        if row["fold_or_pooled"] == "pooled":
            interval = diagnostics["bootstrap_95"][row["strategy"]][f"precision_at_{row['top_pct']}pct"]
            top_k.loc[
                (top_k["strategy"] == row["strategy"])
                & (top_k["fold_or_pooled"] == "pooled")
                & (top_k["top_pct"] == row["top_pct"]),
                ["precision_lower_95", "precision_upper_95"],
            ] = [interval["lower_95"], interval["upper_95"]]

    current = pd.read_csv(ROOT / "outputs" / "tables" / "day2_label_samples_primary.csv")
    distributions = [
        _distribution("Mẫu DEV hiện tại (một snapshot/khách)", current),
        _distribution("DEV snapshot đa mốc", frame),
    ]
    test_aggregate = _read_test_aggregate()
    distributions.append({"universe": "Cohort scoring test, aggregate đã commit", **test_aggregate})

    result = {
        "status": "exploratory_dev_only_not_confirmed_out_of_sample",
        "protocol_sha256": hashlib.sha256((ROOT / "docs" / "analysis_plan_wp5.md").read_bytes()).hexdigest(),
        "snapshot_id": split["snapshot_id"],
        "analysis_window": "DEV only; T + N + L strictly before test_start",
        "test_start": str(test_start),
        "test_scope_access": {
            "date_field_read_for_dev_gate": "inserted_at",
            "other_test_order_fields_accessed": False,
            "test_labels_or_behavior_constructed": False,
            "test_aggregate_source": "outputs/tables/test_segment_profiles.csv; K=2, test_pre_T rows; only customer count and pre-T recency/frequency means read",
        },
        "dev_status3_order_count": int(order_scope["status3_dev_orders"]),
        "n_candidate_T": int(frame["as_of"].nunique()),
        "snapshot_rows": int(len(frame)),
        "unique_customers": int(frame["customer_key"].nunique()),
        "positive_snapshots": int(frame["label_returned"].sum()),
        "positive_rate": float(frame["label_returned"].mean()),
        "fold_count": len(folds),
        "common_baseline": baseline_info,
        "pooled_metrics_and_customer_bootstrap_95": {
            "metrics": pooled_metrics.to_dict("records"),
            **diagnostics,
        },
        "feature_distributions": distributions,
        "legacy_fold_prevalence_baseline_diagnostic": _legacy_baseline_diagnostic(),
        "number_of_preregistered_strategies": 4,
        "number_of_model_vs_common_baseline_comparisons": 3,
        "seed": 20261028,
        "bootstrap_draws": 2000,
        "run_attempt_log": [
            "Attempt 1 interrupted before output after the initial DataFrame-per-customer bootstrap implementation proved too slow; no metric was produced.",
            "Attempt 2 interrupted before output while profiling the first vectorized implementation; no metric was produced.",
            "Attempt 3 interrupted before output because sklearn recomputed ranking sorts for every bootstrap draw; no metric was produced.",
            "Attempt 4 completed the calculations but failed JSON serialization because a pandas DataFrame was nested in the result; no artifact was written.",
            "Final attempt uses vectorized cluster-bootstrap multiplicities and grouped-score weighted metrics, reusing the registered 2,000 draws, seed, folds, features, and four strategies.",
        ],
    }

    outputs = ROOT / "outputs"
    (outputs / "metrics").mkdir(exist_ok=True)
    (outputs / "tables").mkdir(exist_ok=True)
    table_outputs = {
        "repurchase_v3_dev_fold_metrics.csv": fold_metrics,
        "repurchase_v3_dev_deciles.csv": deciles,
        "repurchase_v3_dev_top_k.csv": top_k,
        "repurchase_v3_dev_calibration.csv": pd.DataFrame(diagnostics["calibration"]),
    }
    for name, table in table_outputs.items():
        if any(column.lower() in {"customer_key", "order_key", "customer_id", "phone", "email", "address"} for column in table.columns):
            raise ValueError(f"sensitive row key in aggregate output schema: {name}")
    (outputs / "metrics" / "repurchase_v3_dev.json").write_text(
        json.dumps(
            result, ensure_ascii=False, indent=2, allow_nan=False,
            default=lambda value: value.item() if hasattr(value, "item") else str(value),
        ) + "\n", encoding="utf-8"
    )
    for name, table in table_outputs.items():
        table.to_csv(outputs / "tables" / name, index=False)
    pd.DataFrame([
        {"universe": row["universe"], "n": row.get("snapshot_rows", row.get("n_customers")),
         "customers": row.get("unique_customers", row.get("n_customers")),
         "recency_mean": row.get("recency_days", {}).get("mean", row.get("mean_recency_days")),
         "recency_p25": row.get("recency_days", {}).get("p25"),
         "recency_median": row.get("recency_days", {}).get("median"),
         "recency_p75": row.get("recency_days", {}).get("p75"),
         "frequency_mean": row.get("frequency", {}).get("mean", row.get("mean_frequency")),
         "frequency_p25": row.get("frequency", {}).get("p25"),
         "frequency_median": row.get("frequency", {}).get("median"),
         "frequency_p75": row.get("frequency", {}).get("p75"),
         "quantiles_available": row.get("distribution_quantiles_available", True)}
        for row in distributions
    ]).to_csv(outputs / "tables" / "repurchase_v3_dev_feature_distributions.csv", index=False)
    print(json.dumps({
        "snapshot_rows": result["snapshot_rows"],
        "unique_customers": result["unique_customers"],
        "positives": result["positive_snapshots"],
        "fold_count": result["fold_count"],
        "legacy_baseline_pooled_roc_auc": result["legacy_fold_prevalence_baseline_diagnostic"]["pooled"]["roc_auc"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
