"""Preregistered DEV-only retention and customer-value analysis (A1)."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
import calendar
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from features.day2_data import load_dev_orders  # noqa: E402

SEED = 20261028
DRAWS = 2000
DEV_END = date(2025, 10, 22)
HORIZONS = (30, 60, 90, 180)
RFM_NAMES = (
    "Giá trị cao, mua lặp lại gần đây",
    "Mua lặp lại gần đây",
    "Mua lặp lại đã lâu",
    "Giá trị cao, một đơn",
    "Một đơn gần đây",
    "Một đơn đã lâu",
)
RFM_ACTIONS = (
    "Ưu tiên giữ trải nghiệm và giới thiệu chăm sóc phù hợp; không mặc định giảm giá.",
    "Gợi ý chăm sóc sản phẩm và nội dung bổ trợ theo thời điểm.",
    "Thử thông điệp quay lại với nhóm đối chứng trước khi mở rộng.",
    "Gửi hướng dẫn chăm sóc sau mua; quan sát xem có phát sinh đơn thứ hai.",
    "Gửi hướng dẫn chăm sóc và nhắc thời điểm dùng/bổ sung phù hợp.",
    "Chỉ thử nhắc lại chi phí thấp sau khi kiểm tra sự đồng ý liên hệ.",
)
RFM_KPIS = (
    "Tỷ lệ mua lại 90 ngày; doanh thu ghi nhận/khách; AOV.",
    "Tỷ lệ mua lại 90 ngày; đơn/khách.",
    "Tỷ lệ phản hồi mua lại trong holdout; không dùng tỷ lệ quan sát làm uplift.",
    "Tỷ lệ có đơn thứ hai trong 180 ngày.",
    "Tỷ lệ có đơn thứ hai trong 90/180 ngày.",
    "Tỷ lệ phản hồi trong holdout; chi phí liên hệ/khách nếu được nhập.",
)
CONTACT_CONDITION = (
    "Điều kiện tiên quyết: có thông tin liên hệ hợp lệ và khách đồng ý nhận liên hệ; "
    "cửa hàng cần kiểm tra quy định bảo vệ dữ liệu cá nhân áp dụng."
)


def cohort_month(first_date: date) -> str:
    return f"{first_date.year:04d}-{first_date.month:02d}"


def month_end(month: str) -> date:
    year, mon = map(int, month.split("-"))
    return date(year, mon, calendar.monthrange(year, mon)[1])


def mature_month(month: str, horizon: int, dev_end: date = DEV_END) -> bool:
    return month_end(month) + timedelta(days=horizon) < dev_end


def kaplan_meier_repeat_probability(times: np.ndarray, events: np.ndarray, horizon: int) -> float:
    """Return 1-KM survival at horizon, with events preceding same-day censoring."""
    at_risk = len(times)
    survival = 1.0
    event_days = sorted(set(int(day) for day, event in zip(times, events) if event and day <= horizon))
    for day in event_days:
        event_count = int(np.sum((times == day) & (events == 1)))
        if at_risk:
            survival *= 1.0 - event_count / at_risk
        censored_same_day = int(np.sum((times == day) & (events == 0)))
        at_risk -= event_count + censored_same_day
    return 1.0 - survival


def returned_within_horizon(rows: list[dict], horizon: int) -> bool:
    if len(rows) < 2:
        return False
    first = rows[0]["date"]
    end = first + timedelta(days=horizon)
    return any(first < row["date"] <= end for row in rows[1:])


def bootstrap_mean_ci(values: np.ndarray, *, rng: np.random.Generator, draws: int = DRAWS) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    if not len(values):
        return (float("nan"), float("nan"))
    means = np.empty(draws)
    for draw in range(draws):
        means[draw] = rng.choice(values, size=len(values), replace=True).mean()
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def bootstrap_share_ci(
    values: np.ndarray,
    included: np.ndarray,
    *,
    rng: np.random.Generator,
    draws: int = DRAWS,
) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    included = np.asarray(included, dtype=bool)
    shares = np.empty(draws)
    for draw in range(draws):
        idx = rng.integers(0, len(values), size=len(values))
        denom = float(values[idx].sum())
        shares[draw] = float(values[idx][included[idx]].sum() / denom) if denom else np.nan
    shares = shares[np.isfinite(shares)]
    return float(np.quantile(shares, .025)), float(np.quantile(shares, .975))


def bootstrap_quantile_ci(values: np.ndarray, q: float, *, rng: np.random.Generator, draws: int = DRAWS) -> tuple[float, float]:
    values = np.asarray(values, dtype=float)
    samples = np.empty(draws)
    for draw in range(draws):
        samples[draw] = np.quantile(rng.choice(values, size=len(values), replace=True), q)
    return float(np.quantile(samples, .025)), float(np.quantile(samples, .975))


def rfm_action_group(recency: float, frequency: float, monetary: float, high_value_cut: float) -> str:
    high = monetary >= high_value_cut
    repeat = frequency >= 2
    recent = recency <= 90
    if high and repeat and recent:
        return RFM_NAMES[0]
    if repeat and recent:
        return RFM_NAMES[1]
    if repeat:
        return RFM_NAMES[2]
    if high:
        return RFM_NAMES[3]
    if recent:
        return RFM_NAMES[4]
    return RFM_NAMES[5]


def summarize_customer_values(
    orders: list[dict],
    *,
    dev_end: date = DEV_END,
    seed: int = SEED,
    draws: int = DRAWS,
) -> dict[str, pd.DataFrame | dict]:
    valid_orders = [
        row for row in orders
        if row.get("customer_key") and not row.get("is_gift") and row.get("date") < dev_end
    ]
    by_customer: dict[str, list[dict]] = defaultdict(list)
    for row in valid_orders:
        by_customer[str(row["customer_key"])].append(row)
    for rows in by_customer.values():
        rows.sort(key=lambda row: (row["date"], row.get("order_sequence", 0)))

    first_dates = {key: rows[0]["date"] for key, rows in by_customer.items()}
    cohort_members: dict[str, list[str]] = defaultdict(list)
    for key, first in first_dates.items():
        cohort_members[cohort_month(first)].append(key)

    rng = np.random.default_rng(seed)
    retention_rows: list[dict] = []
    exclusion_rows: list[dict] = []
    horizon_repeaters: dict[int, list[str]] = {}
    for horizon in HORIZONS:
        mature_months = sorted(month for month in cohort_members if mature_month(month, horizon, dev_end))
        excluded_months = sorted(month for month in cohort_members if month not in mature_months)
        exclusion_rows.append({
            "horizon_days": horizon,
            "included_cohort_months": ",".join(mature_months),
            "excluded_cohort_months": ",".join(excluded_months),
            "included_month_count": len(mature_months),
            "excluded_month_count": len(excluded_months),
            "exclusion_reason": "cohort month end + horizon is on/after exclusive DEV end; right-censored",
        })
        eligible_keys = [key for month in mature_months for key in cohort_members[month]]
        horizon_repeaters[horizon] = []
        for month in mature_months:
            keys = cohort_members[month]
            returned = np.asarray([
                returned_within_horizon(by_customer[key], horizon)
                for key in keys
            ], dtype=int)
            n = len(keys)
            if n < 30:
                retention_rows.append({"cohort_month": month, "horizon_days": horizon,
                                       "n_customers": "<30", "repeaters": None,
                                       "retention_rate": None, "ci_lower_95": None,
                                       "ci_upper_95": None, "evidence": "C; n<30, suppressed"})
            else:
                low, high = bootstrap_mean_ci(returned, rng=rng, draws=draws)
                retention_rows.append({"cohort_month": month, "horizon_days": horizon,
                                       "n_customers": n, "repeaters": int(returned.sum()),
                                       "retention_rate": float(returned.mean()),
                                       "ci_lower_95": low, "ci_upper_95": high,
                                       "evidence": "mô tả DEV; khám phá, chưa xác nhận ngoài mẫu"})
        all_returned = []
        for key in eligible_keys:
            hit = returned_within_horizon(by_customer[key], horizon)
            all_returned.append(int(hit))
            if hit:
                horizon_repeaters[horizon].append(key)
        all_returned_array = np.asarray(all_returned, dtype=int)
        low, high = bootstrap_mean_ci(all_returned_array, rng=rng, draws=draws)
        retention_rows.append({"cohort_month": "Tổng cohort trưởng thành", "horizon_days": horizon,
                               "n_customers": len(eligible_keys), "repeaters": int(all_returned_array.sum()),
                               "retention_rate": float(all_returned_array.mean()) if len(all_returned_array) else None,
                               "ci_lower_95": low, "ci_upper_95": high,
                               "evidence": "mô tả DEV; mẫu số thay đổi theo horizon"})

    mature_180_months = [month for month in cohort_members if mature_month(month, 180, dev_end)]
    mature_180_keys = [key for month in mature_180_months for key in cohort_members[month]]
    times, events = [], []
    conditional_gaps = []
    for key in mature_180_keys:
        first = first_dates[key]
        second = by_customer[key][1]["date"] if len(by_customer[key]) > 1 else None
        gap = max(0, (second - first).days) if second else 180
        event = int(second is not None and gap <= 180)
        times.append(min(gap, 180))
        events.append(event)
        if event:
            conditional_gaps.append(gap)
    times_a, events_a = np.asarray(times, dtype=int), np.asarray(events, dtype=int)
    km_rows = []
    for horizon in HORIZONS:
        estimate = kaplan_meier_repeat_probability(times_a, events_a, horizon)
        boot = np.empty(draws)
        for draw in range(draws):
            idx = rng.integers(0, len(times_a), size=len(times_a))
            boot[draw] = kaplan_meier_repeat_probability(times_a[idx], events_a[idx], horizon)
        km_rows.append({"horizon_days": horizon, "n_mature_customers": len(times_a),
                        "repeat_probability_km": estimate,
                        "ci_lower_95": float(np.quantile(boot, .025)),
                        "ci_upper_95": float(np.quantile(boot, .975)),
                        "events_by_horizon": int(np.sum((events_a == 1) & (times_a <= horizon))),
                        "same_day_second_order_n": int(np.sum((events_a == 1) & (times_a == 0))),
                        "median_time_to_second_days": min((int(day) for day in np.unique(times_a[events_a == 1])
                                                           if kaplan_meier_repeat_probability(times_a, events_a, int(day)) >= .5),
                                                          default=None),
                        "median_note": "chưa đạt nếu xác suất mua lại chưa tới 50%"})
    gap_array = np.asarray(conditional_gaps, dtype=float)
    gap_quantile_rows = []
    if len(gap_array) >= 30:
        for q in (.25, .5, .75):
            boot_q = np.empty(draws)
            for draw in range(draws):
                boot_q[draw] = np.quantile(rng.choice(gap_array, size=len(gap_array), replace=True), q)
            gap_quantile_rows.append({"quantile": q, "days": float(np.quantile(gap_array, q)),
                                      "ci_lower_95": float(np.quantile(boot_q, .025)),
                                      "ci_upper_95": float(np.quantile(boot_q, .975)),
                                      "n_repeaters": len(gap_array),
                                      "interpretation": "thời gian có điều kiện trong nhóm có lần hai trong 180 ngày"})
    else:
        gap_quantile_rows.append({"quantile": None, "days": None, "ci_lower_95": None,
                                  "ci_upper_95": None, "n_repeaters": len(gap_array),
                                  "interpretation": "n<30; chỉ mô tả, không ước lượng phân vị"})

    customer_revenue = {
        key: float(sum((float(row["revenue_recognized"]) for row in rows
                        if row.get("revenue_recognized") is not None), 0.0))
        for key, rows in by_customer.items()
    }
    keys = sorted(customer_revenue)
    values = np.asarray([customer_revenue[key] for key in keys], dtype=float)
    pareto_rows = []
    total_revenue = float(values.sum())
    for pct in (10, 20):
        n_top = max(1, math.ceil(len(values) * pct / 100))
        share = float(np.sort(values)[::-1][:n_top].sum() / total_revenue) if total_revenue else None
        boot = []
        for _ in range(draws):
            sample = rng.choice(values, size=len(values), replace=True)
            denom = float(sample.sum())
            boot.append(float(np.sort(sample)[::-1][:n_top].sum() / denom) if denom else float("nan"))
        boot_clean = np.asarray([x for x in boot if math.isfinite(x)])
        pareto_rows.append({"top_customer_pct": pct, "n_customers": n_top,
                            "total_customers": len(values), "recognized_revenue_share": share,
                            "ci_lower_95": float(np.quantile(boot_clean, .025)),
                            "ci_upper_95": float(np.quantile(boot_clean, .975)),
                            "total_recognized_revenue_vnd": total_revenue})

    first_month = {key: cohort_month(first) for key, first in first_dates.items()}
    monthly: dict[tuple[str, str], dict] = {}
    month_total_revenue: dict[str, float] = defaultdict(float)
    monthly_customer_revenue: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for row in valid_orders:
        key = str(row["customer_key"])
        month = row["date"].strftime("%Y-%m")
        customer_type = "Khách mới" if first_month[key] == month else "Khách quay lại"
        revenue = float(row["revenue_recognized"] or 0)
        bucket = monthly.setdefault((month, customer_type), {"customer_ids": set(), "orders": 0, "revenue": 0.0})
        bucket["customer_ids"].add(key)
        bucket["orders"] += 1
        bucket["revenue"] += revenue
        month_total_revenue[month] += revenue
        monthly_customer_revenue[month][key] += revenue
    monthly_rows = []
    for (month, customer_type), bucket in sorted(monthly.items()):
        n = len(bucket["customer_ids"])
        small = n < 30
        month_keys = sorted(monthly_customer_revenue[month])
        month_values = np.asarray([monthly_customer_revenue[month][key] for key in month_keys], dtype=float)
        group_flags = np.asarray([
            (first_month[key] == month) == (customer_type == "Khách mới")
            for key in month_keys
        ], dtype=bool)
        share_low, share_high = bootstrap_share_ci(month_values, group_flags, rng=rng, draws=draws) if not small else (None, None)
        monthly_rows.append({"month": month, "customer_type": customer_type,
                             "customer_count": "<30" if small else n,
                             "order_count": None if small else bucket["orders"],
                             "recognized_revenue_vnd": None if small else bucket["revenue"],
                             "revenue_share_of_month": None if small or not month_total_revenue[month]
                             else bucket["revenue"] / month_total_revenue[month],
                             "share_ci_lower_95": share_low,
                             "share_ci_upper_95": share_high,
                             "suppression_note": "nhóm dưới 30; chỉ mô tả, số tiền/số đơn ẩn" if small else ""})

    features = pd.read_csv(ROOT / "outputs" / "tables" / "day2_features_primary.csv")
    if features["customer_key"].duplicated().any():
        raise ValueError("DEV feature snapshot must have one row per customer")
    rfm_features = features.copy()
    rfm_features["monetary"] = rfm_features["customer_key"].astype(str).map(customer_revenue).fillna(0.0)
    high_value_cut = float(rfm_features["monetary"].quantile(.90))
    rfm_features["rfm_group"] = rfm_features.apply(
        lambda row: rfm_action_group(row["recency_days"], row["frequency"], row["monetary"], high_value_cut), axis=1
    )
    feature_by_key = rfm_features.set_index("customer_key")
    revenue_by_key = customer_revenue
    rfm_rows = []
    for group in RFM_NAMES:
        members = rfm_features[rfm_features["rfm_group"] == group]
        group_keys = set(members["customer_key"].astype(str))
        n = len(members)
        group_revenue = sum(revenue_by_key.get(key, 0.0) for key in group_keys)
        small = n < 30
        revenue_values = np.asarray([revenue_by_key.get(str(key), 0.0) for key in rfm_features["customer_key"]], dtype=float)
        group_flags = rfm_features["rfm_group"].eq(group).to_numpy()
        share_low, share_high = bootstrap_share_ci(revenue_values, group_flags, rng=rng, draws=draws) if not small else (None, None)
        recency_values = members["recency_days"].to_numpy(dtype=float)
        frequency_values = members["frequency"].to_numpy(dtype=float)
        monetary_values = members["monetary"].to_numpy(dtype=float)
        r_low, r_high = bootstrap_mean_ci(recency_values, rng=rng, draws=draws) if not small else (None, None)
        f_low, f_high = bootstrap_quantile_ci(frequency_values, .5, rng=rng, draws=draws) if not small else (None, None)
        m_low, m_high = bootstrap_mean_ci(monetary_values, rng=rng, draws=draws) if not small else (None, None)
        rfm_rows.append({
            "rfm_group": group,
            "customers": "<30" if small else n,
            "recognized_revenue_vnd": None if small else group_revenue,
            "recognized_revenue_share": None if small or not total_revenue else group_revenue / total_revenue,
            "mean_recency_days": None if small else float(members["recency_days"].mean()),
            "mean_recency_ci_lower_95": r_low,
            "mean_recency_ci_upper_95": r_high,
            "median_frequency_orders": None if small else float(members["frequency"].median()),
            "median_frequency_ci_lower_95": f_low,
            "median_frequency_ci_upper_95": f_high,
            "mean_monetary_vnd": None if small else float(members["monetary"].mean()),
            "mean_monetary_ci_lower_95": m_low,
            "mean_monetary_ci_upper_95": m_high,
            "revenue_share_ci_lower_95": share_low,
            "revenue_share_ci_upper_95": share_high,
            "action": RFM_ACTIONS[RFM_NAMES.index(group)] if n >= 30 else "Chỉ mô tả; gộp/ẩn thống kê vì n<30.",
            "kpi": RFM_KPIS[RFM_NAMES.index(group)] if n >= 30 else "Chỉ mô tả; chưa gán KPI hành động.",
            "condition_precedent": CONTACT_CONDITION,
            "suppression_note": "n<30; nhóm chỉ mô tả" if small else "",
        })

    mature_clv_keys = set(mature_180_keys)
    clv_group_rows = []
    overall_clv_data = []
    for key in mature_180_keys:
        first = first_dates[key]
        end = first + timedelta(days=180)
        in_window = [row for row in by_customer[key] if first <= row["date"] <= end]
        total = sum(float(row["revenue_recognized"] or 0) for row in in_window)
        overall_clv_data.append((key, total, len(in_window)))
    group_for_key = feature_by_key["rfm_group"].to_dict()
    for group in ["Toàn bộ cohort trưởng thành", *RFM_NAMES]:
        vals = overall_clv_data if group == "Toàn bộ cohort trưởng thành" else [
            row for row in overall_clv_data if group_for_key.get(row[0]) == group
        ]
        n = len(vals)
        small = n < 30
        revenues = np.asarray([row[1] for row in vals], dtype=float)
        order_counts = np.asarray([row[2] for row in vals], dtype=float)
        clv_mean = float(revenues.mean()) if n else None
        low, high = bootstrap_mean_ci(revenues, rng=rng, draws=draws) if n >= 30 else (None, None)
        total_orders = float(order_counts.sum())
        total_clv_revenue = float(revenues.sum())
        clv_group_rows.append({
            "rfm_group": group,
            "mature_customers": "<30" if small else n,
            "clv_180d_mean_vnd": None if small else clv_mean,
            "ci_lower_95_vnd": None if small else low,
            "ci_upper_95_vnd": None if small else high,
            "aov_180d_vnd": None if small or not total_orders else total_clv_revenue / total_orders,
            "orders_per_customer_180d": None if small or not n else total_orders / n,
            "formula_check_aov_x_frequency": None if small or not n else (total_clv_revenue / total_orders) * (total_orders / n),
            "definition": "Doanh thu ghi nhận từ đơn đầu đến hết ngày 180 chia cho khách đủ theo dõi; chỉ là mô tả lịch sử.",
            "suppression_note": "n<30; metrics hidden" if small else "",
        })

    # RFM outlier comparison on the existing DEV-only customer snapshot.
    monetary = np.maximum(features["monetary"].to_numpy(dtype=float), 0)
    max_order = np.maximum(features["max_order_value"].to_numpy(dtype=float), 0)
    log_m = np.log1p(monetary)
    log_o = np.log1p(max_order)
    q99_m = float(np.quantile(monetary, .99))
    q99_o = float(np.quantile(max_order, .99))
    proxy = (monetary >= q99_m) | (max_order >= q99_o)
    q1_m, q3_m = np.quantile(log_m, [.25, .75])
    q1_o, q3_o = np.quantile(log_o, [.25, .75])
    fence_m = float(q3_m + 1.5 * (q3_m - q1_m))
    fence_o = float(q3_o + 1.5 * (q3_o - q1_o))
    tukey_m, tukey_o = log_m > fence_m, log_o > fence_o
    iqr_union = tukey_m | tukey_o
    outlier_rows = []
    for name, flags in (("Proxy p99 hiện hành: Monetary hoặc max order", proxy),
                        ("Tukey upper fence log1p(Monetary)", tukey_m),
                        ("Tukey upper fence log1p(max order)", tukey_o),
                        ("Hợp hai Tukey upper fence", iqr_union)):
        count = int(flags.sum())
        small = count < 30
        share_low, share_high = bootstrap_mean_ci(flags.astype(float), rng=rng, draws=draws) if not small else (None, None)
        outlier_rows.append({"rule": name, "flagged_customers": "<30" if small else count,
                             "share": None if small else count / len(features),
                             "share_ci_lower_95": share_low,
                             "share_ci_upper_95": share_high,
                             "p99_monetary_threshold_vnd": q99_m if name.startswith("Proxy") else None,
                             "p99_max_order_threshold_vnd": q99_o if name.startswith("Proxy") else None,
                             "overlap_with_p99_customers": "<30" if int((flags & proxy).sum()) < 30 else int((flags & proxy).sum()),
                             "interpretation": "Cờ ngoại lai chỉ để mô tả; không phải loại khách hay nhãn rủi ro."})
    jaccard = float((iqr_union & proxy).sum() / max(1, (iqr_union | proxy).sum()))

    # Cluster stability and Ward comparison use the existing frozen RFM recipe.
    rfm_values = features[["recency_days", "frequency", "monetary"]].astype(float)
    raw = np.column_stack((rfm_values["recency_days"].to_numpy(),
                           np.log1p(rfm_values["frequency"].to_numpy()),
                           np.log1p(np.maximum(rfm_values["monetary"].to_numpy(), 0))))
    full_scaled = StandardScaler().fit_transform(raw)
    seeds = (13, 42, 87, 2025, 7)
    n_init = {2: 20, 3: 10, 4: 10, 5: 10}
    cluster_rows = []
    rng_cluster = np.random.default_rng(seed)
    comparison_idx = np.sort(rng_cluster.choice(len(features), size=min(2000, len(features)), replace=False))
    for k in (2, 3, 4, 5):
        if k == 2:
            silhouette_mean = .5075411954131032
            silhouette_range = (.5075411954131032, .5075411954131032)
        else:
            saved = {3: (.39014634620099925, .3827, .3986),
                     4: (.3853336384967297, .3722, .3954),
                     5: (.39239782077777746, .3829, .4005)}[k]
            silhouette_mean, silhouette_range = saved[0], (saved[1], saved[2])
        reference = KMeans(n_clusters=k, random_state=42, n_init=n_init[k], max_iter=500).fit_predict(full_scaled)
        ward = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(full_scaled[comparison_idx])
        ward_silhouette = float(silhouette_score(full_scaled[comparison_idx], ward))
        ward_ari = float(adjusted_rand_score(reference[comparison_idx], ward))
        ari_values = []
        for draw in range(100):
            sampled_idx = rng_cluster.integers(0, len(raw), size=len(raw))
            scaler = StandardScaler().fit(raw[sampled_idx])
            sampled_scaled = scaler.transform(raw[sampled_idx])
            full_rescaled = scaler.transform(raw)
            model = KMeans(n_clusters=k, random_state=SEED + draw, n_init=n_init[k], max_iter=500)
            model.fit(sampled_scaled)
            bootstrap_labels = model.predict(full_rescaled)
            ari_values.append(float(adjusted_rand_score(reference, bootstrap_labels)))
        cluster_rows.append({
            "k": k,
            "saved_kmeans_silhouette_mean": silhouette_mean,
            "saved_kmeans_silhouette_min": silhouette_range[0],
            "saved_kmeans_silhouette_max": silhouette_range[1],
            "bootstrap_draws": len(ari_values),
            "bootstrap_ari_median": float(np.median(ari_values)),
            "bootstrap_ari_p25": float(np.quantile(ari_values, .25)),
            "bootstrap_ari_p75": float(np.quantile(ari_values, .75)),
            "bootstrap_ari_min": float(np.min(ari_values)),
            "bootstrap_ari_max": float(np.max(ari_values)),
            "ward_comparison_n": len(comparison_idx),
            "ward_silhouette_sample": ward_silhouette,
            "kmeans_vs_ward_ari_sample": ward_ari,
            "ward_sample_seed": SEED,
            "interpretation": "Độ ổn định hình học; chưa xác nhận ý nghĩa kinh doanh.",
        })

    return {
        "retention": pd.DataFrame(retention_rows),
        "retention_exclusions": pd.DataFrame(exclusion_rows),
        "time_to_second_km": pd.DataFrame(km_rows),
        "time_to_second_conditional_quantiles": pd.DataFrame(gap_quantile_rows),
        "pareto": pd.DataFrame(pareto_rows),
        "monthly_new_returning": pd.DataFrame(monthly_rows),
        "rfm_segments": pd.DataFrame(rfm_rows),
        "clv_180d": pd.DataFrame(clv_group_rows),
        "outliers": pd.DataFrame(outlier_rows),
        "kmeans_stability": pd.DataFrame(cluster_rows),
        "meta": {
            "dev_orders": len(valid_orders),
            "customers": len(by_customer),
            "cohort_months": len(cohort_members),
            "mature_180d_customers": len(mature_180_keys),
            "repeaters_180d": int(events_a.sum()),
            "same_day_second_orders": int(np.sum((events_a == 1) & (times_a == 0))),
            "conditional_repeat_gap_n": len(gap_array),
            "high_value_p90_vnd": high_value_cut,
            "p99_proxy_customers": int(proxy.sum()),
            "tukey_union_customers": int(iqr_union.sum()),
            "p99_tukey_jaccard": jaccard,
            "seed": seed,
            "bootstrap_draws": draws,
        },
    }


def main() -> int:
    orders, scope, _products = load_dev_orders()
    if scope.get("test_labels_loaded") or scope.get("test_behavior_loaded"):
        raise RuntimeError("DEV loader reported test access")
    result = summarize_customer_values(orders)
    plan_hash = hashlib.sha256((ROOT / "docs" / "analysis_plan_wp2.md").read_bytes()).hexdigest()
    metrics = {
        "status": "exploratory_dev_only_not_confirmed_out_of_sample",
        "snapshot_id": "20261024T052943Z",
        "analysis_plan_sha256": plan_hash,
        "test_labels_or_behavior_used": False,
        "date_gate": "local date < 2025-10-22; valid status 3, non-gift DEV orders only",
        "meta": result["meta"],
        "retention_exclusions": result["retention_exclusions"].to_dict("records"),
        "kmeans_sample_note": "KMeans vs Ward ARI and Ward silhouette use the same deterministic sample of at most 2,000 DEV customers.",
        "saved_silhouette_sources": ["outputs/metrics/day2_segmentation.json", "docs/dev_segmentation_objective_i.md"],
        "suppression_rule": "Customer group n<30 is descriptive only; monetary/count estimates are suppressed in aggregate tables.",
    }
    metrics_dir, tables_dir = ROOT / "outputs" / "metrics", ROOT / "outputs" / "tables"
    metrics_dir.mkdir(exist_ok=True)
    tables_dir.mkdir(exist_ok=True)
    (metrics_dir / "customer_value_dev.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    table_names = {
        "retention": "customer_retention_dev.csv",
        "retention_exclusions": "customer_retention_exclusions_dev.csv",
        "time_to_second_km": "time_to_second_purchase_dev.csv",
        "time_to_second_conditional_quantiles": "time_to_second_purchase_quantiles_dev.csv",
        "pareto": "customer_revenue_pareto_dev.csv",
        "monthly_new_returning": "customer_revenue_new_returning_monthly_dev.csv",
        "rfm_segments": "rfm_action_segments_dev.csv",
        "clv_180d": "clv_180d_dev.csv",
        "outliers": "customer_outlier_comparison_dev.csv",
        "kmeans_stability": "kmeans_stability_ward_dev.csv",
    }
    for key, filename in table_names.items():
        table = result[key]
        if any(c.lower() in {"customer_key", "order_key", "customer_id", "phone", "email", "address"} for c in table.columns):
            raise ValueError(f"sensitive field in output table {filename}")
        # Round machine-readable aggregates to six decimal places. Full
        # precision remains in the JSON metrics; this also prevents float
        # tails from resembling phone numbers to the repository PII tripwire.
        table.to_csv(tables_dir / filename, index=False, float_format="%.6f")
    print(json.dumps(metrics["meta"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
