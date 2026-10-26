from __future__ import annotations

from decimal import Decimal

from features.gift_lines import _unique_subset, classify_order_lines


def _line(price, quantity=1, **kwargs):
    return {"product_key": kwargs.pop("product_key", "p"), "retail_price": Decimal(str(price)), "quantity": Decimal(str(quantity)), **kwargs}


def test_unique_subset_infers_only_a_single_exact_subset():
    lines = [_line(10), _line(20), _line(40)]
    assert _unique_subset(lines, Decimal("30")) == (0, 1)
    assert _unique_subset(lines, Decimal("41")) is None


def test_multiple_exact_subsets_are_not_inferred():
    lines = [_line(10), _line(20), _line(30)]
    assert _unique_subset(lines, Decimal("30")) is None


def test_gift_source_priority_flag_then_full_discount_then_subset():
    order = {
        "total_discount_at_snapshot": Decimal("30"),
        "gift_line_records": [
            _line(50, bonus_flag=True),
            _line(40, discount_each_product=40, is_discount_percent=False),
            _line(10),
            _line(20),
            _line(90),
        ],
    }
    result = classify_order_lines(order)
    assert [line["gift_source"] for line in result] == [
        "flag", "zero_price", "inferred_subset", "inferred_subset", "not_gift"
    ]
    assert result[2]["gift_low_confidence"] is True


def test_zero_list_price_or_unverified_discount_does_not_mark_gift():
    order = {
        "total_discount_at_snapshot": Decimal("0"),
        "gift_line_records": [
            _line(0, discount_each_product=0, is_discount_percent=None),
            _line(100, discount_each_product=100, is_discount_percent=None),
        ],
    }
    result = classify_order_lines(order)
    assert all(line["gift_source"] == "not_gift" for line in result)
