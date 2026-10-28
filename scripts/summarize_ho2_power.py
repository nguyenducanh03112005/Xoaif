"""Label-free precision and approximate power calculations for Gate B."""
from __future__ import annotations

import json
import math
from statistics import NormalDist

N_ELIGIBLE = 7282
N_FREQ2 = 988
N_FREQ1 = N_ELIGIBLE - N_FREQ2
REFERENCE_PREVALENCES = {"DEV": 0.074, "test_aggregate_reference": 0.046}


def auc_se_hanley_mcneil(auc: float, positives: int, negatives: int) -> float:
    q1 = auc / (2 - auc)
    q2 = 2 * auc * auc / (1 + auc)
    variance = (auc * (1 - auc) + (positives - 1) * (q1 - auc * auc)
                + (negatives - 1) * (q2 - auc * auc)) / (positives * negatives)
    return math.sqrt(variance)


def h2_expected(prevalence: float, true_rr: float) -> dict[str, float | int]:
    weight2 = N_FREQ2 / N_ELIGIBLE
    p1 = prevalence / (weight2 * true_rr + (1 - weight2))
    p2 = true_rr * p1
    events1 = N_FREQ1 * p1
    events2 = N_FREQ2 * p2
    se_log_rr = math.sqrt((1 / events2 - 1 / N_FREQ2) + (1 / events1 - 1 / N_FREQ1))
    critical = NormalDist().inv_cdf(0.95)  # one-sided 95% lower bound; H2 is secondary
    power = 1 - NormalDist().cdf(critical - (math.log(true_rr) - math.log(1.5)) / se_log_rr)
    return {
        "expected_events_freq1": round(events1),
        "expected_events_freq_ge2": round(events2),
        "se_log_rr": se_log_rr,
        "lower_bound_rr_95_one_sided": math.exp(math.log(true_rr) - critical * se_log_rr),
        "approx_power_against_rr_1_5": power,
    }


def build_report() -> dict:
    z_two_sided = NormalDist().inv_cdf(0.975)
    z_primary = NormalDist().inv_cdf(0.95)  # Holm family has one remaining primary hypothesis
    rows = {}
    for label, p in REFERENCE_PREVALENCES.items():
        positives = round(N_ELIGIBLE * p)
        rate_se = math.sqrt(p * (1 - p) / N_ELIGIBLE)
        auc_rows = {}
        for auc in (0.60, 0.65, 0.70):
            se = auc_se_hanley_mcneil(auc, positives, N_ELIGIBLE - positives)
            auc_rows[str(auc)] = {
                "se": se,
                "two_sided_95_ci_width": 2 * z_two_sided * se,
                "approx_power_lower_bound_gt_0_55_primary_alpha_0_05": 1 - NormalDist().cdf(
                    z_primary - (auc - 0.55) / se
                ),
            }
        rows[label] = {
            "reference_prevalence": p,
            "expected_total_positives": positives,
            "wilson_normal_approx_95_ci_width_percentage_points": 2 * z_two_sided * rate_se * 100,
            "h1_auc_scenarios": auc_rows,
            "h2_rr_scenarios": {str(rr): h2_expected(p, rr) for rr in (1.5, 2.0, 2.5, 3.0)},
        }
    return {
        "scope": "label-free planning only; no HO2 labels or outcomes read",
        "N_eligible_pre_T2": N_ELIGIBLE,
        "N_frequency_ge_2": N_FREQ2,
        "N_frequency_eq_1": N_FREQ1,
        "H1_method": "Hanley-McNeil large-sample ROC-AUC variance; sensitivity scenarios, one-sided alpha=.05 (single remaining primary hypothesis)",
        "H2_method": "Wald log-risk-ratio approximation; group counts fixed to pre-T2 counts; prevalence fixed at references; one-sided 95% lower bound, secondary only",
        "caveat": "Power is scenario-based, not a guarantee; future prevalence, model AUC, customer mix and independence assumptions may differ.",
        "reference_scenarios": rows,
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), indent=2))
