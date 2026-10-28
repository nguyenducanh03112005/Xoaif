"""Describe DEV repurchase base-rate drift by first-purchase cohort and CV fold."""

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
from features.repurchase_v3 import build_multisnapshot_folds, build_multisnapshot_samples  # noqa: E402
from analyze_customer_value_dev import mature_month, cohort_month  # noqa: E402

DEV_END = date(2025, 10, 22)
SEED = 20261028
DRAWS = 2000


def cohort_rates(orders: list[dict]) -> pd.DataFrame:
    customers: dict[str, list[dict]] = defaultdict(list)
    for r in orders:
        if r.get("customer_key") and not r.get("is_gift") and r.get("date") < DEV_END:
            customers[str(r["customer_key"])].append(r)
    rows = []
    for key, records in customers.items():
        records.sort(key=lambda r: (r["date"], r.get("order_sequence", 0)))
        first = records[0]["date"]
        month = cohort_month(first)
        if not mature_month(month, 180, DEV_END):
            continue
        returned = int(any(first < r["date"] <= first.fromordinal(first.toordinal() + 180) for r in records[1:]))
        rows.append({"customer_key": key, "cohort_month": month, "returned_180d": returned})
    return pd.DataFrame(rows)


def trend_bootstrap(frame: pd.DataFrame) -> dict:
    months = sorted(frame.cohort_month.unique())
    month_index = {m: i for i, m in enumerate(months)}
    grouped = {m: frame[frame.cohort_month == m].returned_180d.to_numpy(dtype=int) for m in months}
    points = np.array([float(grouped[m].mean()) for m in months])
    x = np.arange(len(months), dtype=float)
    point_slope = float(np.polyfit(x, points, 1)[0])
    rng = np.random.default_rng(SEED)
    slopes = np.empty(DRAWS)
    for i in range(DRAWS):
        rates = [float(rng.choice(grouped[m], size=len(grouped[m]), replace=True).mean()) for m in months]
        slopes[i] = np.polyfit(x, rates, 1)[0]
    return {"months": len(months), "slope_rate_per_month": point_slope,
            "slope_pp_per_month": point_slope * 100,
            "ci_lower_95_pp_per_month": float(np.quantile(slopes, .025) * 100),
            "ci_upper_95_pp_per_month": float(np.quantile(slopes, .975) * 100),
            "seed": SEED, "bootstrap_draws": DRAWS}


def fold_rates(frame: pd.DataFrame, folds: list[dict], family: str) -> pd.DataFrame:
    rows = []
    for no, fold in enumerate(folds, 1):
        train = frame.iloc[fold["train"]]
        valid = frame.iloc[fold["validation"]]
        for side, sample in (("train", train), ("validation", valid)):
            rows.append({"family": family, "fold": no, "validation_T": str(fold["validation_t"]),
                         "side": side, "snapshots": len(sample),
                         "customers": int(sample.customer_key.nunique()),
                         "positive_n": int(sample.label_returned.sum()),
                         "prevalence": float(sample.label_returned.mean())})
    return pd.DataFrame(rows)


def main() -> int:
    orders, scope, _ = load_dev_orders()
    if scope.get("test_labels_loaded") or scope.get("test_behavior_loaded"):
        raise RuntimeError("DEV loader reported test access")
    cohort = cohort_rates(orders)
    cohort_table = cohort.groupby("cohort_month", as_index=False).agg(
        customers=("returned_180d", "size"), repeaters=("returned_180d", "sum"),
        retention_180d=("returned_180d", "mean"))
    cohort_table["evidence"] = "khám phá, chưa xác nhận ngoài mẫu"
    v3_frame = build_multisnapshot_samples(orders, test_start=DEV_END)
    folds = build_multisnapshot_folds(v3_frame)
    fold_table = fold_rates(v3_frame, folds, "WP5/WP5b chung fold")
    trend = trend_bootstrap(cohort)
    result = {"status": "exploratory_dev_only_not_confirmed_out_of_sample",
              "test_raw_or_labels_read": False,
              "plan_sha256": hashlib.sha256((ROOT / "docs/analysis_plan_f2.md").read_bytes()).hexdigest(),
              "cohort_customers": len(cohort), "cohort_month_count": len(cohort_table),
              "cohort_trend": trend, "overall_cohort_rate": float(cohort.returned_180d.mean()),
              "folds": fold_table.to_dict("records"),
              "mean_train_prevalence": float(fold_table[fold_table.side == "train"].prevalence.mean()),
              "mean_validation_prevalence": float(fold_table[fold_table.side == "validation"].prevalence.mean()),
              "folds_used": len(folds), "seed": SEED, "bootstrap_draws": DRAWS}
    (ROOT / "outputs/metrics/prevalence_drift_f2.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    cohort_table.to_csv(ROOT / "outputs/tables/prevalence_cohort_month_f2.csv", index=False, float_format="%.6f")
    fold_table.to_csv(ROOT / "outputs/tables/prevalence_fold_f2.csv", index=False, float_format="%.6f")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
