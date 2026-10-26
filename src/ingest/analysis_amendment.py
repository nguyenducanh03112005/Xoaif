"""Verify the owner-approved analysis-start amendment without changing split.yaml."""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


def load_analysis_amendment(project_root: Path) -> tuple[dict[str, Any], str, str]:
    config_dir = project_root / "config"
    amendment_path = config_dir / "amendment_01_analysis_start.yaml"
    sidecar_path = config_dir / "amendment_01_analysis_start.lock.json"
    split_lock_path = config_dir / "split.lock.json"
    split_config_path = config_dir / "split.yaml"

    amendment_bytes = amendment_path.read_bytes()
    amendment = yaml.safe_load(amendment_bytes)
    amendment_sha256 = hashlib.sha256(amendment_bytes).hexdigest()
    split_lock_bytes = split_lock_path.read_bytes()
    split_lock_sha256 = hashlib.sha256(split_lock_bytes).hexdigest()
    split_lock = json.loads(split_lock_bytes)
    split_config_bytes = split_config_path.read_bytes()
    split_config = yaml.safe_load(split_config_bytes)
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))

    if not isinstance(amendment, dict) or amendment.get("status") != "approved_owner_decision":
        raise ValueError("analysis-start amendment is missing or not an approved owner decision")
    if sidecar.get("amendment_sha256") != amendment_sha256:
        raise ValueError("analysis-start amendment hash does not match its sidecar")
    if sidecar.get("split_lock_sha256") != split_lock_sha256:
        raise ValueError("amendment sidecar points to a different split lock")
    if amendment.get("split_lock_sha256") != split_lock_sha256:
        raise ValueError("amendment does not record the current split lock hash")
    if split_lock.get("config_sha256") != hashlib.sha256(split_config_bytes).hexdigest():
        raise ValueError("split.yaml no longer matches its immutable lock")
    if amendment.get("decision_date") != "2026-10-25":
        raise ValueError("amendment decision date differs from its recorded date")
    if amendment.get("timezone") != split_config.get("timezone"):
        raise ValueError("analysis-start timezone differs from the locked analysis timezone")

    expected_split = {
        "test_start": str(split_config.get("test_start")),
        "test_end_exclusive": str(split_config.get("test_end_exclusive")),
        "N_days": split_config.get("primary_n_days"),
        "L_days": split_config.get("l_candidates_days", [None])[0],
        "W_days": split_config.get("window_days"),
    }
    if amendment.get("split_dates_unchanged") != expected_split:
        raise ValueError("amendment changes or misstates the locked test split")

    access_log = project_root / "outputs" / "logs" / "reserved_access.jsonl"
    if access_log.exists():
        for line in access_log.read_text(encoding="utf-8").splitlines():
            if line.strip() and json.loads(line).get("kind") == "label_load":
                raise ValueError("test-label access is recorded; this amendment precondition is no longer true")

    analysis_start = date.fromisoformat(str(amendment["analysis_start"]))
    test_start = date.fromisoformat(str(split_config["test_start"]))
    if analysis_start >= test_start:
        raise ValueError("analysis_start must precede test_start")
    if amendment.get("decision_precedes_test_open_and_label_access") is not True:
        raise ValueError("amendment does not declare its timing relative to test/label access")
    return amendment, amendment_sha256, split_lock_sha256
