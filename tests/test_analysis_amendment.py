import hashlib
import json
from pathlib import Path

import pytest

from ingest.analysis_amendment import load_analysis_amendment


def _make_project(root: Path, *, label_load: bool = False) -> Path:
    config = root / "config"
    logs = root / "outputs" / "logs"
    config.mkdir(parents=True)
    logs.mkdir(parents=True)
    split_yaml = b"status: locked\ntimezone: Asia/Ho_Chi_Minh\ntest_start: 2025-10-22\ntest_end_exclusive: 2026-04-20\nprimary_n_days: 180\nl_candidates_days: [7]\nwindow_days: 180\n"
    split = {"config_sha256": hashlib.sha256(split_yaml).hexdigest()}
    (config / "split.yaml").write_bytes(split_yaml)
    split_bytes = json.dumps(split, indent=2).encode() + b"\n"
    (config / "split.lock.json").write_bytes(split_bytes)
    split_lock_hash = hashlib.sha256(split_bytes).hexdigest()
    amendment = (
        "status: approved_owner_decision\n"
        'decision_date: "2026-10-25"\n'
        'analysis_start: "2024-04-01"\n'
        "timezone: Asia/Ho_Chi_Minh\n"
        f"split_lock_sha256: {split_lock_hash}\n"
        "split_dates_unchanged:\n"
        '  test_start: "2025-10-22"\n'
        '  test_end_exclusive: "2026-04-20"\n'
        "  N_days: 180\n  L_days: 7\n  W_days: 180\n"
        "decision_precedes_test_open_and_label_access: true\n"
    ).encode()
    (config / "amendment_01_analysis_start.yaml").write_bytes(amendment)
    amendment_hash = hashlib.sha256(amendment).hexdigest()
    (config / "amendment_01_analysis_start.lock.json").write_text(
        json.dumps({"amendment_sha256": amendment_hash, "split_lock_sha256": split_lock_hash}),
        encoding="utf-8",
    )
    if label_load:
        (logs / "reserved_access.jsonl").write_text('{"kind":"label_load"}\n', encoding="utf-8")
    return root


def test_analysis_amendment_verifies_and_keeps_split_locked(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    amendment, amendment_hash, _ = load_analysis_amendment(root)
    assert amendment["analysis_start"] == "2024-04-01"
    assert len(amendment_hash) == 64


def test_analysis_amendment_rejects_changed_yaml_hash(tmp_path: Path) -> None:
    root = _make_project(tmp_path)
    path = root / "config" / "amendment_01_analysis_start.yaml"
    path.write_text(path.read_text(encoding="utf-8") + "# changed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="hash"):
        load_analysis_amendment(root)


def test_analysis_amendment_rejects_any_recorded_test_label_access(tmp_path: Path) -> None:
    root = _make_project(tmp_path, label_load=True)
    with pytest.raises(ValueError, match="test-label access"):
        load_analysis_amendment(root)
