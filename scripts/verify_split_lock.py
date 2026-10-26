"""Verify the immutable split config and snapshot manifest hashes."""

from __future__ import annotations

from datetime import date, timedelta
import csv
import hashlib
import json
from pathlib import Path
import sys

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ingest.analysis_amendment import load_analysis_amendment
from ingest.decision_amendment import load_decision_amendment, load_money_adjustment_amendment


def verify() -> tuple[dict, str, str, str]:
    config_path = PROJECT_ROOT / "config" / "split.yaml"
    lock_path = PROJECT_ROOT / "config" / "split.lock.json"
    config_bytes = config_path.read_bytes()
    config = yaml.safe_load(config_bytes)
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    config_hash = hashlib.sha256(config_bytes).hexdigest()
    if config.get("status") != "locked" or config_hash != lock.get("config_sha256"):
        raise ValueError("split.yaml hash does not match its lock sidecar")
    if config.get("snapshot_id") != lock.get("snapshot_id"):
        raise ValueError("snapshot ID differs between config and lock")

    manifest_path = PROJECT_ROOT / "data" / "raw" / "pancake_orders" / config["snapshot_id"] / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    if (
        manifest_hash != lock.get("snapshot_manifest_sha256")
        or manifest_hash != config.get("snapshot_manifest_sha256")
    ):
        raise ValueError("snapshot manifest hash differs from the locked hash")
    if manifest.get("status") != "complete" or manifest.get("snapshot_id") != config["snapshot_id"]:
        raise ValueError("locked snapshot is incomplete or has a mismatched ID")
    amendment, amendment_hash, _ = load_analysis_amendment(PROJECT_ROOT)
    if amendment.get("analysis_start") != "2024-04-01":
        raise ValueError("analysis-start amendment differs from the owner's approved date")
    decision_amendment, decision_hash = load_decision_amendment(PROJECT_ROOT)
    if decision_amendment.get("source_hashes", {}).get("split_lock_sha256") != hashlib.sha256(lock_path.read_bytes()).hexdigest():
        raise ValueError("Day 2 amendment differs from the active split lock")
    money_amendment, money_hash = load_money_adjustment_amendment(PROJECT_ROOT)
    if money_amendment.get("source_hashes", {}).get("split_lock_sha256") != hashlib.sha256(lock_path.read_bytes()).hexdigest():
        raise ValueError("Active money amendment differs from the locked split")

    followup_path = PROJECT_ROOT / "config" / "amendment_04_followup.yaml"
    followup_lock_path = PROJECT_ROOT / "config" / "amendment_04_followup.lock.json"
    if followup_path.exists() or followup_lock_path.exists():
        if not followup_path.is_file() or not followup_lock_path.is_file():
            raise ValueError("Day 2B amendment or lock sidecar is missing")
        followup_bytes = followup_path.read_bytes()
        followup = yaml.safe_load(followup_bytes)
        followup_lock = json.loads(followup_lock_path.read_text(encoding="utf-8"))
        followup_hash = hashlib.sha256(followup_bytes).hexdigest()
        expected_hashes = {
            "split_lock_sha256": hashlib.sha256(lock_path.read_bytes()).hexdigest(),
            "amendment_01_sha256": hashlib.sha256((PROJECT_ROOT / "config" / "amendment_01_analysis_start.yaml").read_bytes()).hexdigest(),
            "amendment_02_sha256": hashlib.sha256((PROJECT_ROOT / "config" / "amendment_02_money_and_gift_rules.yaml").read_bytes()).hexdigest(),
            "amendment_03_sha256": hashlib.sha256((PROJECT_ROOT / "config" / "amendment_03_money_adjustment.yaml").read_bytes()).hexdigest(),
        }
        if followup_hash != followup_lock.get("amendment_sha256") or followup.get("source_hashes") != expected_hashes:
            raise ValueError("Day 2B amendment hash or source hashes do not match")
        if followup_lock.get("snapshot_id") != config.get("snapshot_id"):
            raise ValueError("Day 2B amendment is for a different locked snapshot")
        if followup.get("test_policy", {}).get("test_remains_closed") is not True:
            raise ValueError("Day 2B amendment does not keep test closed")
        if followup.get("test_policy", {}).get("recorded_reserved_label_reads") != 0 or followup.get("test_policy", {}).get("recorded_reserved_behavior_reads") != 0:
            raise ValueError("Day 2B preregistration records a reserved test read")
    else:
        followup_hash = "not registered"

    cutoff = date.fromisoformat(str(config["data_cutoff"]))
    test_start = date.fromisoformat(str(config["test_start"]))
    test_end = date.fromisoformat(str(config["test_end_exclusive"]))
    n_days = int(config["primary_n_days"])
    l_days = int(config["l_candidates_days"][0])
    w_days = int(config["window_days"])
    expected_end = cutoff - timedelta(days=n_days + l_days)
    expected_start = expected_end - timedelta(days=w_days)
    if (test_start, test_end) != (expected_start, expected_end):
        raise ValueError("primary test dates do not match locked N/L/W and data cutoff")
    if (n_days, l_days, w_days) != (180, 7, 180):
        raise ValueError("primary plan differs from owner-selected N=180, L=7, W=180")

    eligibility_path = PROJECT_ROOT / "outputs" / "tables" / "eligibility_preflight.csv"
    with eligibility_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    primary = next((row for row in rows if row.get("candidate") == "N180"), None)
    if not primary or primary.get("test_start") != test_start.isoformat():
        raise ValueError("N=180 eligibility preflight is missing or uses another test_start")
    if int(primary["eligible_customers"]) < int(config["min_test_eligible_customers"]):
        raise ValueError("N=180 eligibility cohort is below the configured minimum")
    return config, config_hash, decision_hash, money_hash, followup_hash


def main() -> int:
    try:
        config, config_hash, decision_hash, money_hash, followup_hash = verify()
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError, yaml.YAMLError) as exc:
        print(f"Split lock verification failed ({type(exc).__name__}).")
        return 1
    print(f"Split lock verified: {config_hash}")
    amendment, amendment_hash, _ = load_analysis_amendment(PROJECT_ROOT)
    print(f"Analysis-start amendment verified: {amendment_hash}; effective from {amendment['analysis_start']}.")
    print(f"Historical amendment 02 verified: {decision_hash}.")
    print(f"Active amendment 03 verified: {money_hash}; pre-label access audit is clean.")
    print(f"Amendment 04 follow-up: {followup_hash}.")
    print(f"Snapshot verified: {config['snapshot_id']}; test={config['test_start']} to {config['test_end_exclusive']} exclusive.")
    opened_lock = PROJECT_ROOT / "outputs" / "metrics" / "test_opened.lock.json"
    if opened_lock.exists():
        try:
            opened = json.loads(opened_lock.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            print(f"Test-open lock could not be read ({type(exc).__name__}).")
            return 1
        if opened.get("test_open_count") != 1 or opened.get("status") != "opened_once":
            print("Test-open lock does not record exactly one authorized opening.")
            return 1
        print("N=180 eligibility gate passed; test was opened once under its locked configuration.")
    else:
        print("N=180 eligibility gate passed; test labels were not loaded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
