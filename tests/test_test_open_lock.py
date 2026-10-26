from __future__ import annotations

import json
from pathlib import Path

import pytest

from ingest.test_open_lock import TestAlreadyOpenedError, create_test_open_lock


HASH_A = "a" * 64
HASH_B = "b" * 64


def test_test_open_lock_is_exclusive_and_blocks_a_second_run(tmp_path: Path):
    path = tmp_path / "test_opened.lock.json"
    payload = create_test_open_lock(
        path,
        split_sha256=HASH_A,
        test_open_config_sha256=HASH_B,
        input_hashes={"model.joblib": "c" * 64},
    )
    assert payload["test_open_count"] == 1
    assert payload["input_hashes"] == {"model.joblib": "c" * 64}
    assert json.loads(path.read_text(encoding="utf-8"))["status"] == "opened_once"
    with pytest.raises(TestAlreadyOpenedError, match="already been opened"):
        create_test_open_lock(
            path,
            split_sha256=HASH_A,
            test_open_config_sha256=HASH_B,
            input_hashes={"model.joblib": "c" * 64},
        )


def test_test_open_lock_rejects_non_sha256_inputs(tmp_path: Path):
    with pytest.raises(ValueError, match="SHA-256"):
        create_test_open_lock(
            tmp_path / "lock.json",
            split_sha256="bad",
            test_open_config_sha256=HASH_B,
            input_hashes={"model.joblib": "c" * 64},
        )
