"""Verify test-open evidence and frozen Day 3 outputs without reading raw orders."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify() -> None:
    config_path = ROOT / "config" / "amendment_05_test_open.yaml"
    sidecar_path = ROOT / "config" / "amendment_05_test_open.lock.json"
    if not config_path.is_file() or not sidecar_path.is_file():
        raise ValueError("Test-open configuration or sidecar is missing")
    config = yaml.safe_load(config_path.read_bytes())
    sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    if digest(config_path) != sidecar.get("config_sha256"):
        raise ValueError("Test-open configuration hash mismatch")
    freeze_path = ROOT / "outputs" / "metrics" / "day3_pretest_freeze.json"
    if digest(freeze_path) != sidecar.get("frozen_manifest_sha256"):
        raise ValueError("Pre-test freeze manifest changed")

    opened = ROOT / "outputs" / "metrics" / "test_opened.lock.json"
    if not opened.exists():
        if sidecar.get("test_opened_lock_absent_at_seal") is not True:
            raise ValueError("Pre-open sidecar does not attest unopened test")
        print("Day 3 locks verified; test remains unopened.")
        return
    lock = json.loads(opened.read_text(encoding="utf-8"))
    if lock.get("status") != "opened_once" or lock.get("test_open_count") != 1:
        raise ValueError("Test-open lock does not record exactly one opening")
    if lock.get("test_open_config_sha256") != sidecar.get("config_sha256"):
        raise ValueError("Opened lock refers to another test configuration")
    split_hash = digest(ROOT / "config" / "split.yaml")
    if lock.get("split_sha256") != split_hash:
        raise ValueError("Opened lock refers to another locked split")
    for relative, expected in lock.get("input_hashes", {}).items():
        if digest(ROOT / relative) != expected:
            raise ValueError(f"Frozen test input changed after opening: {relative}")

    access_path = ROOT / "outputs" / "logs" / "test_eval_access.jsonl"
    events = [json.loads(line) for line in access_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if [event.get("kind") for event in events] != ["label_load", "behavior_load"]:
        raise ValueError("Post-open access log does not contain exactly the two registered access types")
    if any(event.get("evaluation_run") != 1 or event.get("values_or_identifiers_logged") is not False for event in events):
        raise ValueError("Post-open access log has an unexpected run or includes values")

    result_path = ROOT / "outputs" / "metrics" / "test_eval.json"
    if not result_path.is_file():
        raise ValueError("Test-open lock exists but the single evaluation result is missing")
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if result.get("status") != "completed_single_test_open" or result.get("test_open_count") != 1:
        raise ValueError("Test result does not attest one completed evaluation")
    if result.get("access_audit", {}).get("raw_values_or_customer_identifiers_written") is not False:
        raise ValueError("Test report metrics do not attest identifier-free output")
    for relative in (
        "docs/test_report.md",
        "outputs/tables/test_segment_profiles.csv",
        "outputs/tables/test_combos_frozen.csv",
        "outputs/tables/dashboard_sales_monthly.csv",
        "outputs/tables/dashboard_sales_province.csv",
        "outputs/tables/dashboard_product_orders.csv",
        "outputs/tables/dashboard_status_counts.csv",
    ):
        if not (ROOT / relative).is_file():
            raise ValueError(f"Expected post-test output is missing: {relative}")
    print("Day 3 locks verified: exactly one test open, inputs unchanged, result and access audit present.")


if __name__ == "__main__":
    try:
        verify()
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
        print(f"Day 3 lock verification failed ({type(exc).__name__}).")
        raise SystemExit(1)
