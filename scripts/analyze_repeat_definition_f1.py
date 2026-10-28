"""Audit repeat-purchase event definitions on DEV without overwriting A1 outputs."""

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
from analyze_customer_value_dev import (  # noqa: E402
    HORIZONS, mature_month, cohort_month, kaplan_meier_repeat_probability,
)

SEED = 20261028
DRAWS = 2000
DEV_END = date(2025, 10, 22)


def summarize(orders: list[dict]) -> dict:
    by_customer: dict[str, list[dict]] = defaultdict(list)
    for row in orders:
        if row.get("customer_key") and not row.get("is_gift") and row.get("date") < DEV_END:
            by_customer[str(row["customer_key"])].append(row)
    for rows in by_customer.values():
        rows.sort(key=lambda r: (r["date"], r.get("order_sequence", 0)))

    first_month: dict[str, str] = {}
    for key, rows in by_customer.items():
        first_month[key] = cohort_month(rows[0]["date"])
    mature = [key for key, month in first_month.items() if mature_month(month, 180, DEV_END)]
    times_legacy, events_legacy, times_strict, events_strict = [], [], [], []
    same_day_customers = 0
    for key in mature:
        rows = by_customer[key]
        first = rows[0]["date"]
        later = [r["date"] for r in rows[1:] if r["date"] <= first.fromordinal(first.toordinal() + 180)]
        second = rows[1]["date"] if len(rows) > 1 else None
        legacy_gap = max(0, (second - first).days) if second is not None else 180
        legacy_event = int(second is not None and legacy_gap <= 180)
        strict_days = [(d - first).days for d in later if d > first]
        strict_gap = min(strict_days) if strict_days else 180
        strict_event = int(bool(strict_days) and strict_gap <= 180)
        times_legacy.append(legacy_gap if legacy_event else 180)
        events_legacy.append(legacy_event)
        times_strict.append(strict_gap if strict_event else 180)
        events_strict.append(strict_event)
        same_day_customers += int(second is not None and second == first)

    tl, el = np.asarray(times_legacy, dtype=int), np.asarray(events_legacy, dtype=int)
    ts, es = np.asarray(times_strict, dtype=int), np.asarray(events_strict, dtype=int)
    rng = np.random.default_rng(SEED)
    km_rows = []
    for horizon in HORIZONS:
        vals = {}
        for name, times, events in (("legacy_including_same_day", tl, el), ("strict_later_date", ts, es)):
            point = kaplan_meier_repeat_probability(times, events, horizon)
            boot = np.empty(DRAWS)
            for b in range(DRAWS):
                ix = rng.integers(0, len(times), len(times))
                boot[b] = kaplan_meier_repeat_probability(times[ix], events[ix], horizon)
            vals[name] = {"estimate": point, "ci_lower_95": float(np.quantile(boot, .025)),
                          "ci_upper_95": float(np.quantile(boot, .975)),
                          "n": len(times), "events_by_horizon": int(((events == 1) & (times <= horizon)).sum())}
        km_rows.append({"horizon_days": horizon, **vals,
                        "difference_strict_minus_legacy": vals["strict_later_date"]["estimate"] - vals["legacy_including_same_day"]["estimate"]})

    # Direct event-count retention under one identical mature cohort universe.
    ret_rows = []
    for horizon in HORIZONS:
        count = 0
        for key in mature:
            first = by_customer[key][0]["date"]
            if any(first < r["date"] <= first.fromordinal(first.toordinal() + horizon) for r in by_customer[key][1:]):
                count += 1
        ret_rows.append({"horizon_days": horizon, "customers": len(mature), "repeaters": count,
                         "rate": count / len(mature)})
    all_first = sum(1 for rows in by_customer.values()
                    if any(row["date"] > rows[0]["date"] for row in rows[1:]))
    split_same_day = sum(1 for rows in by_customer.values() if len(rows) > 1 and rows[1]["date"] == rows[0]["date"])
    return {"eligible_dev_customers": len(by_customer), "mature_180d_customers": len(mature),
            "same_day_second_customers_all_dev": split_same_day,
            "strict_repeat_customers_all_dev": all_first,
            "same_day_second_customers_mature_180d": same_day_customers,
            "km": km_rows, "retention_same_mature_universe": ret_rows}


def main() -> int:
    orders, scope, _ = load_dev_orders()
    if scope.get("test_labels_loaded") or scope.get("test_behavior_loaded"):
        raise RuntimeError("DEV loader reported test access")
    result = summarize(orders)
    result.update({"status": "exploratory_dev_only_not_confirmed_out_of_sample",
                   "plan_sha256": hashlib.sha256((ROOT / "docs/analysis_plan_f1.md").read_bytes()).hexdigest(),
                   "seed": SEED, "bootstrap_draws": DRAWS,
                   "test_raw_or_labels_read": False,
                   "definition": "repeat requires a later local calendar date than the first valid order; same-day split orders excluded"})
    (ROOT / "outputs/metrics/repeat_definition_f1.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    pd.DataFrame(result["km"]).to_csv(ROOT / "outputs/tables/repeat_definition_km_f1.csv", index=False, float_format="%.6f")
    pd.DataFrame(result["retention_same_mature_universe"]).to_csv(ROOT / "outputs/tables/repeat_definition_retention_f1.csv", index=False, float_format="%.6f")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
