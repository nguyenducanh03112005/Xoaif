from datetime import date

import pandas as pd
import pytest

from scripts.evaluate_holiday_time_dev import (
    CALENDAR_END,
    CALENDAR_START,
    add_time_features,
    build_rolling_folds,
    load_calendar,
)


def test_calendar_is_manual_cited_and_inside_requested_period() -> None:
    events = load_calendar()

    assert events
    assert all(CALENDAR_START <= event["date"] <= CALENDAR_END for event in events)
    assert all(event["source_url"].startswith("https://") for event in events)
    assert {event["event_type"] for event in events} == {
        "public_holiday",
        "tet",
        "sale_proxy",
    }


def test_time_features_are_known_at_anchor_and_last_purchase() -> None:
    frame = pd.DataFrame({
        "as_of": ["2025-01-29"],
        "last_purchase_date": ["2024-12-12"],
    })
    features = add_time_features(frame, load_calendar())

    assert features.loc[0, "anchor_is_tet"] == 1
    assert features.loc[0, "last_purchase_is_sale_proxy"] == 1
    assert features.loc[0, "anchor_days_to_tet"] == 0
    assert features.loc[0, "last_purchase_month_sin"] == pytest.approx(-0.5)
    assert features.loc[0, "last_purchase_month_cos"] == pytest.approx(0.8660254)


def test_time_features_reject_dates_outside_calendar() -> None:
    frame = pd.DataFrame({
        "as_of": ["2027-01-01"],
        "last_purchase_date": ["2026-10-30"],
    })

    with pytest.raises(ValueError, match="outside the manually defined calendar"):
        add_time_features(frame, load_calendar())


def test_rolling_origin_requires_mature_labels_and_disjoint_customers() -> None:
    frame = pd.DataFrame({
        "customer_key": [f"train-{index}" for index in range(30)] + ["valid-c", "valid-d"],
        "as_of": (
            ["2024-05-01"] * 15
            + ["2024-06-01"] * 15
            + ["2025-01-01", "2025-01-01"]
        ),
        "label_returned": [index % 2 for index in range(30)] + [0, 1],
    })

    folds = build_rolling_folds(frame)

    assert len(folds) == 1
    assert folds[0]["validation_anchor"] == date(2025, 1, 1)
    assert pd.to_datetime(frame.iloc[folds[0]["train"]]["as_of"]).max().date() == date(2024, 6, 1)
    assert set(frame.iloc[folds[0]["train"]]["customer_key"]).isdisjoint(
        frame.iloc[folds[0]["validation"]]["customer_key"]
    )
