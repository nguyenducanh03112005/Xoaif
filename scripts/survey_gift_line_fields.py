"""Aggregate development-only order-line field coverage before gift-rule preregistration.

This survey never reads any order field in the reserved test interval except
``inserted_at`` for date gating. It writes aggregate schema/value coverage only.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, timezone
import hashlib
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import re
from typing import Any
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parents[1]
LOCAL_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
INTERESTING = re.compile(r"gift|bonus|free|promo|discount|price|quantity|qty|type|categor|sale|stock|status|active|publish", re.I)
SAFE_ENUM = re.compile(r"^[\w .:/+-]{1,48}$")


def _local_date(value: Any) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)
    return parsed.astimezone(LOCAL_TZ).date()


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _walk(value: Any, prefix: str = ""):
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            yield path, child
            yield from _walk(child, path)
    elif isinstance(value, list):
        for child in value:
            yield from _walk(child, prefix)


def main() -> int:
    split_path = ROOT / "config" / "split.yaml"
    split_bytes = split_path.read_bytes()
    split = yaml.safe_load(split_bytes)
    split_lock = json.loads((ROOT / "config" / "split.lock.json").read_text(encoding="utf-8"))
    amendment_01 = yaml.safe_load((ROOT / "config" / "amendment_01_analysis_start.yaml").read_bytes())
    snapshot = ROOT / "data" / "raw" / "pancake_orders" / str(split["snapshot_id"])
    manifest_bytes = (snapshot / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    if hashlib.sha256(split_bytes).hexdigest() != split_lock.get("config_sha256"):
        raise ValueError("split lock mismatch")
    if hashlib.sha256(manifest_bytes).hexdigest() != split.get("snapshot_manifest_sha256"):
        raise ValueError("snapshot manifest mismatch")

    start = date.fromisoformat(str(amendment_01["analysis_start"]))
    test_start = date.fromisoformat(str(split["test_start"]))
    fields: dict[str, Counter[str]] = {}
    all_line_fields: dict[str, Counter[str]] = {}
    enum_values: dict[str, Counter[str]] = {}
    numeric_stats: dict[str, dict[str, int | float | None]] = {}
    orders = 0
    lines = 0
    max_lines_per_order = 0
    products = 0
    category_values: Counter[str] = Counter()
    line_semantics: Counter[str] = Counter()
    order_discount_values: Counter[str] = Counter()
    total_rows = 0

    for page_no, page in enumerate(manifest["pages"], start=1):
        page_path = (snapshot / str(page["file"])).resolve()
        if not page_path.is_relative_to(snapshot.resolve()):
            raise ValueError("manifest page escaped snapshot")
        raw = page_path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != page.get("sha256"):
            raise ValueError("snapshot page checksum mismatch")
        payload = json.loads(raw)
        if payload.get("page_number") != page_no:
            raise ValueError("snapshot page number mismatch")
        rows = payload.get("data")
        if not isinstance(rows, list) or len(rows) != page.get("rows"):
            raise ValueError("snapshot page row count mismatch")
        for order in rows:
            total_rows += 1
            if not isinstance(order, dict):
                continue
            # Timestamp is the sole field read until the row is proven to be dev.
            day = _local_date(order.get("inserted_at"))
            if day is None or day < start or day >= test_start:
                continue
            if order.get("status") not in (3, "3"):
                continue
            orders += 1
            try:
                order_discount = Decimal(str(order.get("total_discount", 0) or 0))
            except InvalidOperation:
                order_discount = Decimal(0)
            order_discount_values["zero" if order_discount == 0 else "nonzero"] += 1
            line_semantics["orders_with_positive_total_discount"] += int(order_discount > 0)
            order_line_count = 0
            item_rows = order.get("items")
            if not isinstance(item_rows, list):
                item_rows = []
            for item in item_rows:
                if not isinstance(item, dict):
                    continue
                lines += 1
                order_line_count += 1
                line_semantics["line_rows"] += 1
                line_semantics["is_bonus_product_true"] += int(item.get("is_bonus_product") is True)
                line_semantics["is_discount_percent_true"] += int(item.get("is_discount_percent") is True)
                try:
                    quantity = Decimal(str(item.get("quantity")))
                    line_discount = Decimal(str(item.get("total_discount", 0) or 0))
                    each_discount = Decimal(str(item.get("discount_each_product", 0) or 0))
                    variation = item.get("variation_info") if isinstance(item.get("variation_info"), dict) else {}
                    retail_price = Decimal(str(variation.get("retail_price")))
                    line_list_value = retail_price * quantity
                    line_semantics["line_total_discount_positive"] += int(line_discount > 0)
                    line_semantics["discount_each_product_positive"] += int(each_discount > 0)
                    line_semantics["item_total_discount_equals_retail_times_quantity"] += int(line_discount == line_list_value and line_list_value > 0)
                    line_semantics["discount_each_product_equals_retail_price"] += int(each_discount == retail_price and retail_price > 0)
                    line_semantics["line_discount_covers_list_value"] += int(line_discount >= line_list_value and line_list_value > 0)
                except (InvalidOperation, TypeError, ValueError):
                    line_semantics["line_math_missing_or_invalid"] += 1
                for path, value in _walk(item):
                    all_line_fields.setdefault(path, Counter())[_type_name(value)] += 1
                    # Names and identifiers are intentionally omitted from the value survey.
                    if not INTERESTING.search(path) or any(tag in path.lower() for tag in ("name", "_id", "barcode", "sku", "note", "address")):
                        continue
                    stat = fields.setdefault(path, Counter())
                    stat[_type_name(value)] += 1
                    if value is None:
                        continue
                    if isinstance(value, bool):
                        enum_values.setdefault(path, Counter())[str(value).lower()] += 1
                    elif isinstance(value, str) and SAFE_ENUM.fullmatch(value) and len(enum_values.get(path, {})) < 20:
                        enum_values.setdefault(path, Counter())[value] += 1
                    elif isinstance(value, (int, float)) and not isinstance(value, bool):
                        record = numeric_stats.setdefault(path, {"non_null": 0, "zero": 0, "minimum": None, "maximum": None})
                        record["non_null"] = int(record["non_null"]) + 1
                        record["zero"] = int(record["zero"]) + int(value == 0)
                        record["minimum"] = value if record["minimum"] is None else min(float(record["minimum"]), value)
                        record["maximum"] = value if record["maximum"] is None else max(float(record["maximum"]), value)
                variation = item.get("variation_info")
                if isinstance(variation, dict):
                    categories = variation.get("category_ids")
                    if isinstance(categories, list):
                        for category in categories:
                            if category is not None:
                                category_values[str(category)] += 1
                    if variation.get("product_id") is not None or item.get("product_id") is not None:
                        products += 1
            max_lines_per_order = max(max_lines_per_order, order_line_count)

    if total_rows != manifest.get("row_count"):
        raise ValueError("snapshot total row count mismatch")

    api_path = ROOT / "src" / "ingest" / "client.py"
    api_source = api_path.read_text(encoding="utf-8")
    allowlisted_paths = ["/shops", "/shops/{shop_id}/orders"]
    output = {
        "scope": "status-3 development orders only",
        "interval": f"[{start.isoformat()},{test_start.isoformat()})",
        "snapshot_id": split["snapshot_id"],
        "snapshot_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "split_config_sha256": hashlib.sha256(split_bytes).hexdigest(),
        "status3_dev_order_count": orders,
        "line_count": lines,
        "max_lines_in_one_order": max_lines_per_order,
        "line_rows_with_variation_metadata": products,
        "line_field_paths_and_types": {
            name: dict(sorted(types.items())) for name, types in sorted(all_line_fields.items())
            if not any(tag in name.lower() for tag in ("name", "phone", "email", "address", "note", "customer", "order_id"))
        },
        "field_coverage": {
            name: {
                "non_null_count": int(sum(count for kind, count in counts.items() if kind != "null")),
                "null_count": int(counts.get("null", 0)),
                "types": dict(sorted(counts.items())),
                "enum_values": dict(enum_values.get(name, {})),
                "numeric_summary": numeric_stats.get(name),
            }
            for name, counts in sorted(fields.items())
        },
        "variation_category_id_values": dict(category_values.most_common(30)),
        "line_discount_semantics": dict(line_semantics),
        "order_total_discount_zero_nonzero": dict(order_discount_values),
        "exact_line_selling_price_fields_found": [
            name for name in all_line_fields if name.rsplit(".", 1)[-1].lower() in {"price", "selling_price", "sale_price", "unit_price", "final_price"}
        ],
        "api_read_allowlist": allowlisted_paths if "_ALLOWED_SHOPS_PATH" in api_source else ["inspection required"],
        "product_inventory_endpoint_in_allowlist": False,
        "catalog_endpoint_added": False,
        "catalog_decision": "not needed for historical profiles: order-line variation_info already contains product ID, retail price, and category IDs; live catalog/stock fields are not historical evidence",
        "test_labels_loaded": False,
        "test_behavior_loaded": False,
    }
    destination = ROOT / "outputs" / "metrics" / "day3_gift_field_survey.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Development item-field survey complete: {orders} orders, {lines} lines; aggregate-only output written.")
    for name, coverage in output["field_coverage"].items():
        print(f"{name}: non_null={coverage['non_null_count']}, null={coverage['null_count']}, types={coverage['types']}")
    print("Test labels/behavior not read; no product/inventory endpoint was added.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
