"""Create coarser DEV dashboard cuboids with primary and complementary suppression."""

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
from analyze_customer_value_dev import rfm_action_group  # noqa: E402
from analyze_seasonality_dev import channel_group  # noqa: E402

DEV_END = date(2025, 10, 22)
MIN_N = 30
RFM_HIGH_VALUE = 830_000.0


def apply_suppression(cube: pd.DataFrame, *, dimensions: list[str], min_n: int = MIN_N) -> tuple[pd.DataFrame, dict]:
    if min_n != 30:
        raise ValueError("suppression threshold is fixed at 30")
    result = cube.copy().reset_index(drop=True)
    primary = (result.orders < min_n) | (result.customers < min_n)
    suppressed = primary.to_numpy(dtype=bool, copy=True)
    complementary = np.zeros(len(result), dtype=bool)
    # For each quarter, protect subtotals along either second/third dimension:
    # no published subtotal may have exactly one hidden child.
    changed = True
    while changed:
        changed = False
        for parent_col, child_col in ((dimensions[1], dimensions[2]), (dimensions[2], dimensions[1])):
            groups = result.groupby(["quarter", parent_col], dropna=False, sort=True).indices
            for _, positions in groups.items():
                positions = np.asarray(positions, dtype=int)
                hidden = positions[suppressed[positions]]
                if len(hidden) == 1:
                    candidates = positions[~suppressed[positions]]
                    if len(candidates):
                        chosen = min(candidates, key=lambda i: (int(result.loc[i, "orders"]), str(result.loc[i, child_col])))
                        suppressed[chosen] = True
                        complementary[chosen] = True
                        changed = True
    result["suppressed_primary"] = primary
    result["suppressed_complementary"] = complementary
    result["suppressed"] = suppressed
    result.loc[suppressed, ["orders", "customers", "recognized_revenue_vnd"]] = np.nan
    result["suppression_note"] = np.where(
        primary, "primary: orders hoặc customers <30",
        np.where(complementary, "complementary: tránh suy ra residual", ""))
    metrics = {"rows": int(len(result)), "suppressed_primary": int(primary.sum()),
               "suppressed_complementary": int(complementary.sum()),
               "suppressed_total": int(suppressed.sum()),
               "suppression_rate": float(suppressed.mean()) if len(result) else 0.0,
               "threshold": min_n}
    return result, metrics


def _prepare_rows(orders: list[dict]) -> pd.DataFrame:
    by_customer: dict[str, list[dict]] = defaultdict(list)
    valid = [r for r in orders if r.get("customer_key") and not r.get("is_gift") and r["date"] < DEV_END]
    for row in valid:
        by_customer[str(row["customer_key"])].append(row)
    monetary = {k: sum(float(r.get("monetary_contribution") or 0) for r in rows) for k, rows in by_customer.items()}
    customer_group = {}
    for k, rows in by_customer.items():
        rows.sort(key=lambda r: (r["date"], r.get("order_sequence", 0)))
        recency = (DEV_END - rows[-1]["date"]).days
        name = rfm_action_group(recency, len(rows), monetary[k], RFM_HIGH_VALUE)
        if name in {"Giá trị cao, mua lặp lại gần đây", "Mua lặp lại gần đây", "Mua lặp lại đã lâu"}:
            bucket = "Mua lặp lại"
        elif recency <= 90:
            bucket = "Một đơn gần đây"
        else:
            bucket = "Một đơn đã lâu"
        customer_group[k] = bucket
    records = []
    for r in valid:
        q = f"{r['date'].year}-Q{(r['date'].month - 1) // 3 + 1}"
        channel = channel_group(r.get("order_channel"))
        channel = "Facebook" if channel == "Facebook" else "Khác/thiếu"
        basket = "3+" if len(r.get("product_keys") or []) >= 3 else "1–2"
        records.append({"quarter": q, "channel_group": channel, "basket_group": basket,
                        "rfm_group": customer_group[str(r["customer_key"])],
                        "customer_key": str(r["customer_key"]),
                        "recognized_revenue_vnd": float(r.get("revenue_recognized") or 0)})
    return pd.DataFrame(records)


def build_cuboids(orders: list[dict]) -> tuple[dict[str, pd.DataFrame], dict]:
    facts = _prepare_rows(orders)
    outputs, meta = {}, {"status": "exploratory_dev_only_not_confirmed_out_of_sample",
                         "test_raw_or_labels_read": False, "source_orders": len(facts),
                         "threshold": MIN_N, "margins_exported": False}
    specs = {"quarter_channel_rfm": ["quarter", "channel_group", "rfm_group"],
             "quarter_basket_rfm": ["quarter", "basket_group", "rfm_group"]}
    for name, dimensions in specs.items():
        grouped = facts.groupby(dimensions, dropna=False, as_index=False).agg(
            orders=("customer_key", "size"), customers=("customer_key", "nunique"),
            recognized_revenue_vnd=("recognized_revenue_vnd", "sum"))
        cube = grouped
        # Full Cartesian grid makes absent/low cells explicit before suppression.
        domains = [sorted(facts[col].unique()) for col in dimensions]
        full = pd.MultiIndex.from_product(domains, names=dimensions).to_frame(index=False)
        cube = full.merge(cube, on=dimensions, how="left").fillna({"orders": 0, "customers": 0, "recognized_revenue_vnd": 0})
        cube["orders"] = cube.orders.astype(int)
        cube["customers"] = cube.customers.astype(int)
        cube, measure = apply_suppression(cube, dimensions=dimensions)
        measure["dimension_count"] = len(dimensions)
        measure["dashboard_target_under_30pct"] = measure["suppression_rate"] < 0.30
        outputs[name] = cube
        meta[name] = measure
    return outputs, meta


def main() -> int:
    orders, scope, _ = load_dev_orders()
    if scope.get("test_labels_loaded") or scope.get("test_behavior_loaded"):
        raise RuntimeError("DEV loader reported test access")
    cuboids, metrics = build_cuboids(orders)
    metrics["plan_sha256"] = hashlib.sha256((ROOT / "docs/analysis_plan_f4.md").read_bytes()).hexdigest()
    for name, cube in cuboids.items():
        cube.to_csv(ROOT / f"outputs/tables/{name}_f4.csv", index=False, float_format="%.6f")
    (ROOT / "outputs/metrics/dashboard_cuboids_f4.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
