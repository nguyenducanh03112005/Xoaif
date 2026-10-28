from datetime import date

import numpy as np
import pandas as pd

from scripts.analyze_seasonality_dev import (
    _customer_bootstrap_rows,
    channel_group,
    decompose_series,
    event_comparisons,
    merge_event_windows,
)


def test_simple_decomposition_reconstructs_observed_values() -> None:
    frame = pd.DataFrame({
        "period": pd.date_range("2024-01-01", periods=18, freq="MS"),
        "orders": np.arange(1, 19), "recognized_revenue_vnd": np.arange(1, 19) * 100,
    })
    result = decompose_series(frame, freq="month", trend_window=3)
    assert np.allclose(result.orders, result.trend_orders + result.seasonal_orders + result.residual_orders)
    assert np.allclose(result.recognized_revenue_vnd, result.trend_revenue_vnd + result.seasonal_revenue_vnd + result.residual_revenue_vnd)


def test_event_windows_merge_overlapping_events_inside_dev() -> None:
    events = pd.DataFrame([
        {"date": "2024-04-30", "event_type": "public_holiday", "event_name": "A"},
        {"date": "2024-05-01", "event_type": "public_holiday", "event_name": "B"},
        {"date": "2024-09-02", "event_type": "public_holiday", "event_name": "C"},
        {"date": "2026-02-17", "event_type": "tet", "event_name": "outside DEV"},
    ])
    blocks = merge_event_windows(events)
    assert len(blocks) == 2
    assert blocks[0]["event_names"] == ["A", "B"]
    assert blocks[0]["start"] == date(2024, 4, 23)
    assert blocks[0]["end"] == date(2024, 5, 8)


def test_channel_labels_follow_existing_documented_groups() -> None:
    assert channel_group("Facebook Ads") == "Facebook"
    assert channel_group(None) == "Thiếu kênh"
    assert channel_group("Instagram") == "Instagram + nguồn hiếm"
    assert channel_group("Other source") == "Instagram + nguồn hiếm"


def test_customer_bootstrap_uses_customer_level_repeat_and_aov() -> None:
    rows = []
    for i in range(40):
        rows.append({
            "customer_key": f"c{i}", "group": "A", "date": date(2024, 4, 1),
            "revenue_recognized": 100 if i < 20 else 200, "repeat_180d": i < 10,
        })
    result = _customer_bootstrap_rows(rows, "group").iloc[0]
    assert result["customers"] == 40
    assert result["aov_vnd"] == 150
    assert result["retention_180d"] == .25
    assert result["aov_ci_lower_95_vnd"] <= 150 <= result["aov_ci_upper_95_vnd"]
    assert result["retention_ci_lower_95"] <= .25 <= result["retention_ci_upper_95"]


def test_event_comparison_reindexes_daily_dates_and_marks_observational() -> None:
    days = pd.date_range("2024-04-01", "2024-07-10", freq="D")
    daily = pd.DataFrame({"date": days, "orders": 1, "recognized_revenue_vnd": 100})
    events = pd.DataFrame([{"date": "2024-05-10", "event_type": "sale_proxy", "event_name": "proxy"}])
    result = event_comparisons(daily, events, draws=50)
    assert len(result) == 2
    assert result.loc[result.metric == "đơn/ngày", "event_daily_mean"].iloc[0] == 1.0
    assert result.loc[result.metric == "đơn/ngày", "control_daily_mean"].iloc[0] == 1.0
    assert result.loc[result.metric == "doanh thu ghi nhận/ngày", "event_daily_mean"].iloc[0] == 100.0
    assert result.loc[result.metric == "doanh thu ghi nhận/ngày", "control_daily_mean"].iloc[0] == 100.0
    assert set(result.evidence_note) == {"n<30 days; descriptive only"}
