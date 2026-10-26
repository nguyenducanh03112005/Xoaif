"""Metadata-only access logging for the reserved temporal region."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Literal

AccessKind = Literal["eligibility_count", "label_load"]


def record_reserved_access(
    path: Path,
    *,
    kind: AccessKind,
    step: str,
    split_hash: str,
    split_locked: bool,
    final_evaluation: bool = False,
) -> None:
    """Append a metadata-only access entry and allow one final label load."""
    if not split_locked or not split_hash:
        raise ValueError("Reserved data requires a locked split hash.")
    if kind == "label_load" and not final_evaluation:
        raise ValueError("Test labels may only load during final evaluation.")
    if kind == "label_load" and path.exists():
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    previous = json.loads(line)
                except json.JSONDecodeError:
                    raise ValueError(
                        "Access log is malformed; refusing to load test labels."
                    ) from None
                if previous.get("kind") == "label_load":
                    raise ValueError("Test labels have already been loaded once.")

    entry = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "step": step,
        "kind": kind,
        "split_hash": split_hash,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
