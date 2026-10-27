from scripts.reconcile_cohorts import cohort_bridge_deltas, validate_order_funnel


def test_dev_order_funnel_partitions_orders():
    assert validate_order_funnel(6517, 6400, 117)
    assert not validate_order_funnel(6517, 6400, 116)


def test_published_customer_bridge_arithmetic_is_explicit():
    assert cohort_bridge_deltas(5499, 5174, 5169) == (325, 5, 330)
