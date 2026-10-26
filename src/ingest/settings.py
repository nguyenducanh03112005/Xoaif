"""Load local Pancake configuration without exposing secret values."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit


DEFAULT_API_BASE_URL = "https://pos.pages.fm/api/v1"


@dataclass(frozen=True)
class Settings:
    """Runtime configuration for read-only API access."""

    api_key: str
    shop_id: str
    api_base_url: str = DEFAULT_API_BASE_URL


def load_environment(env_file: Path | None = None) -> None:
    """Load xoaif.env if python-dotenv is installed; preserve existing env vars."""
    target = env_file or Path.cwd() / "xoaif.env"
    if not target.is_file():
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(dotenv_path=target, override=False)


def load_settings(env_file: Path | None = None) -> Settings:
    """Read required settings and validate the API host before sending a key."""
    load_environment(env_file)
    api_key = os.environ.get("PANCAKE_POS_API_KEY", "").strip()
    shop_id = os.environ.get("PANCAKE_POS_SHOP_ID", "").strip()
    base_url = os.environ.get("PANCAKE_POS_API_BASE_URL", DEFAULT_API_BASE_URL).strip()

    if not api_key:
        raise ValueError("PANCAKE_POS_API_KEY is missing; set it in local xoaif.env.")
    if not shop_id or not shop_id.isdigit():
        raise ValueError("PANCAKE_POS_SHOP_ID must be a numeric shop identifier.")

    parsed = urlsplit(base_url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "pos.pages.fm"
        or parsed.port not in (None, 443)
        or parsed.path.rstrip("/") != "/api/v1"
    ):
        raise ValueError("API base URL must use HTTPS on the documented Pancake POS host.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("API base URL must not contain credentials, query parameters, or fragments.")

    return Settings(api_key=api_key, shop_id=shop_id, api_base_url=base_url.rstrip("/"))


def load_analytics_hmac_key(env_file: Path | None = None) -> bytes:
    """Load the separate local pseudonymization key without exposing it."""
    load_environment(env_file)
    value = os.environ.get("ANALYTICS_HMAC_KEY", "").strip()
    key = value.encode("utf-8")
    if len(key) < 32:
        raise ValueError("ANALYTICS_HMAC_KEY must contain at least 32 bytes.")
    return key
