"""Feature construction at a frozen cutoff; this module never loads data itself."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
import math

import pandas as pd

from features.day2_data import make_customer_features, nearest_holiday_distance


def feature_eligible(local_date: date, t2: date) -> bool:
    return local_date < t2


def outcome_eligible(local_date: date, t2: date, horizon_days: int = 180) -> bool:
    return t2 < local_date <= t2 + timedelta(days=horizon_days)


def _latest_order_features(orders: list[dict], customers: set[str], t2: date) -> pd.DataFrame:
    by_customer: dict[str, list[dict]] = defaultdict(list)
    for order in orders:
        if order.get("customer_key") in customers and not order.get("is_gift"):
            order_date = order["date"]
            if order_date < t2:
                by_customer[order["customer_key"]].append(order)
    rows = []
    for customer in sorted(customers):
        history = sorted(by_customer.get(customer, []), key=lambda row: (row["date"], row.get("order_sequence", 0)))
        if not history:
            continue
        last = history[-1]
        day = last["date"]
        if day >= t2:
            raise ValueError("latest-order feature crossed T2")
        products = set(last.get("product_keys", []))
        categories = Counter(str(item["category"]) for item in last.get("items", [])
                             if item.get("category") is not None and str(item["category"]).strip())
        month = day.month
        total = last.get("total_price_at_snapshot")
        discount = last.get("total_discount_at_snapshot")
        rows.append({
            "customer_key": customer,
            "last_order_product_count": len(products),
            "last_order_primary_product_group": categories.most_common(1)[0][0] if categories else None,
            "last_order_discount_rate": float(discount / total) if total and discount is not None else None,
            "last_order_revenue_recognized": float(last.get("revenue_recognized") or 0),
            "last_order_channel": last.get("order_channel"),
            "last_order_province": last.get("province"),
            "last_order_month": month,
            "last_order_month_sin": math.sin(2 * math.pi * month / 12),
            "last_order_month_cos": math.cos(2 * math.pi * month / 12),
            "last_order_holiday_distance_days": nearest_holiday_distance(day),
            "latest_feature_date": day,
        })
    return pd.DataFrame(rows)


def build_customer_features_at_t(orders: list[dict], t2: date, *, analysis_start: date) -> pd.DataFrame:
    """Build one row per customer from strict pre-T2 status-3 non-gift history."""
    eligible = [o for o in orders if o.get("customer_key") and not o.get("is_gift")
                and o.get("status", 3) == 3 and feature_eligible(o["date"], t2)]
    customers = {str(o["customer_key"]) for o in eligible}
    base = pd.DataFrame(make_customer_features(eligible, as_of=t2, customer_keys=customers,
                                               analysis_start=analysis_start))
    latest = _latest_order_features(eligible, customers, t2)
    if base.empty or latest.empty:
        raise ValueError("feature cohort is empty")
    if base.customer_key.duplicated().any() or latest.customer_key.duplicated().any():
        raise ValueError("feature key is not unique")
    frame = base.merge(latest, on="customer_key", validate="one_to_one")
    if not (pd.to_datetime(frame.latest_feature_date).dt.date < t2).all():
        raise ValueError("feature date is not strictly before T2")
    frame["first_purchase_age_days"] = frame.first_purchase_date.map(
        lambda value: (t2 - date.fromisoformat(str(value))).days
    )
    frame["t_month_sin"] = math.sin(2 * math.pi * t2.month / 12)
    frame["t_month_cos"] = math.cos(2 * math.pi * t2.month / 12)
    return frame


def attach_holdout2_labels(features: pd.DataFrame, orders: list[dict], t2: date,
                           horizon_days: int = 180) -> pd.DataFrame:
    positive = {str(o["customer_key"]) for o in orders
                if o.get("customer_key") and o.get("status", 3) == 3 and not o.get("is_gift")
                and outcome_eligible(o["date"], t2, horizon_days)}
    out = features.copy()
    out["label_returned"] = out.customer_key.astype(str).isin(positive).astype(int)
    return out
