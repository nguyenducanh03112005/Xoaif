"""DEV-only descriptive revenue drivers and explicitly assumed sensitivities."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
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
from analyze_customer_value_dev import DEV_END, mature_month, cohort_month  # noqa: E402

SEED = 20261028
DRAWS = 2000
HIGH_VALUE_CUT = 830_000.0


def _round_json(value):
    if isinstance(value, dict):
        return {key: _round_json(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_round_json(item) for item in value]
    if isinstance(value, (float, np.floating)):
        return round(float(value), 6)
    if isinstance(value, (int, np.integer)):
        return int(value)
    return value


def customer_cohort_rows(orders: list[dict]) -> pd.DataFrame:
    by_customer: dict[str, list[dict]] = defaultdict(list)
    for r in orders:
        if r.get("customer_key") and not r.get("is_gift") and r.get("date") < DEV_END:
            by_customer[str(r["customer_key"])].append(r)
    totals = {k: sum(float(r.get("monetary_contribution") or 0) for r in rs) for k, rs in by_customer.items()}
    p90 = HIGH_VALUE_CUT
    output = []
    for key, rs in by_customer.items():
        rs.sort(key=lambda r: (r["date"], r.get("order_sequence", 0)))
        first = rs[0]
        month = cohort_month(first["date"])
        if not mature_month(month, 180, DEV_END):
            continue
        end = first["date"].fromordinal(first["date"].toordinal() + 180)
        window = [r for r in rs if first["date"] <= r["date"] <= end]
        revenue = sum(float(r.get("revenue_recognized") or 0) for r in window)
        first_revenue = float(first.get("revenue_recognized") or 0)
        orders_n = len(window)
        output.append({"customer_key": key, "cohort_month": month,
                       "revenue_180d": revenue, "first_order_revenue": first_revenue,
                       "orders_180d": orders_n,
                       "repeat_180d": int(any(first["date"] < r["date"] <= end for r in window[1:])),
                       "high_value": int(totals[key] >= p90),
                       "first_order_value_positive": int(first_revenue > 0)})
    return pd.DataFrame(output)


def _summary(frame: pd.DataFrame) -> dict[str, float]:
    revenue = frame.revenue_180d.to_numpy(dtype=float)
    orders = frame.orders_180d.to_numpy(dtype=float)
    first = frame.first_order_revenue.to_numpy(dtype=float)
    total_revenue = float(revenue.sum())
    total_orders = float(orders.sum())
    return {"customers": int(len(frame)), "revenue_180d": total_revenue,
            "clv180_vnd": float(revenue.mean()),
            "orders_per_customer": float(orders.mean()),
            "aov_vnd": float(total_revenue / total_orders) if total_orders else 0.0,
            "first_order_share": float(first.sum() / total_revenue) if total_revenue else 0.0,
            "repeat_rate_180d": float(frame.repeat_180d.mean())}


def analyze(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    monthly = pd.DataFrame([{"cohort_month": month, **_summary(group)}
                            for month, group in frame.groupby("cohort_month", sort=True)])
    rng = np.random.default_rng(SEED)
    scenario_names = ["Khách mới +10%", "AOV +5%", "Mua lại +1 điểm %", "Mua lại +3 điểm %",
                      "Mua lại +5 điểm %", "Giữ thêm 5 điểm % khách high-value"]
    point = _summary(frame)
    high = frame[frame.high_value == 1]
    effects = {
        scenario_names[0]: point["revenue_180d"] * .10,
        scenario_names[1]: point["revenue_180d"] * .05,
        scenario_names[2]: point["customers"] * .01 * point["aov_vnd"],
        scenario_names[3]: point["customers"] * .03 * point["aov_vnd"],
        scenario_names[4]: point["customers"] * .05 * point["aov_vnd"],
        scenario_names[5]: len(high) * .05 * (float(high.revenue_180d.mean()) if len(high) else 0.0),
    }
    boot: dict[str, list[float]] = {name: [] for name in scenario_names}
    base_boot: dict[str, list[float]] = {key: [] for key in
        ("revenue_180d", "clv180_vnd", "orders_per_customer", "aov_vnd", "first_order_share", "repeat_rate_180d")}
    monthly_boot: dict[str, dict[str, list[float]]] = {
        m: {key: [] for key in ("revenue_180d", "clv180_vnd", "orders_per_customer", "aov_vnd", "first_order_share", "repeat_rate_180d")}
        for m in sorted(frame.cohort_month.unique())}
    groups = {m: g.reset_index(drop=True) for m, g in frame.groupby("cohort_month", sort=True)}
    for _ in range(DRAWS):
        pieces = [g.iloc[rng.integers(0, len(g), size=len(g))] for g in groups.values()]
        sample = pd.concat(pieces, ignore_index=True)
        s = _summary(sample)
        for key in base_boot:
            base_boot[key].append(float(s[key]))
        hi = sample[sample.high_value == 1]
        vals = [s["revenue_180d"] * .10, s["revenue_180d"] * .05,
                s["customers"] * .01 * s["aov_vnd"], s["customers"] * .03 * s["aov_vnd"],
                s["customers"] * .05 * s["aov_vnd"], len(hi) * .05 * (hi.revenue_180d.mean() if len(hi) else 0)]
        for name, value in zip(scenario_names, vals):
            boot[name].append(float(value))
        for month, g in groups.items():
            b = g.iloc[rng.integers(0, len(g), size=len(g))]
            b_summary = _summary(b)
            for key in monthly_boot[month]:
                monthly_boot[month][key].append(float(b_summary[key]))
    scenarios = []
    for name in scenario_names:
        values = np.asarray(boot[name])
        scenarios.append({"scenario": name, "assumed_incremental_revenue_vnd": effects[name],
                          "ci_lower_95_vnd": float(np.quantile(values, .025)),
                          "ci_upper_95_vnd": float(np.quantile(values, .975)),
                          "label": "giả định minh họa, không phải dự báo, không phải lợi nhuận"})
    for _, row in monthly.iterrows():
        values = monthly_boot[row.cohort_month]
        for metric, suffix in (("revenue_180d", "revenue"), ("clv180_vnd", "clv180"),
                               ("aov_vnd", "aov"), ("orders_per_customer", "orders_per_customer"),
                               ("first_order_share", "first_order_share"), ("repeat_rate_180d", "repeat_rate")):
            monthly.loc[monthly.cohort_month == row.cohort_month, f"{suffix}_ci_lower_95"] = np.quantile(values[metric], .025)
            monthly.loc[monthly.cohort_month == row.cohort_month, f"{suffix}_ci_upper_95"] = np.quantile(values[metric], .975)
    base_ci = {key: {"lower_95": float(np.quantile(values, .025)),
                     "upper_95": float(np.quantile(values, .975))}
               for key, values in base_boot.items()}
    return monthly, pd.DataFrame(scenarios), {"base": point, "base_bootstrap_95": base_ci,
        "high_value_customers": int(len(high)),
        "high_value_clv180_vnd": float(high.revenue_180d.mean()) if len(high) else None,
        "high_value_sample_n": int(len(high)), "seed": SEED, "bootstrap_draws": DRAWS}


def main() -> int:
    orders, scope, _ = load_dev_orders()
    if scope.get("test_labels_loaded") or scope.get("test_behavior_loaded"):
        raise RuntimeError("DEV loader reported test access")
    customers = customer_cohort_rows(orders)
    monthly, scenarios, summary = analyze(customers)
    plan_hash = hashlib.sha256((ROOT / "docs/analysis_plan_f5.md").read_bytes()).hexdigest()
    channel = pd.read_csv(ROOT / "outputs/tables/channel_behavior_dev.csv")
    channel["coverage_note"] = "Chỉ có nguồn kênh 62,64% orders theo A3; association only"
    metrics = {"status": "exploratory_dev_only_not_confirmed_out_of_sample",
               "plan_sha256": plan_hash, "test_raw_or_labels_read": False,
               **summary, "channel_source_order_coverage": .6264,
               "first_basket_note": "First order value share computed at transaction row level; same-day split orders remain in 180-day revenue, not repeat-event count."}
    (ROOT / "outputs/metrics/revenue_scenarios_f5.json").write_text(json.dumps(_round_json(metrics), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    monthly.to_csv(ROOT / "outputs/tables/revenue_drivers_month_f5.csv", index=False, float_format="%.6f")
    scenarios.to_csv(ROOT / "outputs/tables/revenue_sensitivity_f5.csv", index=False, float_format="%.6f")
    channel.to_csv(ROOT / "outputs/tables/revenue_channel_f5.csv", index=False, float_format="%.6f")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(scenarios.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
