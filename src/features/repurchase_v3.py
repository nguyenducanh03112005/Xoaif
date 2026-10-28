"""DEV-only multi-snapshot data and temporal folds for repurchase v3."""

from __future__ import annotations

from datetime import date, timedelta
import math
from typing import Any

import pandas as pd

from features.day2_data import LABEL_T_CANDIDATES, make_customer_features


def build_multisnapshot_samples(
    orders: list[dict[str, Any]],
    *,
    test_start: date,
    n_days: int = 180,
    l_days: int = 7,
    candidates: tuple[date, ...] = LABEL_T_CANDIDATES,
) -> pd.DataFrame:
    """Build one point-in-time sample per eligible customer at every T."""
    usable = [
        row for row in orders
        if row.get("customer_key") and not row.get("is_gift")
        and isinstance(row.get("date"), date)
        and row["date"] < test_start
    ]
    by_customer: dict[str, list[dict[str, Any]]] = {}
    for row in usable:
        by_customer.setdefault(str(row["customer_key"]), []).append(row)

    eligible_t = tuple(
        t for t in candidates if t + timedelta(days=n_days + l_days) < test_start
    )
    samples: list[dict[str, Any]] = []
    for t in eligible_t:
        eligible_keys = {
            key for key, records in by_customer.items()
            if any(record["date"] < t for record in records)
        }
        if not eligible_keys:
            continue
        features = make_customer_features(
            usable,
            as_of=t,
            customer_keys=eligible_keys,
            analysis_start=min(row["date"] for row in usable),
        )
        for feature in features:
            key = str(feature["customer_key"])
            label = int(any(
                t < record["date"] <= t + timedelta(days=n_days)
                for record in by_customer[key]
            ))
            month_angle = 2 * math.pi * t.month / 12
            samples.append({
                **feature,
                "as_of": t.isoformat(),
                "first_purchase_age_days": (
                    (t - date.fromisoformat(feature["first_purchase_date"])).days
                    if feature.get("first_purchase_date") else 0
                ),
                "t_month_sin": math.sin(month_angle),
                "t_month_cos": math.cos(month_angle),
                "label_returned": label,
            })
    frame = pd.DataFrame(samples)
    if frame.empty:
        raise ValueError("no eligible DEV snapshots were created")
    if (pd.to_datetime(frame["as_of"]).dt.date + pd.to_timedelta(n_days + l_days, unit="D") >= test_start).any():
        raise ValueError("a label maturity interval reaches the reserved test window")
    if (pd.to_datetime(frame["as_of"]).dt.date >= test_start).any():
        raise ValueError("snapshot T reaches the reserved test window")
    return frame


def build_multisnapshot_folds(
    frame: pd.DataFrame,
    *,
    n_days: int = 180,
    l_days: int = 7,
    minimum_train_rows: int = 30,
) -> list[dict[str, Any]]:
    """Forward temporal folds; repeated customers are allowed across folds."""
    dates = pd.to_datetime(frame["as_of"]).dt.date
    folds: list[dict[str, Any]] = []
    for validation_t in sorted(set(dates)):
        validation_idx = (dates == validation_t).to_numpy().nonzero()[0]
        train_idx = (
            (dates + pd.to_timedelta(n_days + l_days, unit="D") < validation_t)
        ).to_numpy().nonzero()[0]
        if len(train_idx) < minimum_train_rows or frame.iloc[train_idx]["label_returned"].nunique() < 2:
            continue
        folds.append({
            "train": train_idx,
            "validation": validation_idx,
            "validation_t": validation_t,
            "customer_overlap_n": len(
                set(frame.iloc[train_idx]["customer_key"])
                & set(frame.iloc[validation_idx]["customer_key"])
            ),
        })
    return folds
