"""Preregistered, line-level gift detection for Day 3 basket analysis."""

from __future__ import annotations

from collections import Counter, defaultdict
from decimal import Decimal
from typing import Any


ZERO = Decimal("0")
HUNDRED = Decimal("100")
MAX_INFERRED_LINES = 6


def _decimal(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _unique_subset(lines: list[dict[str, Any]], target: Decimal) -> tuple[int, ...] | None:
    """Return the only 1..6-line subset summing to target; ambiguity is None.

    DP counts exact subsets by (sum, cardinality), capped at two. A path is
    retained only while the sum/cardinality combination has exactly one way.
    """
    if target <= ZERO:
        return None
    states: list[dict[Decimal, tuple[int, tuple[int, ...] | None]]] = [
        {ZERO: (1, ())}, *({} for _ in range(MAX_INFERRED_LINES))
    ]
    for index, line in enumerate(lines):
        price = _decimal(line.get("retail_price"))
        quantity = _decimal(line.get("quantity"))
        if price is None or quantity is None or price <= ZERO or quantity <= ZERO:
            continue
        amount = price * quantity
        for size in range(MAX_INFERRED_LINES - 1, -1, -1):
            for subtotal, (ways, path) in list(states[size].items()):
                new_total = subtotal + amount
                if new_total > target:
                    continue
                prior = states[size + 1].get(new_total)
                if prior is None:
                    states[size + 1][new_total] = (
                        min(2, ways),
                        (path + (index,)) if ways == 1 and path is not None else None,
                    )
                else:
                    combined = min(2, prior[0] + ways)
                    states[size + 1][new_total] = (combined, prior[1] if combined == 1 else None)
    matches: list[tuple[int, ...] | None] = []
    for size in range(1, MAX_INFERRED_LINES + 1):
        state = states[size].get(target)
        if state:
            ways, path = state
            if ways > 1:
                return None
            matches.append(path)
    return matches[0] if len(matches) == 1 and matches[0] is not None else None


def _full_line_discount(line: dict[str, Any]) -> bool:
    price = _decimal(line.get("retail_price"))
    discount = _decimal(line.get("discount_each_product"))
    is_percent = line.get("is_discount_percent")
    if price is None or discount is None or price <= ZERO:
        return False
    if is_percent is True:
        return discount == HUNDRED
    if is_percent is False:
        return discount == price
    return False


def classify_order_lines(order: dict[str, Any]) -> list[dict[str, Any]]:
    """Apply the fixed priority: explicit bonus flag, full discount, unique subset."""
    source_lines = [dict(line) for line in order.get("gift_line_records", [])]
    for line in source_lines:
        line["gift_line"] = False
        line["gift_source"] = "not_gift"
        line["gift_low_confidence"] = False
        if line.get("bonus_flag") is True:
            line["gift_line"] = True
            line["gift_source"] = "flag"
        elif _full_line_discount(line):
            line["gift_line"] = True
            line["gift_source"] = "zero_price"

    discount = _decimal(order.get("total_discount_at_snapshot")) or ZERO
    candidates = [
        line for line in source_lines
        if not line["gift_line"] and line.get("product_key") is not None
    ]
    match = _unique_subset(candidates, discount)
    if match is not None:
        for candidate_index in match:
            line = candidates[candidate_index]
            line["gift_line"] = True
            line["gift_source"] = "inferred_subset"
            line["gift_low_confidence"] = True

    return source_lines


def classify_orders(orders: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return copied orders with classified lines and aggregate source counts."""
    result: list[dict[str, Any]] = []
    line_counts: Counter[str] = Counter()
    order_counts: dict[str, set[int]] = defaultdict(set)
    for order_index, order in enumerate(orders):
        copied = dict(order)
        classified = classify_order_lines(order)
        copied["gift_line_records"] = classified
        result.append(copied)
        for line in classified:
            source = line["gift_source"]
            line_counts[source] += 1
            order_counts[source].add(order_index)
    sources = ("flag", "zero_price", "inferred_subset", "not_gift")
    audit = {
        "line_count_by_source": {key: int(line_counts[key]) for key in sources},
        "distinct_orders_with_source": {key: len(order_counts[key]) for key in sources},
        "gift_line_count": int(sum(line_counts[key] for key in sources if key != "not_gift")),
        "line_count": int(sum(line_counts.values())),
        "low_confidence_inferred_line_count": int(sum(line["gift_low_confidence"] for order in result for line in order["gift_line_records"])),
        "test_labels_loaded": False,
        "test_behavior_loaded": False,
    }
    return result, audit
