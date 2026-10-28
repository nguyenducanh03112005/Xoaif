"""DEV-only supplementary rolling-origin evaluation of calendar time features."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


ROOT = Path(__file__).resolve().parents[1]
DEV_LABELS = ROOT / "outputs" / "tables" / "day2_label_samples_primary.csv"
CALENDAR = ROOT / "data" / "reference" / "vietnam_holiday_sale_calendar_2024-04_to_2026-10.csv"
RESULT = ROOT / "outputs" / "metrics" / "holiday_time_supplement_dev.json"
CALENDAR_START = date(2024, 4, 1)
CALENDAR_END = date(2026, 10, 31)
LABEL_HORIZON_AND_GAP_DAYS = 187
FIRST_ALLOWED_ANCHOR = date(2024, 5, 1)
LAST_ALLOWED_ANCHOR = date(2025, 4, 1)
THRESHOLD = 0.5

BASE_NUMERIC = [
    "recency_days",
    "frequency",
    "monetary",
    "average_order_value",
    "max_order_value",
    "total_quantity",
    "distinct_products",
    "mean_days_between_orders",
    "first_order_month",
    "first_order_month_sin",
    "first_order_month_cos",
    "nearest_holiday_distance_days",
    "adjustment_positive_rate",
    "adjustment_negative_rate",
    "no_history_after_sensitivity",
]
BASE_CATEGORICAL = ["province"]
RAW_COLUMNS = [
    "customer_key",
    "as_of",
    "last_purchase_date",
    "label_returned",
    *BASE_NUMERIC,
    *BASE_CATEGORICAL,
]
EVENT_TYPES = {"public_holiday", "tet", "sale_proxy"}


def load_calendar(path: Path = CALENDAR) -> list[dict[str, Any]]:
    """Read the manually curated calendar and enforce its narrow date scope."""
    frame = pd.read_csv(path, dtype=str)
    required = {"date", "event_type", "event_name", "source_url"}
    if not required.issubset(frame.columns):
        raise ValueError(f"calendar is missing required columns: {sorted(required - set(frame.columns))}")
    if frame.empty or frame["source_url"].isna().any() or frame["source_url"].str.strip().eq("").any():
        raise ValueError("each calendar row must cite a public source")
    if not set(frame["event_type"]).issubset(EVENT_TYPES):
        raise ValueError("calendar contains an unregistered event type")
    events: list[dict[str, Any]] = []
    for row in frame.to_dict("records"):
        event_date = date.fromisoformat(row["date"])
        if not CALENDAR_START <= event_date <= CALENDAR_END:
            raise ValueError(f"calendar date outside the declared range: {event_date}")
        events.append({**row, "date": event_date})
    if len({(event["date"], event["event_type"]) for event in events}) != len(events):
        raise ValueError("calendar contains duplicate date/type entries")
    return events


def _cyclic(value: float, period: float) -> tuple[float, float]:
    angle = 2.0 * math.pi * value / period
    return math.sin(angle), math.cos(angle)


def add_time_features(frame: pd.DataFrame, events: list[dict[str, Any]]) -> pd.DataFrame:
    """Add deterministic features derived only from known calendar dates."""
    by_type: dict[str, set[date]] = defaultdict(set)
    for event in events:
        by_type[event["event_type"]].add(event["date"])
    public_dates = by_type["public_holiday"] | by_type["tet"]
    if not public_dates or not by_type["tet"] or not by_type["sale_proxy"]:
        raise ValueError("calendar must include public holidays, Tet, and sale proxies")

    enriched = frame.copy()
    date_fields = {"as_of": "anchor", "last_purchase_date": "last_purchase"}
    for source_column, prefix in date_fields.items():
        parsed_dates = pd.to_datetime(enriched[source_column], errors="raise").dt.date
        if any(day < CALENDAR_START or day > CALENDAR_END for day in parsed_dates):
            raise ValueError(f"{source_column} falls outside the manually defined calendar")
        for feature, dates in (
            ("public_holiday", public_dates),
            ("tet", by_type["tet"]),
            ("sale_proxy", by_type["sale_proxy"]),
        ):
            ordered_dates = sorted(dates)
            enriched[f"{prefix}_is_{feature}"] = parsed_dates.map(lambda day: int(day in dates))
            enriched[f"{prefix}_days_to_{feature}"] = parsed_dates.map(
                lambda day: min(abs((day - event_day).days) for event_day in ordered_dates)
            )
        month_sin_cos = parsed_dates.map(lambda day: _cyclic(day.month - 1, 12))
        weekday_sin_cos = parsed_dates.map(lambda day: _cyclic(day.weekday(), 7))
        year_period = parsed_dates.map(lambda day: 366 if _is_leap_year(day.year) else 365)
        day_sin_cos = pd.Series(
            [_cyclic(day.timetuple().tm_yday - 1, period) for day, period in zip(parsed_dates, year_period)],
            index=enriched.index,
        )
        enriched[f"{prefix}_month_sin"] = month_sin_cos.map(lambda pair: pair[0])
        enriched[f"{prefix}_month_cos"] = month_sin_cos.map(lambda pair: pair[1])
        enriched[f"{prefix}_weekday_sin"] = weekday_sin_cos.map(lambda pair: pair[0])
        enriched[f"{prefix}_weekday_cos"] = weekday_sin_cos.map(lambda pair: pair[1])
        enriched[f"{prefix}_day_of_year_sin"] = day_sin_cos.map(lambda pair: pair[0])
        enriched[f"{prefix}_day_of_year_cos"] = day_sin_cos.map(lambda pair: pair[1])
    return enriched


def _is_leap_year(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def build_rolling_folds(frame: pd.DataFrame) -> list[dict[str, Any]]:
    """Build expanding folds where all training labels are mature at validation time."""
    anchor_dates = pd.to_datetime(frame["as_of"], errors="raise").dt.date
    folds: list[dict[str, Any]] = []
    for validation_anchor in sorted(set(anchor_dates)):
        valid = np.flatnonzero(anchor_dates.to_numpy() == validation_anchor)
        train = np.flatnonzero(
            np.asarray([
                anchor + timedelta(days=LABEL_HORIZON_AND_GAP_DAYS) < validation_anchor
                for anchor in anchor_dates
            ])
        )
        if not len(valid):
            continue
        train_labels = frame.iloc[train]["label_returned"].astype(int).to_numpy()
        if len(train) < 30 or len(np.unique(train_labels)) < 2:
            continue
        train_keys = set(frame.iloc[train]["customer_key"])
        valid_keys = set(frame.iloc[valid]["customer_key"])
        if train_keys & valid_keys:
            raise ValueError("customer overlap across rolling-origin train and validation")
        folds.append({
            "validation_anchor": validation_anchor,
            "train": train,
            "validation": valid,
        })
    if not folds:
        raise ValueError("no valid DEV rolling-origin folds satisfy the maturity rule")
    return folds


def _pipeline(numeric: list[str], categorical: list[str]) -> Pipeline:
    numeric_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True)),
        ("scale", StandardScaler()),
    ])
    categorical_pipe = Pipeline([
        ("impute", SimpleImputer(strategy="constant", fill_value="__MISSING__")),
        ("encode", OneHotEncoder(handle_unknown="ignore")),
    ])
    prep = ColumnTransformer([
        ("numeric", numeric_pipe, numeric),
        ("categorical", categorical_pipe, categorical),
    ], remainder="drop")
    return Pipeline([
        ("preprocess", prep),
        ("model", LogisticRegression(
            C=1.0,
            class_weight="balanced",
            max_iter=2000,
            solver="lbfgs",
            random_state=42,
        )),
    ])


def _metrics(y_true: np.ndarray, scores: np.ndarray) -> dict[str, Any]:
    predictions = (scores >= THRESHOLD).astype(int)
    return {
        "sample_count": int(len(y_true)),
        "positive_count": int(y_true.sum()),
        "positive_rate": float(y_true.mean()) if len(y_true) else None,
        "roc_auc": float(roc_auc_score(y_true, scores)) if len(np.unique(y_true)) == 2 else None,
        "pr_auc_average_precision": float(average_precision_score(y_true, scores)) if len(y_true) else None,
        "precision_at_0_5": float(precision_score(y_true, predictions, zero_division=0)),
        "recall_at_0_5": float(recall_score(y_true, predictions, zero_division=0)),
        "f1_at_0_5": float(f1_score(y_true, predictions, zero_division=0)),
        "confusion_matrix_tn_fp_fn_tp_at_0_5": confusion_matrix(
            y_true, predictions, labels=[0, 1]
        ).tolist(),
    }


def _read_dev_labels(path: Path = DEV_LABELS) -> pd.DataFrame:
    if path.resolve() != DEV_LABELS.resolve():
        raise ValueError("only the registered DEV label artifact may be loaded")
    frame = pd.read_csv(path, usecols=RAW_COLUMNS)
    required = set(RAW_COLUMNS)
    if not required.issubset(frame.columns):
        raise ValueError(f"DEV label artifact is missing columns: {sorted(required - set(frame.columns))}")
    frame["as_of"] = pd.to_datetime(frame["as_of"], errors="raise")
    frame["last_purchase_date"] = pd.to_datetime(frame["last_purchase_date"], errors="raise")
    if frame.empty or frame["customer_key"].isna().any() or frame["customer_key"].duplicated().any():
        raise ValueError("DEV input must have one non-null pseudonymous customer key per sample")
    anchors = frame["as_of"].dt.date
    if any(anchor < FIRST_ALLOWED_ANCHOR or anchor > LAST_ALLOWED_ANCHOR for anchor in anchors):
        raise ValueError("DEV input contains an anchor outside the registered DEV sample interval")
    if not (frame["last_purchase_date"] < frame["as_of"]).all():
        raise ValueError("a last-purchase feature is not strictly before its label anchor")
    labels = frame["label_returned"]
    if labels.isna().any() or not set(labels.unique()).issubset({0, 1}):
        raise ValueError("DEV labels must be binary and non-null")
    frame["label_returned"] = labels.astype(int)
    return frame


def _evaluate_feature_set(
    frame: pd.DataFrame,
    folds: list[dict[str, Any]],
    numeric: list[str],
    categorical: list[str],
) -> dict[str, Any]:
    feature_columns = numeric + categorical
    all_y = frame["label_returned"].to_numpy(dtype=int)
    pooled_y: list[int] = []
    pooled_scores: list[float] = []
    fold_results: list[dict[str, Any]] = []
    for fold in folds:
        train = frame.iloc[fold["train"]]
        valid = frame.iloc[fold["validation"]]
        model = _pipeline(numeric, categorical)
        model.fit(train[feature_columns], all_y[fold["train"]])
        classes = list(model.named_steps["model"].classes_)
        probabilities = model.predict_proba(valid[feature_columns])
        scores = probabilities[:, classes.index(1)] if 1 in classes else np.zeros(len(valid))
        fold_y = all_y[fold["validation"]]
        metric = _metrics(fold_y, scores)
        metric["validation_anchor"] = fold["validation_anchor"].isoformat()
        metric["train_sample_count"] = int(len(train))
        metric["train_positive_count"] = int(all_y[fold["train"]].sum())
        metric["train_latest_anchor"] = train["as_of"].max().date().isoformat()
        fold_results.append(metric)
        pooled_y.extend(fold_y.tolist())
        pooled_scores.extend(scores.tolist())

    pooled_y_array = np.asarray(pooled_y, dtype=int)
    pooled_scores_array = np.asarray(pooled_scores, dtype=float)
    return {
        "fixed_estimator": "LogisticRegression(C=1.0, class_weight='balanced', max_iter=2000, solver='lbfgs', random_state=42)",
        "feature_count": len(feature_columns),
        "pooled_oof_metrics": _metrics(pooled_y_array, pooled_scores_array),
        "mean_fold_roc_auc": float(np.mean([row["roc_auc"] for row in fold_results if row["roc_auc"] is not None])),
        "mean_fold_pr_auc_average_precision": float(np.mean([
            row["pr_auc_average_precision"] for row in fold_results
        ])),
        "folds": fold_results,
    }


def run() -> dict[str, Any]:
    """Evaluate the pre-existing DEV feature set against its calendar-augmented version."""
    frame = _read_dev_labels()
    events = load_calendar()
    enhanced = add_time_features(frame, events)
    folds = build_rolling_folds(enhanced)

    time_columns = [
        column for column in enhanced.columns
        if column.startswith(("anchor_", "last_purchase_"))
        and column not in {"last_purchase_date"}
    ]
    numeric_time = [column for column in time_columns if column != "last_purchase_date"]
    result = {
        "label": "khảo sát bổ sung",
        "purpose": "DEV-only, leakage-safe rolling-origin comparison; does not replace the primary model",
        "scope": {
            "input": "outputs/tables/day2_label_samples_primary.csv",
            "samples_available": int(len(frame)),
            "anchor_start": frame["as_of"].min().date().isoformat(),
            "anchor_end": frame["as_of"].max().date().isoformat(),
            "calendar_start_inclusive": CALENDAR_START.isoformat(),
            "calendar_end_inclusive": CALENDAR_END.isoformat(),
            "calendar_event_rows": len(events),
            "pseudonymous_customer_keys_written": False,
            "raw_or_restricted_data_loaded": False,
            "network_calls_made": False,
        },
        "assumptions": [
            "Training labels are eligible only when anchor + 187 days is strictly before the validation anchor, preserving the existing 180-day outcome plus 7-day gap.",
            "The primary feature set and the added time features are compared with the same fixed logistic-regression recipe; no parameter or feature selection is performed.",
            "Sale dates are calendar proxies, not evidence that this shop or a particular platform ran a promotion on each backfilled date.",
            "Holiday and sale calendars are date markers only; they do not establish causal effects.",
        ],
        "fold_plan": [
            {
                "validation_anchor": fold["validation_anchor"].isoformat(),
                "train_sample_count": int(len(fold["train"])),
                "train_positive_count": int(frame.iloc[fold["train"]]["label_returned"].sum()),
                "train_latest_anchor": frame.iloc[fold["train"]]["as_of"].max().date().isoformat(),
                "validation_sample_count": int(len(fold["validation"])),
                "validation_positive_count": int(frame.iloc[fold["validation"]]["label_returned"].sum()),
                "customer_disjoint": True,
            }
            for fold in folds
        ],
        "models": {
            "primary_feature_reference": _evaluate_feature_set(
                frame, folds, BASE_NUMERIC, BASE_CATEGORICAL
            ),
            "calendar_time_augmented": _evaluate_feature_set(
                enhanced, folds, BASE_NUMERIC + numeric_time, BASE_CATEGORICAL
            ),
        },
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, ensure_ascii=False))
