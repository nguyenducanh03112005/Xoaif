from __future__ import annotations

import sys
import hashlib
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from count_ho2_eligibility_preregistered import pre_t2_day  # noqa: E402
from summarize_ho2_power import build_report  # noqa: E402
import yaml  # noqa: E402


class InsertedAtOnly(dict):
    def get(self, key, default=None):
        if key != "inserted_at":
            raise AssertionError(f"field accessed before pre-T2 gate: {key}")
        return super().get(key, default)


def test_gate_accepts_only_local_dates_strictly_before_t2():
    assert pre_t2_day(InsertedAtOnly(inserted_at="2026-04-19T16:59:59Z")) == date(2026, 4, 19)
    assert pre_t2_day(InsertedAtOnly(inserted_at="2026-04-19T17:00:00Z")) is None
    assert pre_t2_day(InsertedAtOnly(inserted_at="2026-10-01T12:00:00Z")) is None


def test_gate_rejects_dates_before_analysis_start_and_invalid_dates():
    assert pre_t2_day(InsertedAtOnly(inserted_at="2024-03-31T16:59:59Z")) is None
    assert pre_t2_day(InsertedAtOnly(inserted_at="not-a-date")) is None


def test_power_summary_is_label_free_and_marks_h2_power_below_target():
    result = build_report()
    assert result["N_eligible_pre_T2"] == 7282
    assert result["N_frequency_ge_2"] == 988
    assert result["N_frequency_eq_1"] == 6294
    assert result["reference_scenarios"]["test_aggregate_reference"]["h2_rr_scenarios"]["2.0"][
        "approx_power_against_rr_1_5"
    ] < 0.8
    assert "no HO2 labels" in result["scope"]


def test_amendment_lock_matches_protocol_and_keeps_window_closed():
    config = yaml.safe_load((ROOT / "config/amendment_06_ho2.yaml").read_text(encoding="utf-8"))
    lock = json.loads((ROOT / "config/amendment_06_ho2.lock.json").read_text(encoding="utf-8"))
    protocol_bytes = (ROOT / "docs/analysis_plan_amendment06_ho2.md").read_bytes()
    config_bytes = (ROOT / "config/amendment_06_ho2.yaml").read_bytes()
    assert hashlib.sha256(protocol_bytes).hexdigest() == lock["protocol_sha256"]
    assert hashlib.sha256(config_bytes).hexdigest() == lock["config_sha256"]
    assert config["label_window"]["not_opened"] is True
    assert config["gate"]["requires_explicit_owner_authorization_to_open"] is True
    assert lock["test_opened"] is False
