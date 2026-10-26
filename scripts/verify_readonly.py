"""Fail the build if application code bypasses the read-only API client."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ingest.readonly_policy import scan_repository


def main() -> int:
    findings = scan_repository(PROJECT_ROOT)
    if findings:
        print("Read-only policy violations:")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("Read-only policy verified: API access is confined to the GET-only client.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
