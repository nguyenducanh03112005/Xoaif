"""Run the single preregistered, development-only Day 3 gift/basket preparation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from features.day3_baskets import run_day3_pretest
from models.frozen_segmenters import freeze_dev_segmenters


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    amendment_path = ROOT / "config" / "amendment_05_gift_lines.yaml"
    lock_path = ROOT / "config" / "amendment_05_gift_lines.lock.json"
    amendment_bytes = amendment_path.read_bytes()
    amendment = yaml.safe_load(amendment_bytes)
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if sha256(amendment_path) != lock.get("amendment_sha256"):
        raise ValueError("Amendment 05 hash does not match its sealed sidecar")
    if lock.get("pre_open_label_reads") != 0 or lock.get("pre_open_behavior_reads") != 0:
        raise ValueError("Amendment 05 records a prior test read")
    if (ROOT / "outputs" / "metrics" / "test_opened.lock.json").exists():
        raise ValueError("The one-time test lock exists; pre-test work cannot run after opening")
    for key, rel in (
        ("gift_field_survey_sha256", "outputs/metrics/day3_gift_field_survey.json"),
        ("pre_open_reserved_access_log_sha256", "outputs/logs/reserved_access.jsonl"),
    ):
        expected = lock.get("survey_sha256") if key == "gift_field_survey_sha256" else lock.get("pre_open_access_log_sha256")
        if sha256(ROOT / rel) != expected:
            raise ValueError(f"Pre-test evidence changed: {rel}")
    access_entries = [json.loads(line) for line in (ROOT / "outputs/logs/reserved_access.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(access_entries) != 2 or any(entry.get("kind") != "eligibility_count" for entry in access_entries):
        raise ValueError("Reserved-data log is not still eligibility-only")
    survey = json.loads((ROOT / "outputs/metrics/day3_gift_field_survey.json").read_text(encoding="utf-8"))
    if survey.get("test_labels_loaded") is not False or survey.get("test_behavior_loaded") is not False:
        raise ValueError("Field survey reports test data access")

    combo = run_day3_pretest()
    combo["amendment_05_sha256"] = sha256(amendment_path)
    (ROOT / "outputs/metrics/day3_combo_prereg.json").write_text(json.dumps(combo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    segmenters = freeze_dev_segmenters()

    registry = json.loads((ROOT / "outputs/metrics/dev_final_models_v2.json").read_text(encoding="utf-8"))
    repurchase = registry["repurchase_features_v2"]
    old_model = registry["frozen_reference_model"]
    frozen_models = [
        {"name": "majority_baseline", "threshold": 0.5, "score": "development positive prevalence", "artifact": None},
        {"name": "amendment_03_logistic_regression", "threshold": 0.5, "parameters": {"C": 10.0},
         "artifact": "outputs/models/day2_dev_final_model.joblib", "sha256": old_model["sha256"]},
        {"name": "repurchase_features_v2_logistic_regression", "threshold": 0.5,
         "parameters": repurchase["selected_parameters"], "artifact": repurchase["final_model_path"],
         "sha256": repurchase["final_model_sha256"]},
    ]
    for model in frozen_models:
        if model["artifact"]:
            path = ROOT / model["artifact"]
            if sha256(path) != model["sha256"]:
                raise ValueError(f"Frozen model artifact hash mismatch: {model['artifact']}")

    output_paths = [
        "outputs/tables/product_profile.csv", "outputs/tables/gift_line_audit.csv",
        "outputs/tables/gift_line_rates_monthly.csv", "outputs/tables/gift_line_rates_order_size.csv",
        "outputs/tables/rules_v2.csv", "outputs/tables/combos_v2.csv",
        "outputs/tables/seasonal_pair_metrics.csv", "outputs/metrics/day3_combo_prereg.json",
        "outputs/models/segmenters_dev_frozen_v1.joblib", "outputs/metrics/frozen_segmenters_dev.json",
    ]
    input_paths = [
        "config/split.yaml", "config/split.lock.json", "config/amendment_04_followup.yaml",
        "config/amendment_05_gift_lines.yaml", "config/amendment_05_gift_lines.lock.json",
        "outputs/metrics/dev_final_models_v2.json", "outputs/metrics/dev_final_model.json",
        "outputs/tables/day2_features_primary.csv", "outputs/tables/day2_features_B.csv",
        "outputs/tables/segments.csv", "outputs/tables/segments_v2.csv",
        "outputs/metrics/day2b_segmentation.json", "outputs/metrics/day3_gift_field_survey.json",
        "outputs/models/day2_dev_final_model.joblib", "outputs/models/repurchase_features_v2.joblib",
    ]
    freeze_manifest = {
        "status": "development_inputs_and_outputs_frozen_before_test",
        "amendment_05_sha256": sha256(amendment_path),
        "model_registry_sha256": sha256(ROOT / "outputs/metrics/dev_final_models_v2.json"),
        "models": frozen_models,
        "repurchase_threshold": 0.5,
        "segmenter_bundle": segmenters,
        "outputs_sha256": {rel: sha256(ROOT / rel) for rel in output_paths},
        "inputs_sha256": {rel: sha256(ROOT / rel) for rel in input_paths},
        "access_log_before_test_sha256": sha256(ROOT / "outputs/logs/reserved_access.jsonl"),
        "test_labels_loaded": False,
        "test_behavior_loaded": False,
        "day3_started": False,
    }
    target = ROOT / "outputs/metrics/day3_pretest_freeze.json"
    target.write_text(json.dumps(freeze_manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Day 3 gift/basket dev preparation frozen; eligible baskets before/after={combo['eligible_baskets_before_gift_line_removal']}/{combo['eligible_baskets_after_all_gift_line_removal']}; stable combos={combo['main_combo_count']}.")
    print("Model artifacts and K-Means assignments match development; test labels and behavior remain unopened.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
