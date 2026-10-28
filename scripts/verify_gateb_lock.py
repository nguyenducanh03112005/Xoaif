"""Verify closed Gate B revision-3 hashes and absence of any HO2 outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_LOCKED_PATHS = {
    "docs/analysis_plan_gateb_r6_fix.md",
    "scripts/evaluate_holdout2_once.py",
    "src/features/holdout2_access.py",
    "src/features/holdout2_features.py",
    "src/features/holdout2_metrics.py",
    "tests/test_holdout2_feature_boundary.py",
    "tests/test_holdout2_metrics.py",
    "scripts/build_amendment06_lock.py",
    "scripts/verify_gateb_lock.py",
    "scripts/build_amendment06_gateb_report.py",
}
FORBIDDEN_OUTPUTS = (
    "outputs/metrics/holdout2_opened.lock.json",
    "outputs/metrics/holdout2_eval.json",
    "docs/holdout2_report.md",
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_lock(root: Path = ROOT, *, allow_missing_local_models: bool = False) -> dict:
    lock_path = root / "config/amendment_06_ho2.lock.json"
    config_path = root / "config/amendment_06_ho2.yaml"
    protocol_path = root / "docs/analysis_plan_amendment06_ho2.md"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    config = yaml.safe_load(config_path.read_bytes())
    if lock.get("amendment_id") != "06-HO2" or lock.get("revision") != 3:
        raise ValueError("06-HO2 lock must be revision 3")
    if lock.get("status") != "prepared_gate_b_not_open" or lock.get("test_opened") is not False:
        raise ValueError("Gate B must stay closed")
    if lock.get("phase_c_started") is not False:
        raise ValueError("Phase C must not have started")
    if lock.get("supersedes") != config.get("supersedes_lock_sha256"):
        raise ValueError("supersedes hash differs from config")
    if digest(config_path) != lock.get("config_sha256"):
        raise ValueError("Amendment 06 YAML hash mismatch")
    if digest(protocol_path) != lock.get("protocol_sha256"):
        raise ValueError("Amendment 06 protocol hash mismatch")
    hashes = lock.get("frozen_source_sha256", {})
    missing_required = REQUIRED_LOCKED_PATHS - set(hashes)
    if missing_required:
        raise ValueError(f"required evaluator/feature/test files missing from lock: {sorted(missing_required)}")
    mismatches, missing = [], []
    for rel, expected in hashes.items():
        path = root / rel
        if not path.is_file():
            if allow_missing_local_models and rel.startswith("outputs/models/"):
                missing.append(rel)
                continue
            missing.append(rel)
            continue
        if digest(path) != expected:
            mismatches.append(rel)
    if mismatches:
        raise ValueError(f"frozen hash mismatch: {mismatches}")
    required_missing = [p for p in missing if p not in REQUIRED_LOCKED_PATHS]
    if required_missing and not allow_missing_local_models:
        raise FileNotFoundError(f"frozen inputs are unavailable: {required_missing}")
    if lock.get("source_hash_count") != len(hashes):
        raise ValueError("source hash count mismatch")
    freeze_path = root / "outputs/metrics/gateb_r5_strategy_freeze.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    for name, item in freeze["strategy_population_and_fit"].items():
        rel = item.get("artifact", item.get("path"))
        expected = item.get("sha256")
        if expected and (not rel or hashes.get(rel) != expected):
            raise ValueError(f"strategy artifact is not frozen in revision-3 lock: {name}")
    expected_sets = {
        "primary_hypothesis": config["hypotheses"]["primary"]["ids"],
        "secondary_hypotheses": config["hypotheses"]["secondary"]["ids"],
        "descriptive_only": config["hypotheses"]["descriptive_only"]["ids"],
        "not_testable": config["hypotheses"]["not_testable"]["ids"],
    }
    for key, expected in expected_sets.items():
        if lock.get(key) != expected:
            raise ValueError(f"hypothesis list mismatch: {key}")
    if config.get("revision") != 3 or config.get("test_opened") is not False or config.get("phase_c_started") is not False:
        raise ValueError("config indicates opened state")
    tolerance = config.get("H4", {}).get("comparison_absolute_tolerance")
    if tolerance != 1e-9 or lock.get("r4_thresholds", {}).get("comparison_absolute_tolerance") != tolerance:
        raise ValueError("H4 comparison tolerance differs from preregistration or lock")
    if lock.get("r4_thresholds", {}).get("minimum_common_groups") != config["H4"]["minimum_common_groups"]:
        raise ValueError("H4 minimum common-group count differs from lock")
    for key in ("s6_rho_dev_half_threshold", "rfm_rho_dev_half_threshold"):
        if lock.get("r4_thresholds", {}).get(key) != config["H4"].get(key):
            raise ValueError(f"H4 threshold differs from YAML: {key}")
    existing_outputs = [p for p in FORBIDDEN_OUTPUTS if (root / p).exists()]
    if existing_outputs:
        raise ValueError(f"HO2 output already exists: {existing_outputs}")
    if b"\r" in lock_path.read_bytes():
        raise ValueError("Gate B lock must use LF line endings")
    attrs = (root / ".gitattributes").read_text(encoding="utf-8") if (root / ".gitattributes").is_file() else ""
    if "config/amendment_06_ho2.lock.json -text" not in attrs:
        raise ValueError("Gate B lock is missing byte-preserving EOL rule")
    return {"revision": 3, "source_hash_count": len(hashes), "verified": len(hashes) - len(mismatches) - len(missing),
            "missing_local_model_artifacts": missing, "test_opened": False, "phase_c_started": False}


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--shipped-only", action="store_true",
                        help="allow local model binaries omitted from source control")
    args = parser.parse_args()
    result = verify_lock(allow_missing_local_models=args.shipped_only)
    suffix = f"; {len(result['missing_local_model_artifacts'])} local model artifacts absent" if result["missing_local_model_artifacts"] else ""
    print(f"Gate B 06-HO2 revision 3 verified: {result['verified']}/{result['source_hash_count']} source hashes; closed{suffix}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
