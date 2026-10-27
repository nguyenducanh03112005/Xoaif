"""Load development-only orders and build leakage-safe customer snapshots."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any
import unicodedata
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from features.money import MoneyAssessment, assess_order_money, decimal_value
from ingest.analysis_amendment import load_analysis_amendment
from ingest.decision_amendment import load_money_adjustment_amendment
from ingest.identifiers import pseudonymize_id
from ingest.settings import load_analytics_hmac_key

LOCAL_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
ZERO = Decimal(0)
# Mùng 1 Tết Nguyên đán: 10 Feb 2024 and 29 Jan 2025.
# Sources: official government information linked from xaydungchinhsach.chinhphu.vn.
TET_DATES = (date(2024, 2, 10), date(2025, 1, 29))
HOLIDAY_MONTH_DAYS = ((3, 8), (10, 20), (11, 20), (12, 25))
LABEL_T_CANDIDATES = tuple(date(year, month, 1) for year, month in (
    (2024, 5), (2024, 6), (2024, 7), (2024, 8), (2024, 9), (2024, 10),
    (2024, 11), (2024, 12), (2025, 1), (2025, 2), (2025, 3), (2025, 4),
))


def local_day(value: Any) -> date | None:
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


def safe_status(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def normalized_category(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return re.sub(r"\s+", " ", value.strip())


def normalize_product_name(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    return re.sub(r"\s+", " ", value.strip())


def canonical_province(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = unicodedata.normalize("NFD", value.strip())
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    text = text.replace("Đ", "D").replace("đ", "d")
    text = re.sub(r"\s+", " ", text).strip().upper()
    return text or None


def load_dev_orders() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, dict[str, Any]]]:
    split = yaml.safe_load((ROOT / "config" / "split.yaml").read_bytes())
    amendment_01, _, _ = load_analysis_amendment(ROOT)
    amendment_03, amendment_hash = load_money_adjustment_amendment(ROOT)
    analysis_start = date.fromisoformat(str(amendment_01["analysis_start"]))
    test_start = date.fromisoformat(str(split["test_start"]))
    snapshot_id = str(split["snapshot_id"])
    snapshot_root = (ROOT / "data" / "raw" / "pancake_orders" / snapshot_id).resolve()
    manifest_path = snapshot_root / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
    if manifest_hash != split.get("snapshot_manifest_sha256"):
        raise ValueError("snapshot manifest differs from locked split")
    manifest = json.loads(manifest_bytes)
    hmac_key = load_analytics_hmac_key(ROOT / "xoaif.env")
    orders: list[dict[str, Any]] = []
    products: dict[str, dict[str, Any]] = {}
    source_rows_seen = 0
    count_status3 = 0
    missing_customer = 0
    gifts = 0
    no_item_rows = 0
    no_customer_and_gift = 0
    for page_no, page_record in enumerate(manifest["pages"], start=1):
        page_path = (snapshot_root / page_record["file"]).resolve()
        if not page_path.is_relative_to(snapshot_root):
            raise ValueError("snapshot page path escaped its directory")
        page_bytes = page_path.read_bytes()
        if hashlib.sha256(page_bytes).hexdigest() != page_record.get("sha256"):
            raise ValueError("snapshot page checksum mismatch")
        payload = json.loads(page_bytes)
        page_rows = payload.get("data", [])
        if payload.get("page_number") != page_no or len(page_rows) != page_record.get("rows"):
            raise ValueError("snapshot page metadata or row count mismatch")
        for source_order in page_rows:
            source_rows_seen += 1
            if not isinstance(source_order, dict):
                continue
            # Do not access any other row field until inserted_at proves it is development data.
            day = local_day(source_order.get("inserted_at"))
            if day is None or day >= test_start or day < analysis_start:
                continue
            if safe_status(source_order.get("status")) != 3:
                continue
            count_status3 += 1
            assessment: MoneyAssessment = assess_order_money(source_order)
            customer = source_order.get("customer")
            customer_id = customer.get("customer_id") if isinstance(customer, dict) else None
            customer_key = None
            if customer_id is not None and str(customer_id).strip():
                customer_key = pseudonymize_id(customer_id, key=hmac_key, namespace="xoaif/customer/v1")
            else:
                missing_customer += 1
            if assessment.is_gift:
                gifts += 1
                if customer_key is None:
                    no_customer_and_gift += 1
            source_items = source_order.get("items")
            items_present = isinstance(source_items, list) and len(source_items) > 0
            if not items_present:
                no_item_rows += 1
                source_items = []
            item_records: list[dict[str, Any]] = []
            gift_line_records: list[dict[str, Any]] = []
            quantity_total = ZERO
            product_keys: set[str] = set()
            for source_line_index, source_item in enumerate(source_items):
                if not isinstance(source_item, dict):
                    continue
                quantity = decimal_value(source_item.get("quantity"))
                if quantity is not None:
                    quantity_total += quantity
                product_id = source_item.get("product_id")
                product_key = None
                if product_id is not None and str(product_id).strip():
                    product_key = pseudonymize_id(product_id, key=hmac_key, namespace="xoaif/product/v1")
                    product_keys.add(product_key)
                variation = source_item.get("variation_info")
                variation = variation if isinstance(variation, dict) else {}
                retail_price = decimal_value(variation.get("retail_price"))
                product_name = normalize_product_name(variation.get("name"))
                categories = variation.get("category_ids")
                if isinstance(categories, list):
                    category = next((str(value).strip() for value in categories if value is not None and str(value).strip()), None)
                else:
                    category = None
                category_ids = [str(value).strip() for value in categories if value is not None and str(value).strip()] if isinstance(categories, list) else []
                if product_key is not None:
                    current = products.setdefault(product_key, {"names": [], "retail_prices": [], "categories": []})
                    if product_name:
                        current["names"].append(product_name)
                    if retail_price is not None and retail_price >= ZERO:
                        current["retail_prices"].append(retail_price)
                    if category:
                        current["categories"].append(category)
                    item_records.append({
                        "product_key": product_key,
                        "quantity": quantity,
                        "retail_price": retail_price,
                        "product_name": product_name,
                        "category": category,
                    })
                gift_line_records.append({
                    "source_line_index": source_line_index,
                    "product_key": product_key,
                    "quantity": quantity,
                    "retail_price": retail_price,
                    "product_name": product_name,
                    "category": category,
                    "category_ids": category_ids,
                    "bonus_flag": source_item.get("is_bonus_product") if isinstance(source_item.get("is_bonus_product"), bool) else None,
                    "discount_each_product": decimal_value(source_item.get("discount_each_product")),
                    "is_discount_percent": source_item.get("is_discount_percent") if isinstance(source_item.get("is_discount_percent"), bool) else None,
                    "line_total_discount": decimal_value(source_item.get("total_discount")),
                    "variation_key": pseudonymize_id(source_item.get("variation_id"), key=hmac_key, namespace="xoaif/variation/v1") if source_item.get("variation_id") is not None else None,
                })
            shipping_address = source_order.get("shipping_address")
            province = canonical_province(shipping_address.get("province_name")) if isinstance(shipping_address, dict) else None
            orders.append({
                "order_sequence": len(orders),
                "date": day,
                "month": day.strftime("%Y-%m"),
                "customer_key": customer_key,
                "is_gift": assessment.is_gift,
                "revenue_recognized": assessment.revenue_recognized,
                "total_price_at_snapshot": decimal_value(source_order.get("total_price")),
                "total_discount_at_snapshot": decimal_value(source_order.get("total_discount")),
                "order_channel": normalize_product_name(source_order.get("order_sources_name")),
                "monetary_contribution": assessment.monetary_contribution,
                "revenue_A": assessment.revenue_A,
                "monetary_A_contribution": assessment.monetary_A_contribution,
                "price_adjustment": assessment.price_adjustment,
                "adj_unexplained": assessment.adj_unexplained,
                "negative_revenue": assessment.negative_revenue,
                "gross_list_value": decimal_value(source_order.get("total_price")),
                "quantity_total": quantity_total,
                "items_present": items_present,
                "items": item_records,
                "gift_line_records": gift_line_records,
                "product_keys": sorted(product_keys),
                "province": province,
            })
    if source_rows_seen != manifest.get("row_count"):
        raise ValueError("source snapshot row reconciliation failed")
    if count_status3 != 6400:
        raise ValueError(f"expected 6400 status-3 development orders, found {count_status3}")
    stats = {
        "snapshot_id": snapshot_id,
        "source_manifest_sha256": manifest_hash,
        "amendment_03_sha256": amendment_hash,
        "analysis_start": analysis_start.isoformat(),
        "test_start_exclusive": test_start.isoformat(),
        "status3_dev_orders": count_status3,
        "missing_customer_id_orders": missing_customer,
        "gift_orders": gifts,
        "orders_without_line_items": no_item_rows,
        "missing_customer_and_gift_overlap": no_customer_and_gift,
        "test_labels_loaded": False,
        "test_behavior_loaded": False,
    }
    for product in products.values():
        if product["names"]:
            product["name"] = max(set(product["names"]), key=product["names"].count)
        else:
            product["name"] = "Sản phẩm không tên"
        if product["categories"]:
            product["category"] = max(set(product["categories"]), key=product["categories"].count)
        else:
            product["category"] = None
        if product["retail_prices"]:
            values = sorted(product["retail_prices"])
            product["retail_price"] = values[len(values) // 2]
        else:
            product["retail_price"] = None
    return orders, stats, products


def holiday_dates() -> list[date]:
    result = list(TET_DATES)
    for year in range(2023, 2027):
        result.extend(date(year, month, day) for month, day in HOLIDAY_MONTH_DAYS)
    return result


def nearest_holiday_distance(reference: date) -> int | None:
    dates = holiday_dates()
    return min((abs((reference - event).days) for event in dates), default=None)


def make_customer_features(
    orders: list[dict[str, Any]],
    *,
    as_of: date,
    monetary_variant: str = "primary",
    exclude_adjusted: bool = False,
    customer_keys: set[str] | None = None,
    analysis_start: date = date(2024, 4, 1),
) -> list[dict[str, Any]]:
    if monetary_variant not in {"primary", "A"}:
        raise ValueError("monetary_variant must be primary or A")
    eligible = []
    for order in orders:
        if order["date"] >= as_of or order["is_gift"] or order["customer_key"] is None:
            continue
        if customer_keys is not None and order["customer_key"] not in customer_keys:
            continue
        if exclude_adjusted and ((order["price_adjustment"] is not None and order["price_adjustment"] != ZERO) or order["adj_unexplained"]):
            continue
        eligible.append(order)
    by_customer: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for order in eligible:
        by_customer[order["customer_key"]].append(order)
    if customer_keys is not None:
        for key in customer_keys:
            by_customer.setdefault(key, [])
    result: list[dict[str, Any]] = []
    all_keys = sorted(by_customer)
    for customer_key in all_keys:
        records = sorted(by_customer[customer_key], key=lambda row: row["date"])
        dates = [row["date"] for row in records]
        no_history = not records
        if no_history:
            recency = (as_of - analysis_start).days
            first_date = None
            last_date = None
            selected_values: list[Decimal] = []
            monetary = ZERO
            quantity = ZERO
            products: set[str] = set()
            province = None
            positive_adj = negative_adj = 0
        else:
            first_date, last_date = dates[0], dates[-1]
            recency = (as_of - last_date).days
            if monetary_variant == "primary":
                selected_values = [row["monetary_contribution"] for row in records if row["monetary_contribution"] is not None]
            else:
                selected_values = [row["monetary_A_contribution"] for row in records if row["monetary_A_contribution"] is not None]
            monetary = sum(selected_values, ZERO)
            quantity = sum((row["quantity_total"] for row in records), ZERO)
            products = {product_key for row in records for product_key in row["product_keys"]}
            province = next((row["province"] for row in reversed(records) if row["province"]), None)
            positive_adj = sum(row["price_adjustment"] is not None and row["price_adjustment"] > ZERO for row in records)
            negative_adj = sum(row["price_adjustment"] is not None and row["price_adjustment"] < ZERO for row in records)
        frequency = len(records)
        gaps = [(right - left).days for left, right in zip(dates, dates[1:])]
        avg_gap = sum(gaps) / len(gaps) if gaps else 0.0
        values = selected_values
        row = {
            "customer_key": customer_key,
            "as_of": as_of.isoformat(),
            "recency_days": recency,
            "frequency": frequency,
            "monetary": float(monetary),
            "average_order_value": float(sum(values, ZERO) / len(values)) if values else 0.0,
            "max_order_value": float(max(values)) if values else 0.0,
            "total_quantity": float(quantity),
            "distinct_products": len(products),
            "mean_days_between_orders": avg_gap,
            "first_order_month": first_date.month if first_date else 0,
            "first_order_month_sin": __import__("math").sin(2 * __import__("math").pi * first_date.month / 12) if first_date else 0.0,
            "first_order_month_cos": __import__("math").cos(2 * __import__("math").pi * first_date.month / 12) if first_date else 0.0,
            "nearest_holiday_distance_days": nearest_holiday_distance(last_date) if last_date else None,
            "province": province or "UNKNOWN",
            "adjustment_positive_rate": positive_adj / frequency if frequency else 0.0,
            "adjustment_negative_rate": negative_adj / frequency if frequency else 0.0,
            "no_history_after_sensitivity": int(no_history),
            "first_purchase_date": first_date.isoformat() if first_date else None,
            "last_purchase_date": last_date.isoformat() if last_date else None,
        }
        result.append(row)
    return result


def build_label_samples(
    orders: list[dict[str, Any]],
    *,
    test_start: date,
    n_days: int = 180,
    l_days: int = 7,
    candidates: tuple[date, ...] = LABEL_T_CANDIDATES,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    purchase_dates: dict[str, list[date]] = defaultdict(list)
    for order in orders:
        if order["customer_key"] and not order["is_gift"]:
            purchase_dates[order["customer_key"]].append(order["date"])
    eligible_t = tuple(t for t in candidates if t + timedelta(days=n_days + l_days) < test_start)
    assigned: dict[str, date] = {}
    for customer_key, dates in purchase_dates.items():
        for t in eligible_t:
            if any(day < t for day in dates):
                assigned[customer_key] = t
                break
    samples: list[dict[str, Any]] = []
    for customer_key, t in sorted(assigned.items(), key=lambda pair: (pair[1], pair[0])):
        label_end = t + timedelta(days=n_days)
        label = int(any(t < day <= label_end for day in purchase_dates[customer_key]))
        samples.append({"customer_key": customer_key, "T": t.isoformat(), "label_returned": label})
    summary = {
        "candidate_T_count": len(eligible_t),
        "candidate_T_dates": [t.isoformat() for t in eligible_t],
        "N_days": n_days,
        "L_days": l_days,
        "customer_samples": len(samples),
        "positive_samples": sum(row["label_returned"] for row in samples),
        "positive_rate": sum(row["label_returned"] for row in samples) / len(samples) if samples else None,
        "unique_customer_count": len({row["customer_key"] for row in samples}),
        "unique_customer_keys": {row["customer_key"] for row in samples},
        "test_start": test_start.isoformat(),
        "max_label_asof": max((date.fromisoformat(row["T"]) + timedelta(days=n_days + l_days) for row in samples), default=None).isoformat() if samples else None,
    }
    if summary["unique_customer_count"] != summary["customer_samples"]:
        raise ValueError("customer appears more than once in the pre-registered label sample")
    if any(date.fromisoformat(row["T"]) + timedelta(days=n_days + l_days) >= test_start for row in samples):
        raise ValueError("a development label window overlaps the reserved test period")
    return samples, summary


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = fieldnames or (list(rows[0]) if rows else [])
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        import csv
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
