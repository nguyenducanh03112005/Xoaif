"""Single-open boundary for HO2; row loader is inert until a valid open lock exists."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from features.day2_data import (LOCAL_TZ, canonical_province, local_day, nearest_holiday_distance,
                                normalize_product_name, safe_status)
from features.money import assess_order_money, decimal_value
from features.gift_lines import classify_order_lines
from ingest.identifiers import pseudonymize_id
from ingest.settings import load_analytics_hmac_key


def require_open_lock(root: Path) -> dict:
    path = root / "outputs/metrics/holdout2_opened.lock.json"
    if not path.is_file():
        raise PermissionError("HO2 is closed: valid single-open lock is required")
    lock = json.loads(path.read_text(encoding="utf-8"))
    config = yaml.safe_load((root / "config/amendment_06_ho2.yaml").read_bytes())
    protocol_path = root / "docs/analysis_plan_amendment06_ho2.md"
    evaluator_path = root / "scripts/evaluate_holdout2_once.py"
    expected = {
        "revision": 2,
        "amendment_id": "06-HO2",
        "status": "opened_once",
        "config_sha256": hashlib.sha256((root / "config/amendment_06_ho2.yaml").read_bytes()).hexdigest(),
        "protocol_sha256": hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
        "evaluator_sha256": hashlib.sha256(evaluator_path.read_bytes()).hexdigest(),
        "t2": str(config["T2"]),
    }
    for key, value in expected.items():
        if lock.get(key) != value:
            raise PermissionError(f"invalid HO2 open lock field: {key}")
    if lock.get("test_open_count") != 1:
        raise PermissionError("HO2 lock must record exactly one open")
    return lock


def load_authorized_holdout_orders(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Load status-3 orders only after checking the one-time lock."""
    lock = require_open_lock(root)
    split = yaml.safe_load((root / "config/split.yaml").read_bytes())
    amendment = yaml.safe_load((root / "config/amendment_06_ho2.yaml").read_bytes())
    start = date.fromisoformat(str(split["analysis_start"]))
    end = date.fromisoformat(str(amendment["label_window"]["end_inclusive"]))
    snapshot_root = (root / "data/raw/pancake_orders" / str(split["snapshot_id"])).resolve()
    manifest_path = snapshot_root / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != split.get("snapshot_manifest_sha256"):
        raise PermissionError("snapshot manifest hash differs from locked split")
    manifest = json.loads(manifest_bytes)
    hmac_key = load_analytics_hmac_key(root / "xoaif.env")
    orders: list[dict[str, Any]] = []
    seen = 0
    for page_no, page_info in enumerate(manifest.get("pages", []), start=1):
        page_path = (snapshot_root / str(page_info["file"])).resolve()
        if not page_path.is_relative_to(snapshot_root):
            raise ValueError("snapshot page escaped locked snapshot")
        page_bytes = page_path.read_bytes()
        if hashlib.sha256(page_bytes).hexdigest() != page_info.get("sha256"):
            raise ValueError("snapshot page checksum mismatch")
        payload = json.loads(page_bytes)
        rows = payload.get("data", [])
        if payload.get("page_number") != page_no or len(rows) != page_info.get("rows"):
            raise ValueError("snapshot page metadata mismatch")
        for source in rows:
            seen += 1
            if not isinstance(source, dict):
                continue
            # inserted_at is the only row field read until the row is in the frozen local-date scope.
            day = local_day(source.get("inserted_at"))
            if day is None or day < start or day > end:
                continue
            if safe_status(source.get("status")) != 3:
                continue
            money = assess_order_money(source)
            customer = source.get("customer")
            raw_customer = customer.get("customer_id") if isinstance(customer, dict) else None
            customer_key = (pseudonymize_id(raw_customer, key=hmac_key, namespace="xoaif/customer/v1")
                            if raw_customer is not None and str(raw_customer).strip() else None)
            source_items = source.get("items")
            source_items = source_items if isinstance(source_items, list) else []
            items, products, gift_line_records = [], set(), []
            quantity_total = Decimal(0)
            for item in source_items:
                if not isinstance(item, dict):
                    continue
                raw_product = item.get("product_id")
                product_key = (pseudonymize_id(raw_product, key=hmac_key, namespace="xoaif/product/v1")
                               if raw_product is not None and str(raw_product).strip() else None)
                if product_key:
                    products.add(product_key)
                q = decimal_value(item.get("quantity"))
                if q is not None:
                    quantity_total += q
                variation = item.get("variation_info")
                variation = variation if isinstance(variation, dict) else {}
                categories = variation.get("category_ids")
                category = next((str(x).strip() for x in categories if x is not None and str(x).strip()), None) if isinstance(categories, list) else None
                items.append({"product_key": product_key, "quantity": q, "category": category})
                gift_line_records.append({
                    "source_line_index": len(gift_line_records), "product_key": product_key,
                    "quantity": q, "retail_price": decimal_value(variation.get("retail_price")),
                    "category": category,
                    "bonus_flag": item.get("is_bonus_product") if isinstance(item.get("is_bonus_product"), bool) else None,
                    "discount_each_product": decimal_value(item.get("discount_each_product")),
                    "is_discount_percent": item.get("is_discount_percent") if isinstance(item.get("is_discount_percent"), bool) else None,
                })
            address = source.get("shipping_address")
            province = canonical_province(address.get("province_name")) if isinstance(address, dict) else None
            orders.append({
                "order_sequence": len(orders), "date": day, "month": day.strftime("%Y-%m"),
                "status": 3, "customer_key": customer_key, "is_gift": money.is_gift,
                "revenue_recognized": money.revenue_recognized,
                "monetary_contribution": money.monetary_contribution,
                "total_price_at_snapshot": decimal_value(source.get("total_price")),
                "total_discount_at_snapshot": decimal_value(source.get("total_discount")),
                "quantity_total": quantity_total, "items": items, "product_keys": sorted(products),
                "gift_line_records": gift_line_records,
                "province": province, "order_channel": normalize_product_name(source.get("order_sources_name")),
                "nearest_holiday_distance_days": nearest_holiday_distance(day),
            })
    if seen != manifest.get("row_count"):
        raise ValueError("snapshot row count differs from manifest")
    orders.sort(key=lambda row: (row["date"], row["order_sequence"]))
    classified, _ = classify_order_lines(orders)
    for order in classified:
        nongift = [line for line in order["gift_line_records"] if not line["gift_line"] and line.get("product_key")]
        order["basket_product_keys"] = sorted({line["product_key"] for line in nongift})
    return orders, {"snapshot_id": split["snapshot_id"], "snapshot_rows_checked": seen,
                    "scope_start": start.isoformat(), "scope_end_inclusive": end.isoformat(),
                    "opened_lock_sha256": hashlib.sha256((root / "outputs/metrics/holdout2_opened.lock.json").read_bytes()).hexdigest(),
                    "labels_loaded": True}
