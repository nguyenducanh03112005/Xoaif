from datetime import date
from decimal import Decimal

from features.day2_data import make_customer_features


def _order(day: date, value: str) -> dict:
    amount = Decimal(value)
    return {
        "customer_key": "synthetic-customer",
        "date": day,
        "is_gift": False,
        "price_adjustment": None,
        "adj_unexplained": False,
        "monetary_contribution": amount,
        "monetary_A_contribution": amount,
        "quantity_total": Decimal("1"),
        "product_keys": ["synthetic-product"],
        "province": "SYNTHETIC",
    }


def test_customer_features_exclude_orders_on_or_after_as_of():
    as_of = date(2025, 1, 1)
    orders = [
        _order(date(2024, 12, 31), "100"),
        _order(as_of, "900"),
        _order(date(2025, 1, 2), "9000"),
    ]

    [features] = make_customer_features(orders, as_of=as_of)

    assert features["frequency"] == 1
    assert features["monetary"] == 100.0
    assert features["last_purchase_date"] == "2024-12-31"
    assert features["recency_days"] == 1
