"""Build coarser 2D dashboard cubes after registered F4 design failed target."""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from features.day2_data import load_dev_orders  # noqa: E402
from build_dashboard_cuboids_f4 import _prepare_rows, MIN_N  # noqa: E402


def suppress_2d(cube: pd.DataFrame, *, dimension: str, min_n: int = MIN_N) -> tuple[pd.DataFrame, dict]:
    if min_n != 30:
        raise ValueError("suppression threshold is fixed at 30")
    result = cube.copy().reset_index(drop=True)
    primary = ((result.orders < min_n) | (result.customers < min_n)).to_numpy(dtype=bool)
    suppressed = primary.copy()
    complementary = [False] * len(result)
    for _, positions in result.groupby("quarter", sort=True).indices.items():
        positions = list(positions)
        hidden = [i for i in positions if suppressed[i]]
        if len(hidden) == 1:
            remaining = next(i for i in positions if i not in hidden)
            suppressed[remaining] = True
            complementary[remaining] = True
    result["suppressed_primary"] = primary
    result["suppressed_complementary"] = complementary
    result["suppressed"] = suppressed
    result.loc[suppressed, ["orders", "customers", "recognized_revenue_vnd"]] = None
    result["suppression_note"] = ["primary: n<30" if p else "complementary: residual protection" if c else ""
                                  for p, c in zip(primary, complementary)]
    return result, {"rows": int(len(result)), "primary": int(sum(primary)),
                    "complementary": int(sum(complementary)), "suppressed": int(sum(suppressed)),
                    "suppression_rate": float(sum(suppressed) / len(result)) if len(result) else 0.0,
                    "target_under_30pct": bool(sum(suppressed) / len(result) < .30) if len(result) else True,
                    "threshold": min_n}


def build(orders: list[dict]) -> tuple[dict[str, pd.DataFrame], dict]:
    facts = _prepare_rows(orders)
    facts["rfm_broad"] = facts.rfm_group.map(
        lambda value: "Mua lặp lại" if value == "Mua lặp lại" else "Một đơn")
    specs = {"quarter_rfm_f4b": "rfm_broad", "quarter_channel_f4b": "channel_group"}
    outputs, meta = {}, {"status": "exploratory_dev_only_not_confirmed_out_of_sample",
                         "test_raw_or_labels_read": False, "margins_exported": False,
                         "threshold": MIN_N}
    for name, dimension in specs.items():
        g = facts.groupby(["quarter", dimension], as_index=False).agg(
            orders=("customer_key", "size"), customers=("customer_key", "nunique"),
            recognized_revenue_vnd=("recognized_revenue_vnd", "sum"))
        domains = [sorted(facts.quarter.unique()), sorted(facts[dimension].unique())]
        grid = pd.MultiIndex.from_product(domains, names=["quarter", dimension]).to_frame(index=False)
        g = grid.merge(g, on=["quarter", dimension], how="left").fillna(
            {"orders": 0, "customers": 0, "recognized_revenue_vnd": 0})
        g["orders"] = g.orders.astype(int)
        g["customers"] = g.customers.astype(int)
        safe, rates = suppress_2d(g, dimension=dimension)
        outputs[name] = safe
        meta[name] = rates
    return outputs, meta


def main() -> int:
    orders, scope, _ = load_dev_orders()
    if scope.get("test_labels_loaded") or scope.get("test_behavior_loaded"):
        raise RuntimeError("DEV loader reported test access")
    outputs, meta = build(orders)
    meta["plan_sha256"] = hashlib.sha256((ROOT / "docs/analysis_plan_f4b.md").read_bytes()).hexdigest()
    for name, frame in outputs.items():
        frame.to_csv(ROOT / f"outputs/tables/{name}.csv", index=False, float_format="%.6f")
    (ROOT / "outputs/metrics/dashboard_cuboids_f4b.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
