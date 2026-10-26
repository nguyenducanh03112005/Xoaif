"""Validate local configuration without displaying secret values."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ingest.settings import load_analytics_hmac_key, load_environment, load_settings


def main() -> int:
    load_environment()
    try:
        settings = load_settings()
    except ValueError as exc:
        print(f"Configuration error: {exc}")
        return 2

    try:
        load_analytics_hmac_key()
        hmac_present = True
    except ValueError:
        hmac_present = False
    print("Pancake API key: configured")
    print("Shop ID: configured")
    print(f"API host: {settings.api_base_url}")
    print(f"Analytics HMAC key: {'configured' if hmac_present else 'not configured'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
