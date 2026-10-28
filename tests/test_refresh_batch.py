from __future__ import annotations

from datetime import datetime, timezone

from scripts.refresh_batch import (
    LIVE_REFRESH_BLOCKER,
    _build_replay_manifest,
    main,
)


def test_default_mode_fails_closed_without_updated_at_contract(capsys) -> None:
    assert main([]) == 2
    output = capsys.readouterr().out
    assert LIVE_REFRESH_BLOCKER in output
    assert "No API request was made" in output


def test_replay_manifest_is_explicitly_marked_and_links_source() -> None:
    source = {
        "snapshot_id": "20261024T052943Z",
        "pages": [],
        "row_count": 0,
    }

    manifest = _build_replay_manifest(
        source,
        snapshot_id="20261028T000000Z",
        source_manifest_sha256="a" * 64,
        started_at=datetime(2026, 10, 28, tzinfo=timezone.utc).isoformat(),
    )

    assert manifest["mode"] == "replay"
    assert manifest["is_replay"] is True
    assert manifest["replay"]["source_snapshot_id"] == "20261024T052943Z"
    assert manifest["replay"]["source_manifest_sha256"] == "a" * 64
    assert "no API request was made" in manifest["replay"]["note"]
    assert manifest["pages"] == []
    assert manifest["row_count"] == 0
