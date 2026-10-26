"""Write the exact test evaluation configuration and sealed source hashes."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import pandas as pd

import yaml

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    metrics = ROOT / "outputs" / "metrics"
    lock_path = metrics / "test_opened.lock.json"
    if lock_path.exists():
        raise SystemExit("Refusing to preregister after the test has been opened.")
    if (ROOT / "outputs" / "logs" / "test_eval_access.jsonl").exists():
        raise SystemExit("Refusing to preregister: a post-open access log already exists.")

    freeze_path = metrics / "day3_pretest_freeze.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if freeze.get("test_labels_loaded") is not False or freeze.get("test_behavior_loaded") is not False:
        raise ValueError("Pre-test freeze does not attest that test remains unread")
    if freeze.get("day3_started") is not False:
        raise ValueError("Day 3 was already marked started before the test")

    input_paths = [
        "config/split.yaml", "config/split.lock.json",
        "config/amendment_01_analysis_start.yaml",
        "config/amendment_01_analysis_start.lock.json",
        "config/amendment_02_money_and_gift_rules.yaml",
        "config/amendment_02_money_and_gift_rules.lock.json",
        "config/amendment_03_money_adjustment.yaml",
        "config/amendment_03_money_adjustment.lock.json",
        "config/amendment_04_followup.yaml", "config/amendment_04_followup.lock.json",
        "config/amendment_05_gift_lines.yaml", "config/amendment_05_gift_lines.lock.json",
        "config/field_allowlist.yaml",
        "outputs/metrics/dev_final_models_v2.json", "outputs/metrics/dev_final_model.json",
        "outputs/metrics/day3_pretest_freeze.json", "outputs/metrics/day3_combo_prereg.json",
        "outputs/metrics/frozen_segmenters_dev.json",
        "outputs/models/day2_dev_final_model.joblib",
        "outputs/models/repurchase_features_v2.joblib",
        "outputs/models/segmenters_dev_frozen_v1.joblib",
        "outputs/tables/day2_features_primary.csv", "outputs/tables/segments.csv",
        "outputs/tables/segments_v2.csv", "outputs/tables/rules_v2.csv",
        "outputs/tables/combos_v2.csv", "outputs/tables/seasonal_pair_metrics.csv",
        "outputs/logs/reserved_access.jsonl",
        "outputs/metrics/day3_gift_field_survey.json",
        "data/raw/pancake_orders/20261024T052943Z/manifest.json",
        "scripts/evaluate_test_once.py", "src/features/gift_lines.py",
        "src/features/day2_data.py", "src/features/day2b_data.py",
        "src/features/money.py", "src/models/classify.py",
        "src/models/classify_v2.py", "src/models/frozen_segmenters.py",
        "src/ingest/test_open_lock.py",
    ]
    input_hashes = {rel: digest(ROOT / rel) for rel in input_paths}
    split = yaml.safe_load((ROOT / "config" / "split.yaml").read_bytes())
    registry = json.loads((metrics / "dev_final_models_v2.json").read_text(encoding="utf-8"))
    combo_metrics = json.loads((metrics / "day3_combo_prereg.json").read_text(encoding="utf-8"))
    segment_metrics = json.loads((metrics / "frozen_segmenters_dev.json").read_text(encoding="utf-8"))
    old_model = json.loads((metrics / "dev_final_model.json").read_text(encoding="utf-8"))
    access_log = ROOT / "outputs" / "logs" / "reserved_access.jsonl"
    access_rows = [line for line in access_log.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(access_rows) != 2 or digest(access_log) != freeze.get("access_log_before_test_sha256"):
        raise ValueError("Reserved-access evidence differs from the sealed pre-test state")
    for rel, expected in freeze.get("outputs_sha256", {}).items():
        if digest(ROOT / rel) != expected:
            raise ValueError(f"Frozen development output changed: {rel}")
    for rel, expected in freeze.get("inputs_sha256", {}).items():
        if digest(ROOT / rel) != expected:
            raise ValueError(f"Frozen development input changed: {rel}")

    models = [
        {
            "name": "majority_baseline",
            "score": "development positive prevalence from dev_final_models_v2.json",
            "threshold": 0.5,
            "artifact": None,
            "score_value": registry["repurchase_features_v2"]["positive_rate"],
        },
        {
            "name": "amendment_03_logistic_regression",
            "parameters": {"C": 10.0}, "threshold": 0.5,
            "artifact": "outputs/models/day2_dev_final_model.joblib",
            "artifact_sha256": freeze["models"][1]["sha256"],
            "feature_schema": "src/models/classify.py NUMERIC_COLUMNS + CATEGORICAL_COLUMNS",
        },
        {
            "name": "repurchase_features_v2_logistic_regression",
            "parameters": registry["repurchase_features_v2"]["selected_parameters"],
            "threshold": 0.5,
            "artifact": registry["repurchase_features_v2"]["final_model_path"],
            "artifact_sha256": registry["repurchase_features_v2"]["final_model_sha256"],
            "feature_schema": "feature_columns in dev_final_models_v2.json; latest order strictly before T",
        },
    ]
    features = registry["repurchase_features_v2"]["feature_columns"]
    combos = pd.read_csv(ROOT / "outputs" / "tables" / "combos_v2.csv")
    frozen_pairs = [
        {
            "product_a_key_hmac": str(row["product_a_key_hmac"]),
            "product_b_key_hmac": str(row["product_b_key_hmac"]),
            "display_name": str(row["combo_name"]),
        }
        for row in combos.to_dict("records")
    ]
    config = {
        "amendment_id": "05-test-open",
        "status": "locked_before_one_time_test_open",
        "registered_at_utc": datetime.now(timezone.utc).isoformat(),
        "timezone": "Asia/Ho_Chi_Minh",
        "snapshot_id": split["snapshot_id"],
        "test_interval": {
            "start_inclusive": str(split["test_start"]),
            "end_exclusive": str(split["test_end_exclusive"]),
            "label_horizon_days": int(split["primary_n_days"]),
            "eligible_customer_rule": "at least one status-3, non-order-gift purchase with customer ID strictly before T",
            "outcome_rule": "at least one status-3, non-order-gift purchase with local date > T and < the locked test_end_exclusive; the exclusive endpoint is not read",
            "nominal_horizon_note": "The locked 180-day calendar interval has 179 post-T local dates because its end is exclusive.",
            "test_order_gift_rule": "active amendment 03 money assessment; exclude order-level gifts",
        },
        "models": models,
        "classification": {
            "numeric_features_v1": [
                "recency_days", "frequency", "monetary", "average_order_value", "max_order_value",
                "total_quantity", "distinct_products", "mean_days_between_orders", "first_order_month",
                "first_order_month_sin", "first_order_month_cos", "nearest_holiday_distance_days",
                "adjustment_positive_rate", "adjustment_negative_rate", "no_history_after_sensitivity",
            ],
            "categorical_features_v1": ["province"],
            "feature_columns_v2": features,
            "threshold_selection": "fixed 0.5; no test threshold search",
            "metrics": ["precision", "recall", "f1", "roc_auc", "average_precision", "confusion_matrix_tn_fp_fn_tp"],
            "bootstrap": {"repetitions": 2000, "seed": 20261026, "unit": "customer row, paired across models and baseline", "interval": "percentile 95%"},
            "baseline_comparison": "paired average-precision difference versus constant dev positive prevalence",
            "dev_prevalence_source": "outputs/metrics/dev_final_models_v2.json repurchase_features_v2.positive_rate",
            "signal_rule": "signal only if lower ROC-AUC 95% CI > 0.55 AND lower paired AP-difference 95% CI > 0",
        },
        "segmentation": {
            "population": "eligible customers at T with at least one prior status-3 non-gift purchase",
            "rfm_as_of": str(split["test_start"]),
            "kmeans_values": [2, 3, 4],
            "model_bundle": "outputs/models/segmenters_dev_frozen_v1.joblib",
            "model_bundle_sha256": segment_metrics["model_sha256"],
            "rule_thresholds_source": "outputs/metrics/frozen_segmenters_dev.json business_rule_thresholds and business_like_proxy_thresholds",
            "business_rule_thresholds": segment_metrics["business_rule_thresholds"],
            "business_like_proxy_thresholds": segment_metrics["business_like_proxy_thresholds"],
            "no_fit_or_threshold_update": True,
            "comparison": "size, customer share, pre-T recognized-revenue share and mean R/F/M versus locked development profile; total-variation distance for mix and normalized Wasserstein-1 (dev IQR) for R/F/M; test-window recognized revenue share also descriptive",
            "business_like_proxy_label": "proxy only; not a verified enterprise-customer identity",
        },
        "association_rules": {
            "frozen_tables": ["outputs/tables/rules_v2.csv", "outputs/tables/combos_v2.csv"],
            "frozen_pair_keys_from": "combos_v2.csv product_a_key_hmac/product_b_key_hmac; exact hash in freeze manifest",
            "frozen_combo_count": len(frozen_pairs),
            "frozen_pairs": frozen_pairs,
            "basket_rule": "status-3 non-order-gift order; classify line gifts by locked amendment 05; remove gift_line=true; aggregate variations to product_id; require >=2 distinct product IDs",
            "metrics": ["support", "confidence_both_directions", "lift", "delta_support_vs_dev", "delta_confidence_vs_dev", "delta_lift_vs_dev", "test_lift_gt_1"],
            "no_new_rule_discovery": True,
        },
        "predeclared_interpretation": {
            "nonstationarity": "if test differs clearly from dev, describe as evidence of temporal/nonstationary behavior; test includes Tet 2026; do not adjust models or rules",
            "association_caveat": "co-occurrence only; not causal",
            "known_limitations": ["only one complete Tet cycle in development", "line-level inferred_subset may be wrong", "no cost basis", "current status is not a historical status timeline"],
        },
        "frozen_sources_sha256": input_hashes,
        "frozen_manifest_sha256": digest(freeze_path),
        "pre_open_evidence": {
            "reserved_access_log_sha256": digest(access_log),
            "reserved_access_log_entries": len(access_rows),
            "pre_open_label_reads": 0,
            "pre_open_behavior_reads": 0,
            "test_labels_loaded": False,
            "test_behavior_loaded": False,
        },
        "constraints": {
            "test_openings": 1,
            "after_open_do_not_refit_reselect_or_rerun_evaluation": True,
            "cancel_refund_model": "not fitted; registered positive-support gate failed in development",
            "no_pii_outputs": True,
        },
    }
    target = ROOT / "config" / "amendment_05_test_open.yaml"
    target.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False, width=100), encoding="utf-8")
    lock = {
        "config_path": "config/amendment_05_test_open.yaml",
        "config_sha256": digest(target),
        "frozen_sources_sha256": input_hashes,
        "frozen_manifest_sha256": digest(freeze_path),
        "test_opened_lock_absent_at_seal": True,
        "pre_open_label_reads": 0,
        "pre_open_behavior_reads": 0,
        "sealed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (ROOT / "config" / "amendment_05_test_open.lock.json").write_text(
        json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Test opening configuration sealed: {digest(target)}; frozen inputs={len(input_hashes)}; test still closed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
