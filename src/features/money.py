"""Owner-approved money adjustments for development-only order analysis."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


def decimal_value(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        parsed = Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, ValueError, AttributeError):
        return None
    return parsed if parsed.is_finite() else None


def retail_price_quantity_total(items: Any) -> Decimal | None:
    """Sum nested variation_info.retail_price × quantity when every item is usable."""
    if not isinstance(items, list) or not items:
        return None
    total = Decimal(0)
    for item in items:
        if not isinstance(item, dict):
            return None
        variation = item.get("variation_info")
        variation = variation if isinstance(variation, dict) else {}
        price = decimal_value(variation.get("retail_price"))
        quantity = decimal_value(item.get("quantity"))
        if price is None or quantity is None:
            return None
        total += price * quantity
    return total


def classify_after_pattern(
    *, total: Decimal | None, discount: Decimal | None, shipping: Decimal | None, after: Decimal | None
) -> tuple[str, bool | None]:
    """Assign a mutually exclusive relationship label and unexplained flag."""
    if any(value is None for value in (total, discount, shipping, after)):
        return "missing_fields", None
    assert total is not None and discount is not None and shipping is not None and after is not None
    base = total - discount
    expected = base + shipping
    residual = after - expected
    if after == expected:
        return "after_equals_total_minus_discount_plus_shipping", False
    if after == base and shipping > 0:
        return "after_equals_total_minus_discount_ship_not_added", False
    if after == total + shipping:
        return "after_equals_total_plus_shipping_discount_not_subtracted", False
    if after == total:
        return "after_equals_total", False
    if shipping != 0 and residual == shipping:
        return "residual_plus_shipping", False
    if shipping != 0 and residual == -shipping:
        return "residual_minus_shipping", False
    if discount != 0 and residual == discount:
        return "residual_plus_discount", False
    if discount != 0 and residual == -discount:
        return "residual_minus_discount", False
    distance = abs(residual)
    if distance <= Decimal(10_000):
        band = "le_10000"
    elif distance <= Decimal(50_000):
        band = "10001_50000"
    elif distance <= Decimal(100_000):
        band = "50001_100000"
    else:
        band = "gt_100000"
    return f"other_distance_{band}", True


@dataclass(frozen=True)
class MoneyAssessment:
    is_gift: bool
    revenue_recognized: Decimal | None
    price_adjustment: Decimal | None
    revenue_A: Decimal | None
    monetary_contribution: Decimal | None
    monetary_A_contribution: Decimal | None
    negative_revenue: bool
    negative_revenue_causes: tuple[str, ...]
    exception_applied: bool
    after_pattern: str
    adj_unexplained: bool
    identity_matches: bool | None
    total_zero_after_positive: bool
    retail_line_total: Decimal | None
    retail_line_matches_total: bool | None
    money_fields_usable: bool


def assess_order_money(order: dict[str, Any]) -> MoneyAssessment:
    total = decimal_value(order.get("total_price"))
    discount = decimal_value(order.get("total_discount"))
    shipping = decimal_value(order.get("shipping_fee"))
    after = decimal_value(order.get("total_price_after_sub_discount"))
    base = total - discount if total is not None and discount is not None else None
    pattern, unexplained = classify_after_pattern(
        total=total, discount=discount, shipping=shipping, after=after
    )
    identity_matches = (
        after == base + shipping
        if after is not None and base is not None and shipping is not None
        else None
    )
    exception_applied = bool(
        after is not None and base is not None and shipping is not None and after == base and shipping > 0
    )
    calculated_revenue = None
    if after is not None and shipping is not None:
        calculated_revenue = after if exception_applied else after - shipping

    is_gift = (calculated_revenue == 0) or (total == 0 and after == 0)
    revenue = Decimal(0) if is_gift else calculated_revenue
    price_adjustment = revenue - base if revenue is not None and base is not None else None
    revenue_a = Decimal(0) if is_gift else base
    negative_revenue = bool(not is_gift and revenue is not None and revenue < 0)
    negative_causes: list[str] = []
    if negative_revenue:
        if after is not None and after < 0:
            negative_causes.append("after_is_negative")
        if after is not None and shipping is not None and after < shipping:
            negative_causes.append("after_below_shipping_fee")
        if base is not None and base < 0:
            negative_causes.append("total_minus_discount_is_negative")
    monetary_contribution = (
        None if is_gift or revenue is None else max(revenue, Decimal(0))
    )
    monetary_a = None if is_gift or base is None else max(base, Decimal(0))
    line_total = retail_price_quantity_total(order.get("items"))
    line_matches = line_total == total if line_total is not None and total is not None else None
    return MoneyAssessment(
        is_gift=is_gift,
        revenue_recognized=revenue,
        price_adjustment=price_adjustment,
        revenue_A=revenue_a,
        monetary_contribution=monetary_contribution,
        monetary_A_contribution=monetary_a,
        negative_revenue=negative_revenue,
        negative_revenue_causes=tuple(negative_causes),
        exception_applied=exception_applied,
        after_pattern=pattern,
        adj_unexplained=(unexplained is not False),
        identity_matches=identity_matches,
        total_zero_after_positive=(total == 0 and after is not None and after > 0),
        retail_line_total=line_total,
        retail_line_matches_total=line_matches,
        money_fields_usable=all(value is not None for value in (total, discount, shipping, after)),
    )
