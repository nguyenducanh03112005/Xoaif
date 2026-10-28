"""Create a safe local replay snapshot; live incremental refresh is not verified."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = PROJECT_ROOT / "data" / "raw" / "pancake_orders"
LIVE_REFRESH_BLOCKER = (
    "Live refresh blocked: this repository does not verify the GET /orders "
    "updated_at window parameter names or semantics. No API request was made."
)
_PAGE_NAME = re.compile(r"page_[0-9]{6}\.json\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_LOCKED_SNAPSHOT_ID = "20261024T052943Z"


class SnapshotError(ValueError):
    """Raised when a source snapshot cannot be safely replayed."""


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _read_manifest(source_dir: Path) -> tuple[dict[str, Any], bytes]:
    manifest_path = source_dir / "manifest.json"
    if manifest_path.is_symlink():
        raise SnapshotError("Source manifest must be a regular local file.")
    try:
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise SnapshotError("Source manifest is missing or invalid.") from None
    if not isinstance(manifest, dict):
        raise SnapshotError("Source manifest is missing or invalid.")
    if (
        manifest.get("snapshot_id") != source_dir.name
        or manifest.get("source") != "pancake_pos"
        or manifest.get("status") != "complete"
        or manifest.get("is_replay") is True
        or manifest.get("mode") == "replay"
    ):
        raise SnapshotError("Source must be a complete, original local Pancake snapshot.")
    return manifest, manifest_bytes


def _validate_source(source_dir: Path) -> tuple[dict[str, Any], bytes]:
    raw_root = RAW_ROOT.resolve()
    resolved_source = source_dir.resolve()
    if resolved_source == raw_root or raw_root not in resolved_source.parents:
        raise SnapshotError("Replay source must be inside the local Pancake snapshot folder.")
    if not resolved_source.is_dir() or source_dir.is_symlink():
        raise SnapshotError("Replay source must be a local snapshot directory.")

    manifest, manifest_bytes = _read_manifest(resolved_source)
    pages = manifest.get("pages")
    if not isinstance(pages, list) or not pages:
        raise SnapshotError("Source manifest does not contain a valid page list.")

    seen_names: set[str] = set()
    counted_rows = 0
    for page in pages:
        if not isinstance(page, dict):
            raise SnapshotError("Source manifest contains invalid page metadata.")
        name = page.get("file")
        digest = page.get("sha256")
        rows = page.get("rows")
        if (
            not isinstance(name, str)
            or not _PAGE_NAME.fullmatch(name)
            or name in seen_names
            or not isinstance(digest, str)
            or not _SHA256.fullmatch(digest)
            or isinstance(rows, bool)
            or not isinstance(rows, int)
            or rows < 0
        ):
            raise SnapshotError("Source manifest contains invalid page metadata.")
        seen_names.add(name)
        page_path = resolved_source / name
        if page_path.is_symlink() or not page_path.is_file():
            raise SnapshotError("A source page is missing or unreadable.")
        try:
            page_bytes = page_path.read_bytes()
        except OSError:
            raise SnapshotError("A source page is missing or unreadable.") from None
        if sha256_bytes(page_bytes) != digest:
            raise SnapshotError("A source page failed its SHA-256 check.")
        try:
            payload = json.loads(page_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise SnapshotError("A source page is not valid JSON.") from None
        if not isinstance(payload, dict) or not isinstance(payload.get("data"), list):
            raise SnapshotError("A source page has an invalid response shape.")
        if len(payload["data"]) != rows:
            raise SnapshotError("A source page row count does not match its manifest.")
        counted_rows += rows

    row_count = manifest.get("row_count")
    if isinstance(row_count, bool) or not isinstance(row_count, int) or row_count != counted_rows:
        raise SnapshotError("Source row count does not match its manifest pages.")
    expected_files = seen_names | {"manifest.json"}
    actual_entries = list(resolved_source.iterdir())
    if any(item.is_symlink() or not item.is_file() for item in actual_entries):
        raise SnapshotError("Source snapshot contains unexpected files.")
    if {item.name for item in actual_entries} != expected_files:
        raise SnapshotError("Source snapshot contains unexpected or missing files.")
    return manifest, manifest_bytes


def _build_replay_manifest(
    source_manifest: dict[str, Any],
    *,
    snapshot_id: str,
    source_manifest_sha256: str,
    started_at: str,
) -> dict[str, Any]:
    pages = source_manifest["pages"]
    row_count = source_manifest["row_count"]
    return {
        "format_version": source_manifest.get("format_version", 1),
        "snapshot_id": snapshot_id,
        "source": "pancake_pos",
        "shop_id": source_manifest.get("shop_id"),
        "endpoint": "GET /shops/{SHOP_ID}/orders",
        "filters": source_manifest.get("filters"),
        "pagination": source_manifest.get("pagination"),
        "started_at_utc": started_at,
        "finished_at_utc": started_at,
        "status": "complete",
        "mode": "replay",
        "is_replay": True,
        "replay": {
            "source_snapshot_id": source_manifest["snapshot_id"],
            "source_manifest_sha256": source_manifest_sha256,
            "note": (
                "Local replay of an existing Pancake snapshot; no API request was made. "
                "This is not newly refreshed data."
            ),
        },
        "pages": pages,
        "row_count": row_count,
        "integrity": {
            "source_page_hashes_verified": True,
            "row_count_matches_source_manifest": True,
        },
    }


def _write_atomic(path: Path, content: bytes) -> None:
    temporary_path = path.with_name(f".{path.name}.{os.getpid()}.writing")
    try:
        with temporary_path.open("xb") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary_path, path)
    finally:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def replay_snapshot(
    source_dir: Path,
    *,
    output_root: Path = RAW_ROOT,
    now: datetime | None = None,
) -> tuple[str, int, int]:
    """Atomically copy a verified real snapshot to a new, replay-marked snapshot."""
    source_manifest, source_manifest_bytes = _validate_source(source_dir)
    timestamp = now or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        raise SnapshotError("Snapshot timestamp must include a timezone.")
    snapshot_id = timestamp.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination_root = output_root.resolve()
    if destination_root != RAW_ROOT.resolve():
        raise SnapshotError("Output must remain in the ignored local Pancake snapshot folder.")
    final_dir = destination_root / snapshot_id
    staging_dir = destination_root / f".{snapshot_id}.{os.getpid()}.staging"
    if snapshot_id == _LOCKED_SNAPSHOT_ID or final_dir.exists() or staging_dir.exists():
        raise SnapshotError("New snapshot ID already exists; no files were changed.")

    destination_root.mkdir(parents=True, exist_ok=True)
    try:
        staging_dir.mkdir(exist_ok=False)
        for page in source_manifest["pages"]:
            name = page["file"]
            _write_atomic(staging_dir / name, (source_dir.resolve() / name).read_bytes())

        manifest = _build_replay_manifest(
            source_manifest,
            snapshot_id=snapshot_id,
            source_manifest_sha256=sha256_bytes(source_manifest_bytes),
            started_at=timestamp.astimezone(timezone.utc).isoformat(),
        )
        manifest_bytes = json.dumps(
            manifest,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        _write_atomic(staging_dir / "manifest.json", manifest_bytes)
        os.rename(staging_dir, final_dir)
    except (OSError, SnapshotError):
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise

    return snapshot_id, len(source_manifest["pages"]), source_manifest["row_count"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--replay",
        metavar="SNAPSHOT_DIR",
        help="Create a replay-marked snapshot from an existing real local snapshot.",
    )
    args = parser.parse_args(argv)
    if not args.replay:
        print(LIVE_REFRESH_BLOCKER)
        return 2

    try:
        snapshot_id, page_count, row_count = replay_snapshot(Path(args.replay))
    except (OSError, SnapshotError) as exc:
        print(f"Replay not created ({type(exc).__name__}); source was not modified.")
        return 1

    print(f"Replay snapshot complete: {snapshot_id}")
    print(f"Mode: replay; pages: {page_count}; order records: {row_count}")
    print(f"Local restricted path: data/raw/pancake_orders/{snapshot_id}")
    print("No API request was made; no order/customer field values were printed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
