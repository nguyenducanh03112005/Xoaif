"""Fail-closed one-time test opening lock."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re


class TestAlreadyOpenedError(RuntimeError):
    __test__ = False

    pass


def create_test_open_lock(
    path: Path,
    *,
    split_sha256: str,
    test_open_config_sha256: str,
    input_hashes: dict[str, str],
) -> dict:
    """Create the lock exclusively; the first write consumes the one opening."""
    if path.exists():
        raise TestAlreadyOpenedError("The one-time test set has already been opened.")
    digests = {"split.yaml": split_sha256, "amendment_05_test_open.yaml": test_open_config_sha256, **input_hashes}
    if not input_hashes:
        raise ValueError("test opening requires frozen input hashes")
    if any(not re.fullmatch(r"[0-9a-f]{64}", digest) for digest in digests.values()):
        raise ValueError("test opening input hashes must be SHA-256 digests")
    payload = {
        "status": "opened_once",
        "opened_at_utc": datetime.now(timezone.utc).isoformat(),
        "test_open_count": 1,
        "split_sha256": split_sha256,
        "test_open_config_sha256": test_open_config_sha256,
        "input_hashes": dict(sorted(input_hashes.items())),
        "opening_authorized_by_locked_config": True,
    }
    encoded = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise TestAlreadyOpenedError("The one-time test set has already been opened.") from None
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    return payload
