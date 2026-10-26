from decimal import Decimal

from features.money import assess_order_money, retail_price_quantity_total


def _order(**updates):
    order = {
        "total_price": 1000,
        "total_discount": 100,
        "shipping_fee": 100,
        "total_price_after_sub_discount": 1000,
        "items": [
            {"quantity": 2, "variation_info": {"retail_price": 500}},
        ],
    }
    order.update(updates)
    return order


def test_primary_revenue_uses_after_less_shipping_and_adjustment_is_zero():
    result = assess_order_money(_order())
    assert result.identity_matches is True
    assert result.exception_applied is False
    assert result.revenue_recognized == Decimal("900")
    assert result.price_adjustment == Decimal("0")
    assert result.revenue_A == Decimal("900")
    assert result.monetary_contribution == Decimal("900")
    assert result.retail_line_matches_total is True


def test_exact_ship_not_added_special_case_avoids_double_deduction():
    result = assess_order_money(_order(total_price_after_sub_discount=900))
    assert result.exception_applied is True
    assert result.after_pattern == "after_equals_total_minus_discount_ship_not_added"
    assert result.revenue_recognized == Decimal("900")
    assert result.price_adjustment == Decimal("0")
    assert result.adj_unexplained is False


def test_positive_adjustment_is_retained_and_classified():
    result = assess_order_money(_order(total_price_after_sub_discount=1050))
    assert result.revenue_recognized == Decimal("950")
    assert result.price_adjustment == Decimal("50")
    assert result.after_pattern == "other_distance_le_10000"
    assert result.adj_unexplained is True


def test_negative_revenue_has_zero_monetary_contribution_but_is_not_gift():
    result = assess_order_money(
        _order(total_discount=0, total_price_after_sub_discount=50)
    )
    assert result.negative_revenue is True
    assert result.negative_revenue_causes == ("after_below_shipping_fee",)
    assert result.is_gift is False
    assert result.revenue_recognized == Decimal("-50")
    assert result.monetary_contribution == Decimal("0")


def test_zero_revenue_is_gift_and_excluded_from_customer_value():
    result = assess_order_money(
        _order(total_discount=1000, shipping_fee=0, total_price_after_sub_discount=0)
    )
    assert result.is_gift is True
    assert result.revenue_recognized == Decimal("0")
    assert result.monetary_contribution is None
    assert result.monetary_A_contribution is None


def test_zero_total_and_zero_after_is_gift_even_when_ship_is_positive():
    result = assess_order_money(
        _order(total_price=0, total_discount=0, shipping_fee=100, total_price_after_sub_discount=0)
    )
    assert result.is_gift is True
    assert result.revenue_recognized == Decimal("0")


def test_cod_value_does_not_change_money_decision():
    ordinary = assess_order_money(_order())
    with_cod_value = assess_order_money(_order(cod=-9999))
    assert ordinary == with_cod_value


def test_non_numeric_or_incomplete_line_items_do_not_produce_partial_totals():
    assert retail_price_quantity_total(
        [
            {"quantity": 1, "variation_info": {"retail_price": 5}},
            {"quantity": None, "variation_info": {"retail_price": 7}},
        ]
    ) is None
