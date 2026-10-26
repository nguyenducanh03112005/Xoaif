"""Inspect one filtered API response without printing or saving record values."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ingest.client import PancakeAPIError, PancakeClient
from ingest.settings import load_settings


def describe_shape(value: Any, *, depth: int = 0, max_depth: int = 2) -> None:
    """Print field names and JSON types only; never print field values."""
    if isinstance(value, dict):
        for key, item in value.items():
            print(f"{'  ' * depth}{key}: {json_type(item)}")
            if depth < max_depth and isinstance(item, dict):
                describe_shape(item, depth=depth + 1, max_depth=max_depth)
            elif depth < max_depth and isinstance(item, list) and item:
                print(f"{'  ' * (depth + 1)}first item: {json_type(item[0])}")
                if isinstance(item[0], dict):
                    describe_shape(item[0], depth=depth + 1, max_depth=max_depth)
    elif isinstance(value, list) and value and isinstance(value[0], dict):
        describe_shape(value[0], depth=depth, max_depth=max_depth)
    else:
        print(f"Response shape: {json_type(value)}")


def json_type(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "unknown"


def main() -> int:
    try:
        settings = load_settings()
        # Status 0 is the documented "new" status. This narrows the request;
        # no undocumented pagination or date parameter is guessed.
        payload = PancakeClient(settings).list_orders(
            settings.shop_id, filter_status=[0]
        )
    except (PancakeAPIError, ValueError) as exc:
        print(f"Order schema check failed: {exc}")
        return 1

    print("Filtered order response field names and value types (values omitted):")
    describe_shape(payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
