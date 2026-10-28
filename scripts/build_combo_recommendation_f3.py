"""Add a preregistered descriptive screen to frozen DEV combo aggregates."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def recommendation_screen(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"bundle_discussion_rank", "dev_lift", "dev_kulczynski", "dev_imbalance_ratio"}
    if not required.issubset(frame.columns):
        raise ValueError(f"missing registered combo measures: {sorted(required - set(frame.columns))}")
    result = frame.copy()
    result["passes_recommendation_screen"] = (
        (pd.to_numeric(result.dev_lift, errors="coerce") > 1)
        & (pd.to_numeric(result.dev_kulczynski, errors="coerce") >= 0.5)
        & (pd.to_numeric(result.dev_imbalance_ratio, errors="coerce") <= 0.5)
    )
    result["screen_rule"] = "DEV lift>1 AND Kulczynski>=0.5 AND imbalance_ratio<=0.5"
    return result


def main() -> int:
    source = pd.read_csv(ROOT / "outputs/tables/frozen_combo_supplement_dev.csv")
    result = recommendation_screen(source)
    result.to_csv(ROOT / "outputs/tables/combo_recommendation_screen_f3.csv", index=False, float_format="%.6f")
    plan_hash = hashlib.sha256((ROOT / "docs/analysis_plan_f3.md").read_bytes()).hexdigest()
    print({"plan_sha256": plan_hash, "combos": len(result),
           "passed": int(result.passes_recommendation_screen.sum()),
           "rank_1_passed": bool(result.loc[result.bundle_discussion_rank == 1, "passes_recommendation_screen"].iloc[0]),
           "source_product_comparisons": 77, "expected_false_positives_at_5pct_approx": 77 * .05,
           "multiple_testing_adjustment": "none; no new p-values or significance claims"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
