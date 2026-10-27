from scripts.reconcile_cohorts import validate_order_funnel


def test_dev_order_funnel_partitions_orders():
    assert validate_order_funnel(6517, 6400, 117)
    assert not validate_order_funnel(6517, 6400, 116)
