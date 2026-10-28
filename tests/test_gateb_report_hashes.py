from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_amendment06_gateb_report import build_report, sha  # noqa: E402


def test_report_hash_table_matches_lock_and_file_bytes() -> None:
    lock_path = ROOT / "config/amendment_06_ho2.lock.json"
    if not lock_path.is_file():
        pytest.skip("Gate B revision-2 lock is not built yet")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("revision") != 3:
        pytest.skip("Gate B revision-3 lock is not built yet")
    missing = [rel for rel in lock["frozen_source_sha256"] if not (ROOT / rel).is_file()]
    if missing:
        pytest.skip("local frozen artifacts are not shipped in this checkout")
    report = build_report(test_count=165)
    assert "revision 3" in report
    for rel, expected in lock["frozen_source_sha256"].items():
        actual = sha(ROOT / rel)
        assert actual == expected
        assert f"| `{rel}` | `{actual}` | `{expected}` | khớp |" in report
    assert f"`{sha(lock_path)}`" in report


def test_hypothesis_lists_are_consistent_across_config_lock_and_protocol() -> None:
    lock_path = ROOT / "config/amendment_06_ho2.lock.json"
    if not lock_path.is_file():
        pytest.skip("Gate B revision-2 lock is not built yet")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if lock.get("revision") != 3:
        pytest.skip("Gate B revision-3 lock is not built yet")
    config = yaml.safe_load((ROOT / "config/amendment_06_ho2.yaml").read_bytes())
    protocol = (ROOT / "docs/analysis_plan_amendment06_ho2.md").read_text(encoding="utf-8")
    report = build_report(test_count=165)
    mappings = {
        "primary": (lock["primary_hypothesis"], config["hypotheses"]["primary"]["ids"], ["H1", "H2"]),
        "secondary": (lock["secondary_hypotheses"], config["hypotheses"]["secondary"]["ids"], ["H3", "H4"]),
        "descriptive": (lock["descriptive_only"], config["hypotheses"]["descriptive_only"]["ids"], ["H5", "holdout2_prevalence", "calibration_in_the_large", "D005_vs_univariate_baselines"]),
        "not_testable": (lock["not_testable"], config["hypotheses"]["not_testable"]["ids"], ["H6"]),
    }
    for _, (locked, configured, expected) in mappings.items():
        assert locked == configured == expected
        for hypothesis in ("H1", "H2", "H3", "H4", "H5", "H6"):
            if hypothesis in expected:
                assert (f"**{hypothesis}" in protocol or f"{hypothesis}:" in protocol
                        or f"## {hypothesis}" in protocol)
                assert (f"**{hypothesis}" in report or f"{hypothesis}:" in report
                        or f"## {hypothesis}" in report)


def test_report_includes_g1_diagnostics_g2_prevalence_and_g3_proposal() -> None:
    lock = json.loads((ROOT / "config/amendment_06_ho2.lock.json").read_text(encoding="utf-8"))
    if lock.get("revision") != 3:
        pytest.skip("Gate B revision-3 lock is not built yet")
    report = build_report(test_count=170)
    assert "S6, một swap liền kề, SciPy spearmanr" in report
    assert "S6, một ULP dưới ngưỡng" in report
    assert "chưa kiểm tính chuyển prevalence sang ho2" in report.lower()
    assert "G3 — đề xuất, chưa thực hiện" in report
    assert "2026-10-27" in report
