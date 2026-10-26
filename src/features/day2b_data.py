"""Development-only data preparation for the preregistered Day 2B follow-up."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
from typing import Any
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from features.day2_data import (
    build_label_samples,
    canonical_province,
    load_dev_orders,
    local_day,
    nearest_holiday_distance,
    normalize_product_name,
    safe_status,
)
from features.money import assess_order_money, decimal_value
from ingest.identifiers import pseudonymize_id
from ingest.settings import load_analytics_hmac_key

LOCAL_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
ZERO = Decimal(0)


def _locked_development_interval() -> tuple[dict[str, Any], date, date, Path, dict[str, Any]]:
    split = yaml.safe_load((ROOT / "config" / "split.yaml").read_bytes())
    start = date.fromisoformat("2024-04-01")
    test_start = date.fromisoformat(str(split["test_start"]))
    snapshot_root = (ROOT / "data" / "raw" / "pancake_orders" / str(split["snapshot_id"])).resolve()
    manifest_path = snapshot_root / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    if manifest_hash != split.get("snapshot_manifest_sha256"):
        raise ValueError("locked snapshot manifest hash mismatch")
    return split, start, test_start, snapshot_root, manifest


def make_repurchase_features(samples: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Attach features from the latest non-gift status-3 order strictly before each T."""
    orders, _, _ = load_dev_orders()
    by_customer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for order in orders:
        if order["customer_key"] and not order["is_gift"]:
            by_customer[order["customer_key"]].append(order)
    for rows in by_customer.values():
        rows.sort(key=lambda row: (row["date"], row["order_sequence"]))

    result: list[dict[str, Any]] = []
    selected_dates: list[date] = []
    channel_present = 0
    category_present = 0
    for sample in samples:
        key = sample["customer_key"]
        as_of = date.fromisoformat(str(sample["T"]))
        history = [order for order in by_customer.get(key, []) if order["date"] < as_of]
        if not history:
            raise ValueError("label sample has no pre-T non-gift purchase for its latest-order features")
        last = history[-1]
        if last["date"] >= as_of:
            raise ValueError("latest-order feature crossed its T boundary")
        selected_dates.append(last["date"])
        distinct_products = set(last["product_keys"])
        category_counts = Counter(
            str(item["category"]) for item in last["items"]
            if item.get("category") is not None and str(item["category"]).strip()
        )
        primary_group = category_counts.most_common(1)[0][0] if category_counts else None
        total = last.get("total_price_at_snapshot")
        discount = last.get("total_discount_at_snapshot")
        discount_rate = float(discount / total) if total is not None and total > ZERO and discount is not None else None
        channel = last.get("order_channel")
        if channel:
            channel_present += 1
        if primary_group:
            category_present += 1
        month = last["date"].month
        result.append({
            **sample,
            "last_order_product_count": len(distinct_products),
            "last_order_primary_product_group": primary_group,
            "last_order_discount_rate": discount_rate,
            "last_order_revenue_recognized": float(last["revenue_recognized"] or ZERO),
            "last_order_channel": channel,
            "last_order_province": last.get("province"),
            "last_order_month": month,
            "last_order_month_sin": __import__("math").sin(2 * __import__("math").pi * month / 12),
            "last_order_month_cos": __import__("math").cos(2 * __import__("math").pi * month / 12),
            "last_order_holiday_distance_days": nearest_holiday_distance(last["date"]),
        })
    summary = {
        "samples": len(result),
        "feature_source": "most recent status-3 non-gift order with local_date < T",
        "latest_feature_date_max": max(selected_dates).isoformat() if selected_dates else None,
        "all_feature_dates_strictly_before_T": True,
        "channel_available_samples": channel_present,
        "primary_product_group_available_samples": category_present,
        "product_group_source": "modal category_id from line items; missing when source category is unavailable",
        "discount_rate_rule": "total_discount / total_price when total_price > 0; otherwise missing",
        "payment_fields_used": False,
        "test_labels_loaded": False,
        "test_behavior_loaded": False,
    }
    return result, summary


def _local_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(LOCAL_TZ)


