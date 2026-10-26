from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml
import pytest

from ingest.decision_amendment import load_decision_amendment


def _write_json(path: Path, value: dict) -> bytes:
    data = (json.dumps(value, indent=2) + "\n").encode("utf-8")
    path.write_bytes(data)
    return data


def _make_project(root: Path) -> Path:
    config = root / "config"
    logs = root / "outputs" / "logs"
    restricted = root / "data" / "restricted"
    tables = root / "outputs" / "tables"
    for folder in (config, logs, restricted, tables):
        folder.mkdir(parents=True, exist_ok=True)

    split_lock = _write_json(config / "split.lock.json", {"config_sha256": "a" * 64})
    amendment_01 = b"status: approved_owner_decision\nanalysis_start: '2024-04-01'\n"
    (config / "amendment_01_analysis_start.yaml").write_bytes(amendment_01)
    access = b'{"kind":"eligibility_count"}\n{"kind":"eligibility_count"}\n'
    (logs / "reserved_access.jsonl").write_bytes(access)
    manifest = _write_json(restricted / "day1_warehouse_manifest.json", {"test_labels_loaded": False})
    quality = _write_json(tables / "dev_quality_summary.json", {"test_labels_loaded": False})

    split_hash = hashlib.sha256(split_lock).hexdigest()
    amendment_01_hash = hashlib.sha256(amendment_01).hexdigest()
    amendment = {
        "amendment_id": 2,
        "status": "approved_owner_decision",
        "decision_date": "2026-10-25",
        "analysis_start": "2024-04-01",
        "source_hashes": {
            "split_lock_sha256": split_hash,
            "amendment_01_sha256": amendment_01_hash,
        },
        "decision_precedes_label_generation_and_modeling": True,
        "revenue_field_rule": {
            "expression": "total_price - total_discount",
            "eligible_status": 3,
        },
        "gift_rule": {"is_gift_if_any": ["condition 1", "condition 2"]},
        "anomaly_rule": {
            "money_anomaly_if_any": ["one", "two", "three", "four"],
            "stop_if_union_share_exceeds": 0.05,
        },
        "H_obs": {"interval": "[analysis_start, T)"},
        "pre_label_access_audit": {
            "reserved_access_log_entries": 2,
            "label_load_entries": 0,
            "test_behavior_load_entries": 0,
            "reserved_access_log_sha256": hashlib.sha256(access).hexdigest(),
            "day1_warehouse_manifest_sha256": hashlib.sha256(manifest).hexdigest(),
            "dev_quality_summary_sha256": hashlib.sha256(quality).hexdigest(),
        },
    }
    amendment_bytes = yaml.safe_dump(amendment, sort_keys=False).encode("utf-8")
    (config / "amendment_02_money_and_gift_rules.yaml").write_bytes(amendment_bytes)
    _write_json(
        config / "amendment_02_money_and_gift_rules.lock.json",
        {
            "amendment_sha256": hashlib.sha256(amendment_bytes).hexdigest(),
            "split_lock_sha256": split_hash,
            "amendment_01_sha256": amendment_01_hash,
        },
    )
    return root


def test_day2_amendment_verifies_against_pre_label_evidence(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    amendment, digest = load_decision_amendment(root)
    assert amendment["H_obs"]["interval"] == "[analysis_start, T)"
    assert len(digest) == 64


def test_day2_amendment_rejects_changed_amendment(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = root / "config" / "amendment_02_money_and_gift_rules.yaml"
    path.write_text(path.read_text(encoding="utf-8") + "# changed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash"):
        load_decision_amendment(root)


def test_day2_amendment_rejects_test_label_access(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    log = root / "outputs" / "logs" / "reserved_access.jsonl"
    log.write_text(log.read_text(encoding="utf-8") + '{"kind":"label_load"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="Reserved access log"):
        load_decision_amendment(root)
