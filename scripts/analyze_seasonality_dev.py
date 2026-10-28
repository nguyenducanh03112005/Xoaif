"""Exploratory DEV-only time series, event, channel, and price analyses."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from features.day2_data import load_dev_orders  # noqa: E402

DEV_START = date(2024, 4, 1)
DEV_END = date(2025, 10, 22)
SEED = 20261028
DRAWS = 2000
MIN_N = 30


def decompose_series(frame: pd.DataFrame, *, freq: str, trend_window: int) -> pd.DataFrame:
    """Simple moving-average trend + repeated calendar-period seasonal mean."""
    result = frame.copy().sort_values("period").reset_index(drop=True)
    result["period"] = pd.to_datetime(result["period"])
    result["trend_orders"] = result["orders"].rolling(trend_window, center=True, min_periods=1).mean()
    result["trend_revenue_vnd"] = result["recognized_revenue_vnd"].rolling(trend_window, center=True, min_periods=1).mean()
    if freq == "month":
        result["season_key"] = result["period"].dt.month.astype(str)
    elif freq == "week":
        result["season_key"] = result["period"].dt.isocalendar().week.astype(str)
    else:
        raise ValueError("freq must be month or week")
    for value, trend, seasonal, residual in (
        ("orders", "trend_orders", "seasonal_orders", "residual_orders"),
        ("recognized_revenue_vnd", "trend_revenue_vnd", "seasonal_revenue_vnd", "residual_revenue_vnd"),
    ):
        detrended = result[value] - result[trend]
        seasonal_means = detrended.groupby(result["season_key"]).mean()
        seasonal_counts = result["season_key"].map(result["season_key"].value_counts())
        result[seasonal] = result["season_key"].map(seasonal_means).where(seasonal_counts >= 2, 0.0)
        result[residual] = result[value] - result[trend] - result[seasonal]
    result["seasonal_repetition_count"] = result["season_key"].map(result["season_key"].value_counts()).astype(int)
    result["seasonality_supported_repeated_period"] = result["seasonal_repetition_count"] >= 2
    return result.drop(columns="season_key")


def merge_event_windows(events: pd.DataFrame, *, start: date = DEV_START, end: date = DEV_END, radius: int = 7) -> list[dict]:
    """Clip event +/- radius windows to DEV and merge overlapping windows."""
    candidates = []
    for row in events.to_dict("records"):
        event_date = pd.Timestamp(row["date"]).date()
        if not start <= event_date < end:
            continue
        candidates.append({
            "start": max(start, event_date - timedelta(days=radius)),
            "end": min(end - timedelta(days=1), event_date + timedelta(days=radius)),
            "event_dates": [event_date.isoformat()], "event_names": [str(row["event_name"])],
            "event_types": [str(row["event_type"])],
        })
    candidates.sort(key=lambda row: row["start"])
    merged: list[dict] = []
    for candidate in candidates:
        if merged and candidate["start"] <= merged[-1]["end"]:
            prior = merged[-1]
            prior["end"] = max(prior["end"], candidate["end"])
            for key in ("event_dates", "event_names", "event_types"):
                prior[key].extend(candidate[key])
        else:
            merged.append(candidate)
    for index, block in enumerate(merged, start=1):
        block["block_id"] = f"E{index:02d}"
        block["event_names"] = sorted(set(block["event_names"]))
        block["event_types"] = sorted(set(block["event_types"]))
        block["event_dates"] = sorted(set(block["event_dates"]))
    return merged


def channel_group(value: str | None) -> str:
    if not value or not str(value).strip():
        return "Thiếu kênh"
    normalized = str(value).strip().lower()
    if "facebook" in normalized:
        return "Facebook"
    return "Instagram + nguồn hiếm"


def _bootstrap_mean(values: np.ndarray, rng: np.random.Generator, draws: int = DRAWS) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    samples = values[rng.integers(0, len(values), size=(draws, len(values)))].mean(axis=1)
    return float(np.quantile(samples, .025)), float(np.quantile(samples, .975))


def _block_bootstrap_pair(event: np.ndarray, control: np.ndarray, *, seed: int = SEED, draws: int = DRAWS, block: int = 7) -> dict:
    event = np.asarray(event, dtype=float)
    control = np.asarray(control, dtype=float)
    if not len(event) or not len(control):
        return {"difference_ci_low": None, "difference_ci_high": None, "ratio_ci_low": None, "ratio_ci_high": None}
    rng = np.random.default_rng(seed)
    differences = np.empty(draws); ratios = np.empty(draws)
    for i in range(draws):
        def sample(values: np.ndarray) -> np.ndarray:
            starts = rng.integers(0, len(values), size=int(np.ceil(len(values) / block)))
            positions = (starts[:, None] + np.arange(block)[None, :]) % len(values)
            return values[positions.ravel()[:len(values)]]
        e = sample(event); c = sample(control)
        differences[i] = e.mean() - c.mean()
        ratios[i] = e.mean() / c.mean() if c.mean() else np.nan
    finite = ratios[np.isfinite(ratios)]
    return {
        "difference_ci_low": float(np.quantile(differences, .025)),
        "difference_ci_high": float(np.quantile(differences, .975)),
        "ratio_ci_low": float(np.quantile(finite, .025)) if len(finite) else None,
        "ratio_ci_high": float(np.quantile(finite, .975)) if len(finite) else None,
    }


def event_comparisons(daily: pd.DataFrame, events: pd.DataFrame, *, seed: int = SEED, draws: int = DRAWS) -> pd.DataFrame:
    blocks = merge_event_windows(events)
    daily_map = daily.copy()
    daily_map["date_key"] = pd.to_datetime(daily_map["date"]).dt.date
    daily_map = daily_map.set_index("date_key").drop(columns="date")
    all_event_dates = set()
    for block in blocks:
        all_event_dates.update(pd.date_range(block["start"], block["end"], freq="D").date)
    rows = []
    offsets = (-56, -49, -42, -35, -28, 28, 35, 42, 49, 56)
    for block_index, block in enumerate(blocks):
        event_dates = list(pd.date_range(block["start"], block["end"], freq="D").date)
        control_dates = set()
        for event_date in block["event_dates"]:
            anchor = date.fromisoformat(event_date)
            for offset in offsets:
                control_date = anchor + timedelta(days=offset)
                if DEV_START <= control_date < DEV_END and control_date not in all_event_dates:
                    control_dates.add(control_date)
        control_dates = sorted(control_dates)
        if not control_dates:
            continue
        event_frame = daily_map.reindex(event_dates).fillna(0)
        control_frame = daily_map.reindex(control_dates).fillna(0)
        for value, label in (("orders", "đơn/ngày"), ("recognized_revenue_vnd", "doanh thu ghi nhận/ngày")):
            event_values = event_frame[value].to_numpy(dtype=float)
            control_values = control_frame[value].to_numpy(dtype=float)
            bootstrap = _block_bootstrap_pair(event_values, control_values, seed=seed + block_index, draws=draws)
            rows.append({
                "block_id": block["block_id"], "event_names": "; ".join(block["event_names"]),
                "event_types": "; ".join(block["event_types"]), "event_dates": "; ".join(block["event_dates"]),
                "event_start": block["start"].isoformat(), "event_end": block["end"].isoformat(), "metric": label,
                "event_days": len(event_dates), "control_days": len(control_dates),
                "event_daily_mean": float(event_values.mean()), "control_daily_mean": float(control_values.mean()),
                "difference_event_minus_control": float(event_values.mean() - control_values.mean()),
                "ratio_event_over_control": float(event_values.mean() / control_values.mean()) if control_values.mean() else None,
                **bootstrap,
                "evidence_note": "n<30 days; descriptive only" if min(len(event_dates), len(control_dates)) < MIN_N else "observational, not causal",
            })
    return pd.DataFrame(rows)


def _customer_bootstrap_rows(rows: list[dict], group_key: str, *, seed: int = SEED) -> pd.DataFrame:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if row.get("customer_key"):
            grouped[str(row["customer_key"])].append(row)
    by_group: dict[str, list[tuple[str, list[dict]]]] = defaultdict(list)
    for customer, customer_rows in grouped.items():
        by_group[str(customer_rows[0].get(group_key, "Không rõ"))].append((customer, customer_rows))
    out = []
    rng = np.random.default_rng(seed)
    for group, customers in sorted(by_group.items()):
        n = len(customers)
        order_values = np.array([float(order["revenue_recognized"]) for _, values in customers for order in values])
        repeat_values = np.array([float(bool(rows[0].get("repeat_180d", False))) for _, rows in customers])
        if n < MIN_N:
            out.append({"group": group, "customers": n, "orders": len(order_values), "aov_vnd": None, "retention_180d": None, "suppression_note": "n<30; chỉ mô tả"})
            continue
        # Customer-level mean bill values for AOV; each customer's orders stay together in resampling.
        customer_revenue_totals = np.array([sum(float(order["revenue_recognized"]) for order in values) for _, values in customers])
        customer_order_counts = np.array([len(values) for _, values in customers])
        aov = float(customer_revenue_totals.sum() / customer_order_counts.sum())
        aov_indices = rng.integers(0, n, size=(DRAWS, n))
        aov_draws = customer_revenue_totals[aov_indices].sum(axis=1) / customer_order_counts[aov_indices].sum(axis=1)
        ret_draws = repeat_values[rng.integers(0, n, size=(DRAWS, n))].mean(axis=1)
        out.append({
            "group": group, "customers": n, "orders": len(order_values),
            "aov_vnd": aov, "aov_ci_lower_95_vnd": float(np.quantile(aov_draws, .025)),
            "aov_ci_upper_95_vnd": float(np.quantile(aov_draws, .975)),
            "retention_180d": float(repeat_values.mean()), "retention_ci_lower_95": float(np.quantile(ret_draws, .025)),
            "retention_ci_upper_95": float(np.quantile(ret_draws, .975)), "suppression_note": "",
        })
    return pd.DataFrame(out)


def analyze_orders(orders: list[dict], calendar: pd.DataFrame, *, plan_sha256: str) -> dict[str, pd.DataFrame | dict]:
    eligible = [row for row in orders if not row["is_gift"] and row["date"] < DEV_END]
    daily = pd.DataFrame([{"date": row["date"], "orders": 1, "recognized_revenue_vnd": float(row["revenue_recognized"])} for row in eligible])
    date_index = pd.date_range(DEV_START, DEV_END - timedelta(days=1), freq="D")
    daily = daily.groupby("date", as_index=True).sum().reindex(date_index.date, fill_value=0).rename_axis("date").reset_index()
    daily["date"] = pd.to_datetime(daily["date"])
    monthly = daily.set_index("date").resample("MS").sum().reset_index().rename(columns={"date": "period"})
    weekly = daily.set_index("date").resample("W-MON", label="left", closed="left").sum().reset_index().rename(columns={"date": "period"})
    monthly = decompose_series(monthly, freq="month", trend_window=3)
    weekly = decompose_series(weekly, freq="week", trend_window=13)
    calendar_dev = calendar.copy()
    calendar_dev["date"] = pd.to_datetime(calendar_dev["date"]).dt.date
    calendar_dev = calendar_dev[(calendar_dev["date"] >= DEV_START) & (calendar_dev["date"] < DEV_END)]
    events = event_comparisons(daily, calendar_dev)

    grouped_customers: dict[str, list[dict]] = defaultdict(list)
    for order in eligible:
        if order.get("customer_key"):
            grouped_customers[str(order["customer_key"])].append(order)
    mature_first_orders = []
    for customer, rows in grouped_customers.items():
        rows.sort(key=lambda row: (row["date"], row["order_sequence"]))
        first = rows[0]
        if first["date"] + timedelta(days=180) >= DEV_END:
            continue
        later_dates = [row["date"] for row in rows if first["date"] < row["date"] <= first["date"] + timedelta(days=180)]
        first_copy = dict(first)
        first_copy["customer_key"] = customer
        first_copy["repeat_180d"] = bool(later_dates)
        first_copy["channel_group"] = channel_group(first.get("order_channel"))
        mature_first_orders.append(first_copy)
    # One row/customer makes the cluster bootstrap unit explicit for channel/price analyses.
    channels = _customer_bootstrap_rows(mature_first_orders, "channel_group")

    positive_discount_rates = [
        float(row["total_discount_at_snapshot"] / row["total_price_at_snapshot"])
        for row in mature_first_orders
        if row.get("total_discount_at_snapshot") is not None and row.get("total_price_at_snapshot")
        and row["total_price_at_snapshot"] > 0 and row["total_discount_at_snapshot"] > 0
    ]
    positive_cut = float(np.median(positive_discount_rates)) if positive_discount_rates else 0.0
    for row in mature_first_orders:
        total = row.get("total_price_at_snapshot")
        discount = row.get("total_discount_at_snapshot")
        if total is None or total <= 0 or discount is None:
            row["discount_group"] = "Không đủ trường giá"
        elif discount <= 0:
            row["discount_group"] = "Không có giảm giá ghi nhận"
        elif float(discount / total) <= positive_cut:
            row["discount_group"] = "Tỷ lệ giảm dương thấp"
        else:
            row["discount_group"] = "Tỷ lệ giảm dương cao"
        adjustment = row.get("price_adjustment")
        row["adjustment_group"] = "Không đủ dữ liệu" if adjustment is None else (
            "Âm" if adjustment < 0 else "Dương" if adjustment > 0 else "Bằng 0"
        )
    discount_groups = _customer_bootstrap_rows(mature_first_orders, "discount_group")
    adjustment_groups = _customer_bootstrap_rows(mature_first_orders, "adjustment_group")
    channel_coverage = sum(bool(row.get("order_channel")) for row in eligible) / len(eligible) if eligible else 0.0
    return {
        "monthly_series": monthly, "weekly_series": weekly, "holiday_event_comparisons": events,
        "channel_summary": channels, "discount_groups": discount_groups, "price_adjustment_groups": adjustment_groups,
        "meta": {
            "analysis_plan_sha256": plan_sha256, "status": "exploratory_dev_only_not_confirmed_out_of_sample",
            "test_raw_or_labels_read": False, "source": "load_dev_orders() with local date gate",
            "seed": SEED, "bootstrap_draws": DRAWS, "dev_status3_non_gift_orders": len(eligible),
            "daily_series_days": len(daily), "monthly_periods": len(monthly), "weekly_periods": len(weekly),
            "calendar_event_rows_in_dev": len(calendar_dev), "merged_event_blocks": int(events["block_id"].nunique()) if not events.empty else 0,
            "event_metric_comparisons": len(events), "channel_field_order_coverage": channel_coverage,
            "mature_first_order_customers": len(mature_first_orders), "positive_discount_rate_median": positive_cut,
            "holiday_seasonality_note": "Chỉ một Tết trọn vẹn trong DEV; event/sale results are observational.",
        },
    }


def main() -> int:
    orders, _, _ = load_dev_orders()
    calendar_path = ROOT / "data" / "reference" / "vietnam_holiday_sale_calendar_2024-04_to_2026-10.csv"
    calendar = pd.read_csv(calendar_path)
    plan = ROOT / "docs" / "analysis_plan_wp4.md"
    digest = hashlib.sha256(plan.read_bytes()).hexdigest()
    result = analyze_orders(orders, calendar, plan_sha256=digest)
    tables = ROOT / "outputs" / "tables"
    files = {
        "monthly_series": "seasonality_monthly_dev.csv", "weekly_series": "seasonality_weekly_dev.csv",
        "holiday_event_comparisons": "holiday_event_comparisons_dev.csv", "channel_summary": "channel_behavior_dev.csv",
        "discount_groups": "discount_behavior_dev.csv", "price_adjustment_groups": "price_adjustment_behavior_dev.csv",
    }
    for key, filename in files.items():
        result[key].to_csv(tables / filename, index=False, float_format="%.6f")
    metrics_path = ROOT / "outputs" / "metrics" / "seasonality_business_dev.json"
    metrics_path.write_text(json.dumps(result["meta"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["meta"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
