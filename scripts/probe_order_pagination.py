"""Probe response-derived order pagination names using a one-row query."""

from __future__ import annotations

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ingest.client import PancakeAPIError, PancakeClient
from ingest.settings import load_settings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--status",
        type=int,
        default=0,
        help="One documented order status to filter; default is 0 (new).",
    )
    parser.add_argument(
        "--all-orders",
        action="store_true",
        help="Omit the status filter while retaining the one-row page limit.",
    )
    parser.add_argument(
        "--page-size", type=int, default=1, help="Requested page size (positive integer)."
    )
    args = parser.parse_args()
    if args.page_size < 1:
        parser.error("--page-size must be positive")
    filters = None if args.all_orders else [args.status]
    try:
        settings = load_settings()
        client = PancakeClient(settings)
        first = client.list_orders(
            settings.shop_id,
            filter_status=filters,
            page_number=1,
            page_size=args.page_size,
        )
        second = client.list_orders(
            settings.shop_id,
            filter_status=filters,
            page_number=2,
            page_size=args.page_size,
        )
    except (PancakeAPIError, ValueError) as exc:
        print(f"Pagination probe failed: {exc}")
        return 1

    first_rows = first.get("data") if isinstance(first, dict) else None
    second_rows = second.get("data") if isinstance(second, dict) else None
    echoed = (
        isinstance(first, dict)
        and first.get("page_number") == 1
        and isinstance(second, dict)
        and second.get("page_number") == 2
        and isinstance(first.get("page_size"), int)
        and isinstance(second.get("page_size"), int)
    )
    bounded = (
        isinstance(first_rows, list)
        and len(first_rows) <= args.page_size
        and isinstance(second_rows, list)
        and len(second_rows) <= args.page_size
    )
    multiple_pages = isinstance(first, dict) and first.get("total_pages", 0) > 1
    requested_size_echoed = (
        isinstance(first, dict)
        and first.get("page_size") == args.page_size
        and isinstance(second, dict)
        and second.get("page_size") == args.page_size
    )
    distinct = (
        multiple_pages
        and bool(first_rows)
        and bool(second_rows)
        and first_rows[0].get("id") != second_rows[0].get("id")
    )
    print(f"Both responses echoed their requested page number and reported an effective size: {'yes' if echoed else 'no'}")
    print(f"Both responses echoed requested page_size: {'yes' if requested_size_echoed else 'no'}")
    print(f"Both returned arrays were within the requested {args.page_size}-row bound: {'yes' if bounded else 'no'}")
    print(f"The filtered result reports multiple pages: {'yes' if multiple_pages else 'no'}")
    print(f"Non-empty page 1 and page 2 contain different order IDs: {'yes' if distinct else 'no / not applicable'}")
    if not echoed or not bounded:
        print("Pagination request behavior remains unverified; do not extract all orders.")
        return 2
    print("This bounded probe completed. Full extraction still needs page integrity checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
