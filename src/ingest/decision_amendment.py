"""Verify the owner-approved Day 2 money, gift, anomaly, and H_obs amendment."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_decision_amendment(project_root: Path) -> tuple[dict[str, Any], str]:
    config_dir = project_root / "config"
    amendment_path = config_dir / "amendment_02_money_and_gift_rules.yaml"
    sidecar_path = config_dir / "amendment_02_money_and_gift_rules.lock.json"
    split_lock_path = config_dir / "split.lock.json"
    analysis_amendment_path = config_dir / "amendment_01_analysis_start.yaml"

    amendment_bytes = amendment_path.read_bytes()
    amendment = yaml.safe_load(amendment_bytes)
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    split_lock_hash = _sha256(split_lock_path.read_bytes())
    analysis_amendment_hash = _sha256(analysis_amendment_path.read_bytes())
    amendment_hash = _sha256(amendment_bytes)

    if not isinstance(amendment, dict) or amendment.get("status") != "approved_owner_decision":
        raise ValueError("Day 2 amendment is missing or not an approved owner decision")
    if amendment.get("amendment_id") != 2 or amendment.get("decision_date") != "2026-10-25":
        raise ValueError("Day 2 amendment identity/date does not match the recorded decision")
    if sidecar.get("amendment_sha256") != amendment_hash:
        raise ValueError("Day 2 amendment hash does not match its sidecar")
    if sidecar.get("split_lock_sha256") != split_lock_hash:
        raise ValueError("Day 2 sidecar points to a different split lock")
    if sidecar.get("amendment_01_sha256") != analysis_amendment_hash:
        raise ValueError("Day 2 sidecar points to a different analysis-start amendment")

    source_hashes = amendment.get("source_hashes", {})
    if source_hashes.get("split_lock_sha256") != split_lock_hash:
        raise ValueError("Day 2 amendment records a different split lock hash")
    if source_hashes.get("amendment_01_sha256") != analysis_amendment_hash:
        raise ValueError("Day 2 amendment records a different analysis-start hash")
    if amendment.get("analysis_start") != "2024-04-01":
        raise ValueError("Day 2 amendment uses a different analysis_start")
    if amendment.get("decision_precedes_label_generation_and_modeling") is not True:
        raise ValueError("Day 2 decision is not declared before label/model generation")

    revenue = amendment.get("revenue_field_rule", {})
    if revenue.get("expression") != "total_price - total_discount" or revenue.get("eligible_status") != 3:
        raise ValueError("Approved revenue rule differs from the owner decision")
    gift = amendment.get("gift_rule", {})
    if len(gift.get("is_gift_if_any", [])) != 2:
        raise ValueError("Gift rule must contain the two approved conditions")
    anomaly = amendment.get("anomaly_rule", {})
    if len(anomaly.get("money_anomaly_if_any", [])) != 4:
        raise ValueError("Money anomaly rule must contain the four approved conditions")
    if float(anomaly.get("stop_if_union_share_exceeds", 0)) != 0.05:
        raise ValueError("Money anomaly stop threshold differs from the owner decision")
    if amendment.get("H_obs", {}).get("interval") != "[analysis_start, T)":
        raise ValueError("H_obs interval differs from the owner decision")

    audit = amendment.get("pre_label_access_audit", {})
    access_log_path = project_root / "outputs" / "logs" / "reserved_access.jsonl"
    access_bytes = access_log_path.read_bytes()
    entries = [json.loads(line) for line in access_bytes.decode("utf-8").splitlines() if line.strip()]
    if any(entry.get("kind") != "eligibility_count" for entry in entries):
        raise ValueError("Reserved access log contains a label or non-eligibility access")
    if len(entries) != audit.get("reserved_access_log_entries"):
        raise ValueError("Reserved access log entry count changed after amendment sealing")
    if audit.get("label_load_entries") != 0 or audit.get("test_behavior_load_entries") != 0:
        raise ValueError("Day 2 amendment does not record a clean pre-label access audit")
    if audit.get("reserved_access_log_sha256") != _sha256(access_bytes):
        raise ValueError("Reserved access log hash differs from the pre-label audit")

    manifest_path = project_root / "data" / "restricted" / "day1_warehouse_manifest.json"
    quality_path = project_root / "outputs" / "tables" / "dev_quality_summary.json"
    manifest_bytes = manifest_path.read_bytes()
    quality_bytes = quality_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    quality = json.loads(quality_bytes)
    if manifest.get("test_labels_loaded") is not False or quality.get("test_labels_loaded") is not False:
        raise ValueError("A Day 1 development artifact reports test labels loaded")
    if audit.get("day1_warehouse_manifest_sha256") != _sha256(manifest_bytes):
        raise ValueError("Day 1 warehouse manifest differs from the pre-label evidence")
    if audit.get("dev_quality_summary_sha256") != _sha256(quality_bytes):
        raise ValueError("Development quality summary differs from the pre-label evidence")
    return amendment, amendment_hash


def load_money_adjustment_amendment(project_root: Path) -> tuple[dict[str, Any], str]:
    """Verify the superseding owner rule and prove it predates Day 2 labels."""
    config_dir = project_root / "config"
    amendment_path = config_dir / "amendment_03_money_adjustment.yaml"
    sidecar_path = config_dir / "amendment_03_money_adjustment.lock.json"
    split_lock_path = config_dir / "split.lock.json"
    amendment_01_path = config_dir / "amendment_01_analysis_start.yaml"
    amendment_02_path = config_dir / "amendment_02_money_and_gift_rules.yaml"

    amendment_bytes = amendment_path.read_bytes()
    amendment = yaml.safe_load(amendment_bytes)
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    amendment_hash = _sha256(amendment_bytes)
    split_hash = _sha256(split_lock_path.read_bytes())
    amendment_01_hash = _sha256(amendment_01_path.read_bytes())
    amendment_02_hash = _sha256(amendment_02_path.read_bytes())

    if not isinstance(amendment, dict) or amendment.get("status") != "approved_owner_decision":
        raise ValueError("Money adjustment amendment is missing or not owner-approved")
    if amendment.get("amendment_id") != 3 or amendment.get("supersedes") != amendment_02_path.name:
        raise ValueError("Money adjustment amendment identity or superseded rule is incorrect")
    if amendment.get("decision_date") != "2026-10-25":
        raise ValueError("Money adjustment decision date differs from its record")
    if sidecar.get("amendment_sha256") != amendment_hash:
        raise ValueError("Money adjustment amendment hash does not match its sidecar")
    if sidecar.get("split_lock_sha256") != split_hash:
        raise ValueError("Money adjustment sidecar points to a different split lock")
    if sidecar.get("amendment_01_sha256") != amendment_01_hash:
        raise ValueError("Money adjustment sidecar points to a different analysis-start amendment")
    if sidecar.get("amendment_02_sha256") != amendment_02_hash:
        raise ValueError("Money adjustment sidecar points to a different prior money amendment")
    hashes = amendment.get("source_hashes", {})
    if hashes != {
        "split_lock_sha256": split_hash,
        "amendment_01_sha256": amendment_01_hash,
        "amendment_02_sha256": amendment_02_hash,
    }:
        raise ValueError("Money adjustment source hashes differ from the active source files")
    if amendment.get("analysis_start") != "2024-04-01":
        raise ValueError("Money adjustment amendment uses a different analysis_start")
    if amendment.get("revenue_rule", {}).get("primary_expression") != "total_price_after_sub_discount - shipping_fee":
        raise ValueError("Primary revenue formula differs from amendment 03")
    if amendment.get("revenue_rule", {}).get("special_case_expression") != "total_price_after_sub_discount":
        raise ValueError("Special-case revenue formula differs from amendment 03")
    if amendment.get("negative_revenue_rule", {}).get("stop_if_count_share_exceeds") != 0.01:
        raise ValueError("Negative revenue stop threshold differs from amendment 03")
    if amendment.get("H_obs", {}).get("interval") != "[analysis_start, T)":
        raise ValueError("H_obs interval differs from amendment 03")

    audit = amendment.get("pre_label_access_audit", {})
    access_path = project_root / "outputs" / "logs" / "reserved_access.jsonl"
    access_bytes = access_path.read_bytes()
    entries = [json.loads(line) for line in access_bytes.decode("utf-8").splitlines() if line.strip()]
    if any(entry.get("kind") != "eligibility_count" for entry in entries):
        raise ValueError("Reserved access log contains a label or non-eligibility access")
    if len(entries) != audit.get("reserved_access_log_entries"):
        raise ValueError("Reserved access log changed after amendment 03 was sealed")
    if audit.get("label_load_entries") != 0 or audit.get("test_behavior_load_entries") != 0:
        raise ValueError("Amendment 03 does not record a clean pre-label access audit")
    if audit.get("reserved_access_log_sha256") != _sha256(access_bytes):
        raise ValueError("Reserved access log hash differs from amendment 03 evidence")

    manifest_path = project_root / "data" / "restricted" / "day1_warehouse_manifest.json"
    quality_path = project_root / "outputs" / "tables" / "dev_quality_summary.json"
    manifest_bytes = manifest_path.read_bytes()
    quality_bytes = quality_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    quality = json.loads(quality_bytes)
    if manifest.get("test_labels_loaded") is not False or quality.get("test_labels_loaded") is not False:
        raise ValueError("A Day 1 artifact reports test labels loaded")
    if audit.get("day1_warehouse_manifest_sha256") != _sha256(manifest_bytes):
        raise ValueError("Warehouse manifest differs from amendment 03 pre-label evidence")
    if audit.get("dev_quality_summary_sha256") != _sha256(quality_bytes):
        raise ValueError("Development quality summary differs from amendment 03 pre-label evidence")
    if amendment.get("decision_precedes_day2_label_generation_and_modeling") is not True:
        raise ValueError("Money adjustment decision is not declared before Day 2 labels/models")
    return amendment, amendment_hash
