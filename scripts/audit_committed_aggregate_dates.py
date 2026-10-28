"""Inventory only temporal columns/keys from committed output aggregates."""
from __future__ import annotations

import csv
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TIME_NAME = re.compile(r"date|month|year|week|quarter|period|cohort|as.?of|window|cutoff|start|end|time", re.I)


def temporal_value(value: object) -> tuple[tuple[int, int, int], str] | None:
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "unknown", "test_pre_t", "test_window", "dev"}:
        return None
    match = re.fullmatch(r"(20\d{2})[-/]?(0[1-9]|1[0-2])[-/]?(0[1-9]|[12]\d|3[01])?", text)
    if match:
        year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3) or 0)
        try:
            if day:
                date(year, month, day)
            return (year, month, day), (f"{year:04d}-{month:02d}-{day:02d}" if day else f"{year:04d}-{month:02d}")
        except ValueError:
            return None
    quarter = re.fullmatch(r"(20\d{2})[- ]?[Qq]([1-4])", text)
    if quarter:
        y, q = int(quarter.group(1)), int(quarter.group(2))
        return (y, q * 3, 0), f"{y:04d}-Q{q}"
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if dt.tzinfo:
            dt = dt.astimezone(timezone.utc)
        return (dt.year, dt.month, dt.day), dt.date().isoformat()
    except ValueError:
        return None


def git_paths() -> list[Path]:
    raw = subprocess.check_output(["git", "ls-files", "-z", "outputs/tables", "outputs/metrics"])
    return [ROOT / x.decode("utf-8") for x in raw.split(b"\0") if x]


def scan_csv(path: Path) -> dict:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        header = next(csv.reader(stream), [])
    cols = [name for name in header if TIME_NAME.search(name)]
    maxima = []
    for col in cols:
        values = pd.read_csv(path, usecols=[col], dtype=str, keep_default_na=False)[col]
        parsed = [v for item in values if (v := temporal_value(item)) is not None]
        if parsed:
            maxima.append({"column": col, "max_local_date_or_period": max(parsed)[1]})
    label = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.name
    return {"path": label, "kind": "CSV aggregate", "temporal_columns": maxima}


def scan_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    maxima: dict[str, tuple[tuple[int, int, int], str]] = {}

    def visit(value: object, key_path: str = "") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                visit(child, f"{key_path}.{key}".strip("."))
        elif isinstance(value, list):
            for child in value:
                visit(child, key_path)
        elif TIME_NAME.search(key_path.split(".")[-1]):
            parsed = temporal_value(value)
            if parsed:
                prior = maxima.get(key_path)
                if prior is None or parsed[0] > prior[0]:
                    maxima[key_path] = parsed

    visit(payload)
    return {"path": path.relative_to(ROOT).as_posix(), "kind": "JSON aggregate/lock",
            "temporal_fields": [{"key": key, "max_local_date_or_period": value[1]} for key, value in sorted(maxima.items())]}


def inventory() -> list[dict]:
    rows = []
    for path in git_paths():
        if not path.is_file():
            continue
        if path.suffix.lower() == ".csv":
            rows.append(scan_csv(path))
        elif path.suffix.lower() == ".json":
            rows.append(scan_json(path))
    return rows


if __name__ == "__main__":
    print(json.dumps(inventory(), ensure_ascii=False, indent=2))
