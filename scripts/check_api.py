"""Make one authorized, read-only request to verify Pancake connectivity."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ingest.client import PancakeAPIError, PancakeClient
from ingest.settings import load_settings


def main() -> int:
    try:
        settings = load_settings()
        client = PancakeClient(settings)
        shops = client.list_shops()
    except (PancakeAPIError, ValueError) as exc:
        print(f"Connection check failed: {exc}")
        return 1

    configured_shop_found = any(
        str(shop.get("id", "")) == settings.shop_id
        for shop in shops
        if isinstance(shop, dict)
    )
    print(f"API connection succeeded; shops visible: {len(shops)}")
    print(f"Configured shop visible: {'yes' if configured_shop_found else 'no'}")
    return 0 if configured_shop_found else 2


if __name__ == "__main__":
    sys.exit(main())