def load_cancel_refund_orders() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Read only development order fields required by the preregistered order-level task."""
    split, analysis_start, test_start, snapshot_root, manifest = _locked_development_interval()
    manifest_hash = hashlib.sha256((snapshot_root / "manifest.json").read_bytes()).hexdigest()
    hmac_key = load_analytics_hmac_key(ROOT / "xoaif.env")
    rows: list[dict[str, Any]] = []
    source_rows_seen = 0
    page_records = manifest.get("pages", [])
    for page_no, page_record in enumerate(page_records, start=1):
        page_path = (snapshot_root / str(page_record["file"])).resolve()
        if not page_path.is_relative_to(snapshot_root):
            raise ValueError("snapshot page escaped its locked directory")
        page_bytes = page_path.read_bytes()
        if hashlib.sha256(page_bytes).hexdigest() != page_record.get("sha256"):
            raise ValueError("snapshot page checksum mismatch")
        payload = json.loads(page_bytes)
        source_rows = payload.get("data", [])
        if payload.get("page_number") != page_no or len(source_rows) != page_record.get("rows"):
            raise ValueError("snapshot page metadata mismatch")
        for source in source_rows:
            source_rows_seen += 1
            if not isinstance(source, dict):
                continue
            # Timestamp is the only field inspected until the row is proven development data.
            timestamp = _local_timestamp(source.get("inserted_at"))
            if timestamp is None or timestamp.date() < analysis_start or timestamp.date() >= test_start:
                continue
            status = safe_status(source.get("status"))
            if status not in {3, 5, 6}:
                continue
            customer = source.get("customer")
            raw_customer_id = customer.get("customer_id") if isinstance(customer, dict) else None
            customer_key = (
                pseudonymize_id(raw_customer_id, key=hmac_key, namespace="xoaif/customer/v1")
                if raw_customer_id is not None and str(raw_customer_id).strip() else None
            )
            item_rows = source.get("items")
            item_rows = item_rows if isinstance(item_rows, list) else []
            products: set[str] = set()
            for item in item_rows:
                if not isinstance(item, dict):
                    continue
                product_id = item.get("product_id")
                if product_id is not None and str(product_id).strip():
                    products.add(pseudonymize_id(product_id, key=hmac_key, namespace="xoaif/product/v1"))
            shipping_address = source.get("shipping_address")
            province = canonical_province(shipping_address.get("province_name")) if isinstance(shipping_address, dict) else None
            total_price = decimal_value(source.get("total_price"))
            # Status-3 gifts are excluded from behavior labels per amendment 03.
            is_gift = assess_order_money(source).is_gift if status == 3 else False
            rows.append({
                "local_timestamp": timestamp,
                "local_date": timestamp.date(),
                "status": status,
                "label_cancel_or_return": int(status in {5, 6}),
                "customer_key": customer_key,
                "is_gift": is_gift,
                "item_count": len(products),
                "order_value_at_creation": float(total_price) if total_price is not None else None,
                "channel": normalize_product_name(source.get("order_sources_name")),
                "province": province,
                "order_month": timestamp.month,
                "nearest_holiday_distance_days": nearest_holiday_distance(timestamp.date()),
            })
    if source_rows_seen != manifest.get("row_count"):
        raise ValueError("source snapshot row reconciliation failed")
    rows.sort(key=lambda row: row["local_timestamp"])
    seen_customers: set[str] = set()
    for row in rows:
        key = row["customer_key"]
        row["customer_new_or_returning"] = (
            "unknown" if key is None else ("returning" if key in seen_customers else "new")
        )
        if row["status"] == 3 and not row["is_gift"] and key:
            seen_customers.add(key)
    usable = [row for row in rows if not (row["status"] == 3 and row["is_gift"])]
    summary = {
        "snapshot_id": split["snapshot_id"],
        "source_manifest_sha256": manifest_hash,
        "analysis_start": analysis_start.isoformat(),
        "test_start_exclusive": test_start.isoformat(),
        "eligible_status_3_5_6_orders": len(usable),
        "status_3_non_gift_orders": sum(row["status"] == 3 for row in usable),
        "status_3_gifts_excluded": sum(row["status"] == 3 and row["is_gift"] for row in rows),
        "status_5_or_6_positive_orders": sum(row["label_cancel_or_return"] for row in usable),
        "status_3_missing_customer_key": sum(row["status"] == 3 and row["customer_key"] is None for row in usable),
        "channel_present": sum(bool(row["channel"]) for row in usable),
        "test_labels_loaded": False,
        "test_behavior_loaded": False,
        "post_creation_fields_used_as_predictors": False,
    }
    return usable, summary


def cancel_validation_windows(analysis_start: date, test_start: date, folds: int = 5, warmup_days: int = 180) -> list[tuple[date, date]]:
    """Return equal-width chronological validation windows after a train-only warmup."""
    start = analysis_start + timedelta(days=warmup_days)
    total_days = (test_start - start).days
    if total_days <= 0 or folds <= 0:
        return []
    quotient, remainder = divmod(total_days, folds)
    windows = []
    cursor = start
    for index in range(folds):
        width = quotient + int(index < remainder)
        end = cursor + timedelta(days=width)
        windows.append((cursor, end))
        cursor = end
    return windows
