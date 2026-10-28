"""Full label-free H1/H2 power tables for the registered Gate B R2 rule."""
from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parents[1]
N1, N2 = 6294, 988
BASELINES = {"DEV_7_4_percent": 0.074, "old_test_aggregate_4_6_percent": 0.046}
ALPHA_HOLM_FIRST = 0.025


def auc_se(auc: float, positives: int, negatives: int) -> float:
    q1, q2 = auc / (2 - auc), 2 * auc * auc / (1 + auc)
    variance = (auc * (1 - auc) + (positives - 1) * (q1 - auc * auc)
                + (negatives - 1) * (q2 - auc * auc)) / (positives * negatives)
    return math.sqrt(variance)


def auc_power(auc: float, prevalence: float) -> dict:
    n = N1 + N2
    positives = round(n * prevalence)
    se = auc_se(auc, positives, n - positives)
    zcrit = NormalDist().inv_cdf(1 - ALPHA_HOLM_FIRST)
    return {"expected_positives": positives, "auc_se": se,
            "power_lower_ci_gt_0_55": 1 - NormalDist().cdf(zcrit - (auc - 0.55) / se)}


def rr_power(rr: float, prevalence: float) -> dict:
    n = N1 + N2
    w2 = N2 / n
    p1 = prevalence / ((1 - w2) + w2 * rr)
    p2 = rr * p1
    e1, e2 = N1 * p1, N2 * p2
    se = math.sqrt((1 / e2 - 1 / N2) + (1 / e1 - 1 / N1))
    zcrit = NormalDist().inv_cdf(1 - ALPHA_HOLM_FIRST)
    return {"expected_events_frequency_1": e1, "expected_events_frequency_ge_2": e2,
            "se_log_rr": se,
            "power_lower_ci_gt_1_5": 1 - NormalDist().cdf(zcrit - (math.log(rr) - math.log(1.5)) / se)}


def build(rr_lower_dev: float) -> dict:
    rr_grid = [1.5, 2.0, 2.5, 3.0, float(rr_lower_dev)]
    result = {
        "scope": "label-free power sensitivity; no HO2 outcomes read",
        "preregistration": "docs/analysis_plan_gateb_r2.md",
        "group_sizes": {"frequency_eq_1": N1, "frequency_ge_2": N2},
        "alpha": ALPHA_HOLM_FIRST,
        "holm_note": "conservative first step if H2 returns to the primary family",
        "rr_lower_dev": rr_lower_dev,
        "rr_dev_passes_minimum_effect": rr_lower_dev > 1.5,
        "decision_rule": "H2 primary iff power>=0.80 at rr_lower_dev under both reference prevalences; otherwise secondary",
        "baselines": {},
    }
    for name, prevalence in BASELINES.items():
        result["baselines"][name] = {
            "prevalence": prevalence,
            "H1": {str(a): auc_power(a, prevalence) for a in (0.55, 0.60, 0.65, 0.70)},
            "H2": {str(r): rr_power(r, prevalence) for r in rr_grid},
        }
    h2_row = str(float(rr_lower_dev))
    powers = [result["baselines"][name]["H2"][h2_row]["power_lower_ci_gt_1_5"] for name in BASELINES]
    result["h2_power_at_rr_lower_dev_both_references"] = powers
    result["h2_primary"] = bool(rr_lower_dev > 1.5 and all(p >= 0.8 for p in powers))
    return result


def rounded(value):
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, dict):
        return {key: rounded(item) for key, item in value.items()}
    if isinstance(value, list):
        return [rounded(item) for item in value]
    return value


def main() -> int:
    metric_path = ROOT / "outputs/metrics/gateb_r2_rr_dev.json"
    rr_data = json.loads(metric_path.read_text(encoding="utf-8"))
    rr_lower = float(rr_data["rr_frequency_ge_2_vs_eq_1"]["ci95_lower"])
    result = rounded(build(rr_lower))
    target = ROOT / "outputs/metrics/gateb_r2_power.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
