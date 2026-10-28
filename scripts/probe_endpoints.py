"""Emit metadata-only aggregates for the approved Pancake GET endpoints."""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime
import json
import math
from pathlib import Path
import re
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ingest.client import PancakeAPIError, PancakeClient
from ingest.identifiers import pseudonymize_id
from ingest.settings import load_analytics_hmac_key, load_settings

PAGE_SIZE = 50
MAX_SAMPLE_RECORDS = 500
ENDPOINTS = (
    {
        "name": "products_variations",
        "path": "/shops/{shop_id}/products/variations",
        "page_param": "page_number",
        "join_key": "product_id",
        "namespace": "xoaif/product/v1",
        "date_fields": ("inserted_at", "created_at", "updated_at"),
    },
    {
        "name": "customers",
        "path": "/shops/{shop_id}/customers",
        "page_param": "page_number",
        "join_key": "customer_id",
        "join_key_candidates": ("customer_id", "id"),
        "namespace": "xoaif/customer/v1",
        "date_fields": ("inserted_at", "updated_at", "last_order_at"),
    },
    {
        "name": "shopee_evaluate",
        "path": "/shops/{shop_id}/shopee/evaluate",
        "page_param": "page",
        "join_key": "order_id",
        "namespace": "xoaif/order/v1",
        "date_fields": ("create_at", "created_at", "evaluation_time"),
        "ratings": True,
    },
    {
        "name": "ads_manager_ad_accounts",
        "path": "/shops/{shop_id}/ads_manager/ad_accounts",
        "page_param": "page",
        "join_key": None,
        "namespace": None,
        "date_fields": ("sync_succeed_at", "created_at", "updated_at"),
    },
    {
        "name": "ads_manager_campaigns",
        "path": "/shops/{shop_id}/ads_manager/campaigns_v2",
        "page_param": "page",
        "join_key": None,
        "namespace": None,
        "date_fields": ("created_at", "updated_at", "start_time", "end_time"),
    },
)
_ISO_DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}")


def _dev_keys(db_path: Path, *, key: bytes) -> dict[str, set[str]]:
    import duckdb

    connection = duckdb.connect(str(db_path), read_only=True)
    try:
        orders = {
            row[0]
            for row in connection.execute(
                """
                SELECT order_key FROM fact_orders
                WHERE status_code = 3
                  AND local_date >= DATE '2024-04-01'
                  AND local_date < DATE '2025-10-22'
                """
            ).fetchall()
        }
        customers = {
            row[0]
            for row in connection.execute(
                """
                SELECT DISTINCT customer_key FROM fact_orders
                WHERE status_code = 3
                  AND customer_key IS NOT NULL
                  AND local_date >= DATE '2024-04-01'
                  AND local_date < DATE '2025-10-22'
                """
            ).fetchall()
        }
        products = {
            row[0]
            for row in connection.execute(
                """
                SELECT DISTINCT i.product_key
                FROM fact_order_items AS i
                JOIN fact_orders AS o USING (order_key)
                WHERE o.status_code = 3
                  AND o.local_date >= DATE '2024-04-01'
                  AND o.local_date < DATE '2025-10-22'
                """
            ).fetchall()
        }
    finally:
        connection.close()
    return {"order_id": orders, "customer_id": customers, "product_id": products}


def _value_type(value: Any) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return "null"


