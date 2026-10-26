"""Generate a local HMAC secret once without printing or replacing API keys."""

from __future__ import annotations

import os
from pathlib import Path
import secrets
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ingest.settings import load_analytics_hmac_key, load_environment


def main() -> int:
    env_file = Path.cwd() / "xoaif.env"
    load_environment(env_file)
    try:
        load_analytics_hmac_key(env_file)
    except ValueError:
        secret = secrets.token_hex(32)
        prefix = "\n" if env_file.exists() and env_file.stat().st_size else ""
        with env_file.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(f"{prefix}ANALYTICS_HMAC_KEY={secret}\n")
        print("Generated a local analytics HMAC key in xoaif.env; value not displayed.")
        return 0

    print("A valid analytics HMAC key is already configured; no file changes made.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
