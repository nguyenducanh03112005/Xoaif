from datetime import date

import numpy as np

from scripts.analyze_customer_value_dev import (
    bootstrap_quantile_ci,
    bootstrap_share_ci,
    kaplan_meier_repeat_probability,
    mature_month,
    rfm_action_group,
    returned_within_horizon,
)


def test_month_maturity_respects_exclusive_dev_end():
    dev_end = date(2025, 10, 22)
    assert mature_month("2025-08", 30, dev_end)
    assert not mature_month("2025-09", 30, dev_end)
    assert mature_month("2025-03", 180, dev_end)
    assert not mature_month("2025-04", 180, dev_end)


def test_retention_requires_a_later_purchase_date_and_horizon_is_inclusive():
    first = {"date": date(2025, 1, 1)}
    same_day = {"date": date(2025, 1, 1)}
    day_30 = {"date": date(2025, 1, 31)}
    day_31 = {"date": date(2025, 2, 1)}
    assert not returned_within_horizon([first, same_day], 30)
    assert returned_within_horizon([first, day_30], 30)
    assert not returned_within_horizon([first, day_31], 30)


def test_kaplan_meier_counts_repeat_events_with_right_censoring():
    times = np.array([10, 180, 180])
    events = np.array([1, 0, 0])
    assert kaplan_meier_repeat_probability(times, events, 9) == 0
    assert np.isclose(kaplan_meier_repeat_probability(times, events, 10), 1 / 3)
    assert np.isclose(kaplan_meier_repeat_probability(times, events, 180), 1 / 3)


def test_rfm_action_groups_are_nonoverlapping_and_follow_registered_priority():
    assert rfm_action_group(20, 3, 200, 100) == "Giá trị cao, mua lặp lại gần đây"
    assert rfm_action_group(20, 1, 200, 100) == "Giá trị cao, một đơn"
    assert rfm_action_group(100, 3, 200, 100) == "Mua lặp lại đã lâu"


def test_customer_bootstrap_share_and_quantile_intervals_are_ordered():
    rng = np.random.default_rng(7)
    values = np.array([10, 20, 30, 40, 50], dtype=float)
    flags = np.array([True, False, True, False, True])
    low, high = bootstrap_share_ci(values, flags, rng=rng, draws=100)
    assert 0 <= low <= high <= 1
    low, high = bootstrap_quantile_ci(values, .5, rng=rng, draws=100)
    assert low <= 30 <= high
