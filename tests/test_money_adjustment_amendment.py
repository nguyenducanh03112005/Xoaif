from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
import pytest

from ingest.decision_amendment import load_money_adjustment_amendment


def _json(path: Path, data: dict) -> bytes:
    payload = (json.dumps(data, indent=2) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return payload


def _project(root: Path) -> Path:
    config = root / "config"
    (config).mkdir(parents=True, exist_ok=True)
    split_lock = _json(config / "split.lock.json", {"snapshot_id": "s"})
    amendment_01 = b"status: approved_owner_decision\nanalysis_start: '2024-04-01'\n"
    (config / "amendment_01_analysis_start.yaml").write_bytes(amendment_01)
    amendment_02 = b"status: approved_owner_decision\namendment_id: 2\n"
    (config / "amendment_02_money_and_gift_rules.yaml").write_bytes(amendment_02)
    access = b'{"kind":"eligibility_count"}\n{"kind":"eligibility_count"}\n'
    (root / "outputs/logs").mkdir(parents=True, exist_ok=True)
    (root / "outputs/logs/reserved_access.jsonl").write_bytes(access)
    manifest = _json(root / "data/restricted/day1_warehouse_manifest.json", {"test_labels_loaded": False})
    quality = _json(root / "outputs/tables/dev_quality_summary.json", {"test_labels_loaded": False})
    hashes = {
        "split_lock_sha256": hashlib.sha256(split_lock).hexdigest(),
        "amendment_01_sha256": hashlib.sha256(amendment_01).hexdigest(),
        "amendment_02_sha256": hashlib.sha256(amendment_02).hexdigest(),
    }
    amendment = {
        "amendment_id": 3,
        "status": "approved_owner_decision",
        "decision_date": "2026-10-25",
        "supersedes": "amendment_02_money_and_gift_rules.yaml",
        "analysis_start": "2024-04-01",
        "source_hashes": hashes,
        "revenue_rule": {
            "primary_expression": "total_price_after_sub_discount - shipping_fee",
            "special_case_expression": "total_price_after_sub_discount",
        },
        "negative_revenue_rule": {"stop_if_count_share_exceeds": 0.01},
        "H_obs": {"interval": "[analysis_start, T)"},
        "pre_label_access_audit": {
            "reserved_access_log_entries": 2,
            "label_load_entries": 0,
            "test_behavior_load_entries": 0,
            "reserved_access_log_sha256": hashlib.sha256(access).hexdigest(),
            "day1_warehouse_manifest_sha256": hashlib.sha256(manifest).hexdigest(),
            "dev_quality_summary_sha256": hashlib.sha256(quality).hexdigest(),
        },
        "decision_precedes_day2_label_generation_and_modeling": True,
    }
    amendment_bytes = yaml.safe_dump(amendment, sort_keys=False).encode("utf-8")
    (config / "amendment_03_money_adjustment.yaml").write_bytes(amendment_bytes)
    _json(config / "amendment_03_money_adjustment.lock.json", {
        "amendment_sha256": hashlib.sha256(amendment_bytes).hexdigest(),
        "split_lock_sha256": hashes["split_lock_sha256"],
        "amendment_01_sha256": hashes["amendment_01_sha256"],
        "amendment_02_sha256": hashes["amendment_02_sha256"],
    })
    return root


def test_amendment_03_verifies_hashes_and_prelabel_evidence(tmp_path: Path) -> None:
    root = _project(tmp_path)
    amendment, digest = load_money_adjustment_amendment(root)
    assert amendment["H_obs"]["interval"] == "[analysis_start, T)"
    assert len(digest) == 64


def test_amendment_03_rejects_changed_lock_source(tmp_path: Path) -> None:
    root = _project(tmp_path)
    path = root / "config/amendment_03_money_adjustment.lock.json"
    lock = json.loads(path.read_text(encoding="utf-8"))
    lock["amendment_02_sha256"] = "0" * 64
    path.write_text(json.dumps(lock), encoding="utf-8")
    with pytest.raises(ValueError, match="prior money amendment"):
        load_money_adjustment_amendment(root)


def test_amendment_03_rejects_non_eligibility_reserved_access(tmp_path: Path) -> None:
    root = _project(tmp_path)
    access = root / "outputs/logs/reserved_access.jsonl"
    access.write_text(access.read_text(encoding="utf-8") + '{"kind":"label_load"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="Reserved access log"):
        load_money_adjustment_amendment(root)
