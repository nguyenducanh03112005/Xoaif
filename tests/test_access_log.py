import json

import pytest

from ingest.access_log import record_reserved_access


def test_test_label_load_requires_locked_split_and_final_evaluation(tmp_path) -> None:
    log = tmp_path / "access_log.jsonl"
    with pytest.raises(ValueError, match="locked split"):
        record_reserved_access(
            log,
            kind="eligibility_count",
            step="cp1",
            split_hash="",
            split_locked=False,
        )
    with pytest.raises(ValueError, match="final evaluation"):
        record_reserved_access(
            log,
            kind="label_load",
            step="eda",
            split_hash="abc",
            split_locked=True,
        )


def test_test_labels_can_be_loaded_once_and_log_contains_no_data_values(tmp_path) -> None:
    log = tmp_path / "access_log.jsonl"
    record_reserved_access(
        log,
        kind="eligibility_count",
        step="cp1",
        split_hash="abc",
        split_locked=True,
    )
    record_reserved_access(
        log,
        kind="label_load",
        step="final_evaluation",
        split_hash="abc",
        split_locked=True,
        final_evaluation=True,
    )

    with pytest.raises(ValueError, match="already been loaded"):
        record_reserved_access(
            log,
            kind="label_load",
            step="second_load",
            split_hash="abc",
            split_locked=True,
            final_evaluation=True,
        )

    entries = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert [entry["kind"] for entry in entries] == ["eligibility_count", "label_load"]
    assert all("customer_id" not in entry for entry in entries)
