from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_gateb_lock import REQUIRED_LOCKED_PATHS, verify_lock  # noqa: E402


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixture(root: Path) -> None:
    for directory in ("config", "docs", "scripts", "src/features", "tests", "outputs/metrics"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    config = {
        "amendment_id": "06-HO2", "revision": 3, "supersedes_lock_sha256": "oldhash",
        "status": "prepared_gate_b_not_open", "test_opened": False, "phase_c_started": False,
        "hypotheses": {
        "primary": {"ids": ["H1", "H2"]}, "secondary": {"ids": ["H3", "H4"]},
            "descriptive_only": {"ids": ["H5"]}, "not_testable": {"ids": ["H6"]},
        },
    }
    config["H4"] = {"comparison_absolute_tolerance": 1e-9, "minimum_common_groups": 4,
                     "s6_rho_dev_half_threshold": 0.9761904761904763,
                     "rfm_rho_dev_half_threshold": 1.0}
    config_path = root / "config/amendment_06_ho2.yaml"
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8", newline="\n")
    protocol_path = root / "docs/analysis_plan_amendment06_ho2.md"
    protocol_path.write_text("locked protocol\n", encoding="utf-8", newline="\n")
    freeze_path = root / "outputs/metrics/gateb_r5_strategy_freeze.json"
    freeze_path.write_text(json.dumps({"strategy_population_and_fit": {}}), encoding="utf-8")
    (root / ".gitattributes").write_text("config/amendment_06_ho2.lock.json -text\n", encoding="utf-8")
    for rel in REQUIRED_LOCKED_PATHS:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"frozen:{rel}\n", encoding="utf-8", newline="\n")
    files = [config_path, protocol_path, freeze_path, *(root / rel for rel in REQUIRED_LOCKED_PATHS)]
    hashes = {p.relative_to(root).as_posix(): _sha(p) for p in files}
    lock = {
        "amendment_id": "06-HO2", "revision": 3, "supersedes": "oldhash",
        "status": "prepared_gate_b_not_open", "test_opened": False, "phase_c_started": False,
        "config_sha256": _sha(config_path), "protocol_sha256": _sha(protocol_path),
        "frozen_source_sha256": hashes, "source_hash_count": len(hashes),
        "primary_hypothesis": ["H1", "H2"], "secondary_hypotheses": ["H3", "H4"],
        "descriptive_only": ["H5"], "not_testable": ["H6"],
        "r4_thresholds": {"comparison_absolute_tolerance": 1e-9, "minimum_common_groups": 4,
                           "s6_rho_dev_half_threshold": 0.9761904761904763,
                           "rfm_rho_dev_half_threshold": 1.0},
    }
    (root / "config/amendment_06_ho2.lock.json").write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8", newline="\n")


def test_closed_lock_verifies_all_required_hashes_and_outputs_absent(tmp_path: Path) -> None:
    _fixture(tmp_path)
    result = verify_lock(tmp_path)
    assert result["verified"] == result["source_hash_count"]
    assert result["test_opened"] is False
    assert result["revision"] == 3


def test_lock_verifier_rejects_hash_mutation_and_open_outputs(tmp_path: Path) -> None:
    _fixture(tmp_path)
    source = tmp_path / "src/features/holdout2_features.py"
    original = source.read_bytes()
    source.write_text("tampered", encoding="utf-8")
    with pytest.raises(ValueError, match="frozen hash mismatch"):
        verify_lock(tmp_path)
    source.write_bytes(original)
    opened = tmp_path / "outputs/metrics/holdout2_eval.json"
    opened.parent.mkdir(parents=True, exist_ok=True)
    opened.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="HO2 output already exists"):
        verify_lock(tmp_path)
