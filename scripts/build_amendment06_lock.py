"""Build Amendment 06-HO2 revision-2 lock from preregistered files and local DEV artifacts."""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OLD_LOCK_SHA256 = "a6c751a50625d8d98ffb2a8c10573d61cac9158e21dd3e16493715a3c413e94d"

FROZEN_PATHS = (
    ".gitignore", "config/amendment_06_ho2.yaml", "config/split.yaml", "config/split.lock.json",
    "config/amendment_05_gift_lines.yaml", "docs/analysis_plan_amendment06_ho2.md",
    "docs/analysis_plan_gateb_r2.md", "docs/gateb_r2_results.md", "docs/analysis_plan_gateb_r4.md",
    "docs/gateb_r4_results.md", "docs/analysis_plan_gateb_r5.md", "docs/gateb_r5_results.md",
    "docs/analysis_plan_wp5.md", "docs/analysis_plan_wp5b.md", "docs/analysis_plan_wp5c.md",
    "docs/canonical_numbers.md", "docs/decisions.md", "docs/amendment_log.md",
    "docs/ho2_access_audit.md", "docs/cohort_definitions.md", "docs/test_provenance_note.md",
    "outputs/metrics/test_opened.lock.json", "outputs/metrics/test_eval.json",
    "outputs/metrics/day3_pretest_freeze.json", "outputs/logs/test_eval_access.jsonl",
    "outputs/metrics/repurchase_v3_dev.json", "outputs/metrics/repurchase_wp5b_dev.json",
    "outputs/metrics/repurchase_wp5c_dev.json", "outputs/metrics/dev_final_model.json",
    "outputs/metrics/dev_final_models_v2.json", "outputs/metrics/frozen_segmenters_dev.json",
    "outputs/metrics/gateb_r2_rr_dev.json", "outputs/metrics/gateb_r2_power.json",
    "outputs/metrics/gateb_r4_dev_calibration.json", "outputs/metrics/gateb_r5_strategy_freeze.json",
    "outputs/tables/repurchase_wp5c_train_rates.csv", "outputs/tables/combos_v2.csv",
    "outputs/tables/combo_recommendation_screen_f3.csv", "outputs/models/day2_dev_final_model.joblib",
    "outputs/models/repurchase_features_v2.joblib", "outputs/models/segmenters_dev_frozen_v1.joblib",
    "outputs/models/gateb_r5/s3_final_dev.joblib", "outputs/models/gateb_r5/s6_final_dev.json",
    "outputs/models/gateb_r5/v3_final_dev.joblib", "scripts/count_ho2_eligibility_preregistered.py",
    "scripts/summarize_ho2_power.py", "scripts/analyze_gateb_r2_dev.py",
    "scripts/summarize_gateb_r2_power.py", "scripts/calibrate_gateb_r4_dev.py",
    "scripts/freeze_gateb_strategies_dev.py", "scripts/evaluate_holdout2_once.py",
    "scripts/evaluate_repurchase_wp5b_dev.py", "scripts/evaluate_repurchase_wp5c_dev.py",
    "scripts/audit_committed_aggregate_dates.py",
    "scripts/build_amendment06_lock.py", "scripts/build_amendment06_gateb_report.py",
    "scripts/build_amendment06_revision_log.py", "scripts/verify_gateb_lock.py", "scripts/run_all.py",
    "scripts/verify_day3_locks.py", "scripts/verify_pii.py", "scripts/verify_readonly.py",
    "scripts/fix_sealed_eol.py",
    "src/features/day2_data.py", "src/features/day2b_data.py", "src/features/money.py",
    "src/features/gift_lines.py", "src/features/repurchase_v3.py", "src/features/holdout2_access.py",
    "src/features/holdout2_features.py", "src/features/holdout2_metrics.py",
    "src/models/classify.py", "src/models/classify_v2.py", "src/models/repurchase_v3.py",
    "src/models/frozen_segmenters.py", "src/ingest/identifiers.py", "src/ingest/settings.py",
    "tests/test_gateb_r4_calibration.py", "tests/test_gateb_r5_freeze.py",
    "tests/test_gateb_aggregate_date_audit.py",
    "tests/test_holdout2_metrics.py", "tests/test_holdout2_feature_boundary.py",
    "tests/test_gateb_lock_verification.py", "tests/test_gateb_report_hashes.py",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_lock() -> dict:
    config_path = ROOT / "config/amendment_06_ho2.yaml"
    protocol_path = ROOT / "docs/analysis_plan_amendment06_ho2.md"
    config = yaml.safe_load(config_path.read_bytes())
    if config.get("revision") != 2 or config.get("test_opened") is not False:
        raise ValueError("Amendment 06 YAML must be revision 2 and closed")
    if config.get("supersedes_lock_sha256") != OLD_LOCK_SHA256:
        raise ValueError("supersedes hash does not match Gate B revision-1 lock")
    missing = [p for p in FROZEN_PATHS if not (ROOT / p).is_file()]
    if missing:
        raise FileNotFoundError(f"required frozen file missing: {missing}")
    hashes = {rel: digest(ROOT / rel) for rel in sorted(set(FROZEN_PATHS))}
    r2 = json.loads((ROOT / "outputs/metrics/gateb_r2_power.json").read_text(encoding="utf-8"))
    rr = json.loads((ROOT / "outputs/metrics/gateb_r2_rr_dev.json").read_text(encoding="utf-8"))["rr_frequency_ge_2_vs_eq_1"]
    r4 = json.loads((ROOT / "outputs/metrics/gateb_r4_dev_calibration.json").read_text(encoding="utf-8"))
    r5 = json.loads((ROOT / "outputs/metrics/gateb_r5_strategy_freeze.json").read_text(encoding="utf-8"))
    lock = {
        "amendment_id": "06-HO2", "revision": 2, "supersedes": OLD_LOCK_SHA256,
        "status": "prepared_gate_b_not_open", "locked_date": str(date(2026, 10, 28)),
        "protocol_sha256": digest(protocol_path), "config_sha256": digest(config_path),
        "frozen_source_sha256": hashes,
        "source_hash_count": len(hashes),
        "candidate_strategies": {"eligible": config["strategy_freeze"]["eligible"],
                                 "selected_candidate": None,
                                 "fit_artifact_hashes": {k: v.get("sha256") for k, v in r5["strategy_population_and_fit"].items()
                                                          if v.get("sha256")}},
        "pre_t2_counts": {"eligible_customers": 7282, "frequency_ge_2": 988,
                          "frequency_eq_1": 6294, "outcome_fields_read": 0,
                          "old_test_labels_used_for_fit_or_selection": 0},
        "r2_decision": {"rr_dev": rr["rr"], "ci_95": [rr["ci95_lower"], rr["ci95_upper"]],
                        "h2_primary": bool(r2["h2_primary"]), "h2_power_at_lower_dev_both_references":
                        r2["h2_power_at_rr_lower_dev_both_references"]},
        "r4_thresholds": {"s6_rho_dev_half": r4["dev_half_reference"]["s6"]["rho"],
                          "rfm_rho_dev_half": r4["dev_half_reference"]["rfm"]["rho"],
                          "k_dev": r4["h5"]["k_dev"]},
        "primary_hypothesis": config["hypotheses"]["primary"]["ids"],
        "secondary_hypotheses": config["hypotheses"]["secondary"]["ids"],
        "descriptive_only": config["hypotheses"]["descriptive_only"]["ids"],
        "not_testable": config["hypotheses"]["not_testable"]["ids"],
        "test_opened": False, "phase_c_started": False,
        "requires_explicit_owner_phrase": config["gate"]["required_phrase"],
        "access_audit": {"prior_test_eval_not_rerun": True, "ho2_labels_or_outcomes_read": 0,
                          "loader_requires_valid_open_lock": True, "scope": "repo code and committed metadata only"},
    }
    return lock


def main() -> int:
    lock = build_lock()
    path = ROOT / "config/amendment_06_ho2.lock.json"
    path.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote closed 06-HO2 revision 2 lock; {lock['source_hash_count']} source hashes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