def _top_level_fields(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return {str(name): child for name, child in value.items()}
    return {}


def _summarize_fields(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    observed: dict[str, dict[str, Any]] = {}
    for record in records:
        for name, value in _top_level_fields(record).items():
            item = observed.setdefault(name, {"types": set(), "non_null": 0})
            if value is not None:
                item["types"].add(_value_type(value))
                item["non_null"] += 1
            else:
                item["types"].add("null")
    return [
        {
            "field": name,
            "types": sorted(values["types"]),
            "non_null_count": values["non_null"],
            "non_null_rate": round(values["non_null"] / len(records), 6),
        }
        for name, values in sorted(observed.items())
    ] if records else []


def _parse_date(value: Any) -> date | None:
    if not isinstance(value, str) or not _ISO_DATE_PREFIX.match(value):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None


def _date_range(records: list[dict[str, Any]], field_names: tuple[str, ...]) -> dict[str, str | None]:
    candidates: list[date] = []
    for record in records:
        fields = _top_level_fields(record)
        for field in field_names:
            candidates.extend(
                parsed
                for name, value in fields.items()
                if name.rsplit(".", 1)[-1] == field
                if (parsed := _parse_date(value)) is not None
            )
    return {
        "min": min(candidates).isoformat() if candidates else None,
        "max": max(candidates).isoformat() if candidates else None,
    }


def _record_keys(
    record: dict[str, Any],
    *,
    field_name: str,
    namespace: str,
    hmac_key: bytes,
) -> set[str]:
    keys: set[str] = set()
    for name, value in _top_level_fields(record).items():
        if name == field_name and isinstance(value, (str, int)):
            keys.add(pseudonymize_id(value, key=hmac_key, namespace=namespace))
    return keys


def aggregate_records(
    records: list[dict[str, Any]],
    endpoint: dict[str, Any],
    *,
    hmac_key: bytes,
    dev_keys: dict[str, set[str]],
) -> dict[str, Any]:
    sampled = records[:MAX_SAMPLE_RECORDS]
    join_key = endpoint["join_key"]
    namespace = endpoint["namespace"]
    key_results: dict[str, dict[str, int | float | None]] = {}
    if join_key and namespace:
        keys = dev_keys[join_key]
        for candidate in endpoint.get("join_key_candidates", (join_key,)):
            matched_count = sum(
                bool(
                    _record_keys(
                        record,
                        field_name=candidate,
                        namespace=namespace,
                        hmac_key=hmac_key,
                    )
                    & keys
                )
                for record in sampled
            )
            key_results[candidate] = {
                "dev_matched_records": matched_count,
                "dev_match_rate": round(matched_count / len(sampled), 6) if sampled else None,
            }
        primary_result = key_results[join_key]
    else:
        primary_result = {"dev_matched_records": None, "dev_match_rate": None}

    summary: dict[str, Any] = {
        "sampled_records": len(sampled),
        "join_key": join_key,
        "dev_matched_records": primary_result["dev_matched_records"],
        "dev_match_rate": primary_result["dev_match_rate"],
        "date_range": _date_range(sampled, endpoint["date_fields"]),
        "fields": _summarize_fields(sampled),
    }
    if len(key_results) > 1:
        summary["alternate_join_key_results"] = {
            candidate: value
            for candidate, value in key_results.items()
            if candidate != join_key
        }
    if endpoint.get("ratings"):
        counts = Counter(
            str(record["rating"])
            for record in sampled
            if isinstance(record.get("rating"), int)
            and not isinstance(record.get("rating"), bool)
            and 1 <= record["rating"] <= 5
        )
        summary["rating_distribution"] = {
            str(rating): counts[str(rating)] for rating in range(1, 6)
        }
    return summary


def _records_and_total(payload: Any) -> tuple[list[dict[str, Any]], int | None]:
    if not isinstance(payload, dict):
        return [], None
    records = payload.get("data")
    total = payload.get("total_entries")
    if not isinstance(records, list):
        records = []
    safe_records = [record for record in records if isinstance(record, dict)]
    safe_total = total if isinstance(total, int) and not isinstance(total, bool) else None
    return safe_records, safe_total


def probe_endpoint(
    client: PancakeClient,
    endpoint: dict[str, Any],
    *,
    shop_id: str,
    hmac_key: bytes,
    dev_keys: dict[str, set[str]],
) -> dict[str, Any]:
    path = endpoint["path"].format(shop_id=shop_id)
    records: list[dict[str, Any]] = []
    total_entries: int | None = None
    http_status: int | None = None
    error_class: str | None = None
    first_page: Any = None
    page_records: list[dict[str, Any]] = []
    payload: Any = None
    try:
        first_page, http_status = client.request_with_status(
            "GET",
            path,
            params={"page_size": PAGE_SIZE, endpoint["page_param"]: 1},
        )
        page_records, total_entries = _records_and_total(first_page)
        records.extend(page_records[:MAX_SAMPLE_RECORDS])
        if total_entries == 0:
            page_numbers: list[int] = []
        elif total_entries is not None:
            page_count = (total_entries + PAGE_SIZE - 1) // PAGE_SIZE
            sample_page_count = min(MAX_SAMPLE_RECORDS // PAGE_SIZE, page_count)
            page_numbers = sorted(
                {
                    1 + round(index * (page_count - 1) / max(sample_page_count - 1, 1))
                    for index in range(sample_page_count)
                }
            )
        else:
            page_numbers = list(range(1, MAX_SAMPLE_RECORDS // PAGE_SIZE + 1))

        for page in page_numbers:
            if page == 1:
                continue
            payload, http_status = client.request_with_status(
                "GET",
                path,
                params={"page_size": PAGE_SIZE, endpoint["page_param"]: page},
            )
            page_records, _ = _records_and_total(payload)
            records.extend(page_records[: MAX_SAMPLE_RECORDS - len(records)])
            if not page_records or len(records) >= MAX_SAMPLE_RECORDS:
                break
    except PancakeAPIError as exc:
        http_status = exc.status_code
        error_class = type(exc).__name__
    except Exception as exc:
        error_class = type(exc).__name__

    result: dict[str, Any] = {
        "endpoint": endpoint["name"],
        "method": "GET",
        "path": endpoint["path"].replace("{shop_id}", "{SHOP_ID}"),
        "http_status": http_status,
        "total_entries": total_entries,
        "status": (
            "ok"
            if http_status is not None and 200 <= http_status < 300
            else "unavailable"
        ),
        "sample_method": "spread_pages",
    }
    if error_class:
        result["error_class"] = error_class
    if http_status in (401, 403, 404) or total_entries == 0:
        result["status"] = "skipped"
        result["sampled_records"] = 0
        result["join_key"] = endpoint["join_key"]
        result["dev_matched_records"] = 0 if endpoint["join_key"] else None
        result["dev_match_rate"] = None
        result["date_range"] = {"min": None, "max": None}
        result["fields"] = []
        if endpoint.get("ratings"):
            result["rating_distribution"] = {str(rating): 0 for rating in range(1, 6)}
        records.clear()
        first_page = None
        payload = None
        page_records.clear()
        return result
    aggregate = aggregate_records(
        records,
        endpoint,
        hmac_key=hmac_key,
        dev_keys=dev_keys,
    )
    records.clear()
    page_records.clear()
    first_page = None
    payload = None
    result.update(aggregate)
    return result


def main() -> int:
    try:
        settings = load_settings(PROJECT_ROOT / "xoaif.env")
        hmac_key = load_analytics_hmac_key(PROJECT_ROOT / "xoaif.env")
        dev_keys = _dev_keys(
            PROJECT_ROOT / "data" / "restricted" / "xoaif_dev.duckdb",
            key=hmac_key,
        )
    except Exception as exc:
        print(
            json.dumps(
                {"status": "preflight_error", "error_class": type(exc).__name__},
                separators=(",", ":"),
            )
        )
        return 2

    client = PancakeClient(settings)
    results = [
        probe_endpoint(
            client,
            endpoint,
            shop_id=settings.shop_id,
            hmac_key=hmac_key,
            dev_keys=dev_keys,
        )
        for endpoint in ENDPOINTS
    ]
    print(
        json.dumps(
            {
                "sample_limit": MAX_SAMPLE_RECORDS,
                "sample_method": "spread_pages",
                "field_depth": "top_level_only",
                "dev_match_scope": "status3 local_date [2024-04-01,2025-10-22)",
                "endpoints": results,
            },
            ensure_ascii=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
