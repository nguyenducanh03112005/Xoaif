"""Exploratory DEV-only first-basket, next-order, and frozen-bundle analysis."""

from __future__ import annotations

from collections import Counter, defaultdict
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
from features.gift_lines import classify_orders  # noqa: E402

DEV_END = date(2025, 10, 22)
SEED = 20261028
DRAWS = 2000
MIN_N = 30


def prepare_baskets(orders: list[dict]) -> tuple[list[dict], dict[str, str]]:
    """Classify gift lines and return eligible DEV transactions without keys in outputs."""
    classified, _ = classify_orders(orders)
    baskets: list[dict] = []
    name_counts: dict[str, Counter] = defaultdict(Counter)
    for order in classified:
        if order.get("is_gift") or order.get("date") >= DEV_END:
            continue
        products = set()
        for line in order.get("gift_line_records", []):
            key = line.get("product_key")
            if key and not line.get("gift_line"):
                products.add(str(key))
                if line.get("product_name"):
                    name_counts[str(key)][str(line["product_name"])] += 1
        if not products:
            continue
        baskets.append({
            "date": order["date"], "month": order["date"].strftime("%Y-%m"),
            "customer_key": order.get("customer_key"), "order_sequence": int(order["order_sequence"]),
            "items": frozenset(products),
            "recognized_revenue": float(order["revenue_recognized"]),
        })
    names = {key: counts.most_common(1)[0][0] for key, counts in name_counts.items() if counts}
    return baskets, names


def customer_first_baskets(baskets: list[dict]) -> tuple[list[dict], list[dict]]:
    """First transaction per customer and next transaction on a later local date."""
    by_customer: dict[str, list[dict]] = defaultdict(list)
    for basket in baskets:
        if basket["customer_key"]:
            by_customer[str(basket["customer_key"])].append(basket)
    first_rows, second_rows = [], []
    for customer, rows in by_customer.items():
        rows.sort(key=lambda row: (row["date"], row["order_sequence"]))
        first = rows[0]
        if first["date"] + timedelta(days=180) >= DEV_END:
            continue
        first_rows.append({**first, "customer_key": customer})
        second = next((row for row in rows[1:] if row["date"] > first["date"]), None)
        if second and second["date"] <= first["date"] + timedelta(days=180):
            second_rows.append({
                "customer_key": customer, "first_date": first["date"], "second_date": second["date"],
                "gap_days": (second["date"] - first["date"]).days,
                "first_items": first["items"], "second_items": second["items"],
            })
    return first_rows, second_rows


def _bootstrap_product_stats(rows: list[dict], product: str, *, seed: int = SEED, draws: int = DRAWS) -> dict:
    """Month-stratified customer bootstrap for raw and standardized repeat rates."""
    present = np.array([product in row["items"] for row in rows], dtype=bool)
    outcome = np.array([row["repeat_180d"] for row in rows], dtype=float)
    months = np.array([row["month"] for row in rows], dtype=object)
    n_yes, n_no = int(present.sum()), int((~present).sum())
    if n_yes < MIN_N or n_no < MIN_N:
        return {"n_product_first_basket": n_yes, "n_without_product": n_no, "suppressed": True}
    month_weights = {m: float(np.mean(months == m)) for m in sorted(set(months))}
    point_yes = float(outcome[present].mean())
    point_no = float(outcome[~present].mean())
    raw_boot_yes = np.empty(draws)
    raw_boot_no = np.empty(draws)
    rng = np.random.default_rng(seed)
    raw_boot_yes = outcome[present][rng.integers(0, n_yes, size=(draws, n_yes))].mean(axis=1)
    raw_boot_no = outcome[~present][rng.integers(0, n_no, size=(draws, n_no))].mean(axis=1)
    strat_yes = np.zeros(draws)
    strat_no = np.zeros(draws)
    usable_weight = 0.0
    usable_month_count = 0
    point_strat_yes = 0.0
    point_strat_no = 0.0
    for month, weight in month_weights.items():
        month_mask = months == month
        yes_values = outcome[month_mask & present]
        no_values = outcome[month_mask & ~present]
        if not len(yes_values) or not len(no_values):
            continue
        yes_draws = yes_values[rng.integers(0, len(yes_values), size=(draws, len(yes_values)))].mean(axis=1)
        no_draws = no_values[rng.integers(0, len(no_values), size=(draws, len(no_values)))].mean(axis=1)
        strat_yes += weight * yes_draws
        strat_no += weight * no_draws
        point_strat_yes += weight * float(yes_values.mean())
        point_strat_no += weight * float(no_values.mean())
        usable_weight += weight
        usable_month_count += 1
    if usable_weight:
        strat_yes /= usable_weight
        strat_no /= usable_weight
        strat_diff = strat_yes - strat_no
        standardized_yes = point_strat_yes / usable_weight
        standardized_no = point_strat_no / usable_weight
        diff_point = standardized_yes - standardized_no
    else:
        strat_diff = np.full(draws, np.nan)
        standardized_yes = standardized_no = diff_point = float("nan")
    standardized_ci = (
        (float(np.quantile(strat_yes, .025)), float(np.quantile(strat_yes, .975)),
         float(np.quantile(strat_no, .025)), float(np.quantile(strat_no, .975)),
         float(np.quantile(strat_diff, .025)), float(np.quantile(strat_diff, .975)))
        if usable_weight else (float("nan"),) * 6
    )
    return {
        "n_product_first_basket": n_yes, "n_without_product": n_no, "suppressed": False,
        "repeat_rate_with_product": point_yes,
        "with_ci_low": float(np.quantile(raw_boot_yes, .025)), "with_ci_high": float(np.quantile(raw_boot_yes, .975)),
        "repeat_rate_without_product": point_no,
        "without_ci_low": float(np.quantile(raw_boot_no, .025)), "without_ci_high": float(np.quantile(raw_boot_no, .975)),
        "overlap_month_standardized_rate_with": standardized_yes,
        "standardized_with_ci_low": standardized_ci[0], "standardized_with_ci_high": standardized_ci[1],
        "overlap_month_standardized_rate_without": standardized_no,
        "standardized_without_ci_low": standardized_ci[2], "standardized_without_ci_high": standardized_ci[3],
        "overlap_month_standardized_difference": diff_point,
        "standardized_difference_ci_low": standardized_ci[4],
        "standardized_difference_ci_high": standardized_ci[5],
        "standardized_month_count": usable_month_count,
        "standardized_month_weight_coverage": usable_weight,
    }


def combo_metrics(
    baskets: list[dict], names: dict[str, str], frozen: pd.DataFrame,
    test_aggregates: pd.DataFrame | None = None,
) -> pd.DataFrame:
    eligible = [row for row in baskets if len(row["items"]) >= 2]
    denominator = len(eligible)
    item_counts = Counter(key for row in eligible for key in row["items"])
    monthly_total = Counter(row["month"] for row in eligible)
    result = []
    for combo in frozen.to_dict("records"):
        a, b = str(combo["product_a_key_hmac"]), str(combo["product_b_key_hmac"])
        together = [row for row in eligible if a in row["items"] and b in row["items"]]
        pair_n = len(together)
        sa, sb, sp = item_counts[a] / denominator, item_counts[b] / denominator, pair_n / denominator
        ca = pair_n / item_counts[a] if item_counts[a] else 0.0
        cb = pair_n / item_counts[b] if item_counts[b] else 0.0
        lift = sp / (sa * sb) if sa and sb else 0.0
        kulc = (ca + cb) / 2
        all_conf = sp / max(sa, sb) if max(sa, sb) else 0.0
        ir = abs(sa - sb) / (sa + sb - sp) if sa + sb - sp else 0.0
        monthly_pair = Counter(row["month"] for row in together)
        supports = [monthly_pair[m] / total for m, total in sorted(monthly_total.items())]
        cv = float(np.std(supports, ddof=0) / np.mean(supports)) if supports and np.mean(supports) else np.nan
        values = [row["recognized_revenue"] for row in together]
        result.append({
            "combo_name": combo["combo_name"], "product_a": combo["product_a"], "product_b": combo["product_b"],
            "dev_eligible_baskets": denominator, "dev_pair_occurrences": pair_n, "dev_support": sp,
            "dev_confidence_a_to_b": ca, "dev_confidence_b_to_a": cb, "dev_lift": lift,
            "dev_kulczynski": kulc, "dev_all_confidence": all_conf, "dev_imbalance_ratio": ir,
            "months_with_pair": sum(n > 0 for n in monthly_pair.values()), "months_observed": len(monthly_total),
            "monthly_support_cv": cv, "median_recognized_basket_revenue_vnd": float(np.median(values)) if values else np.nan,
            "combined_listed_price_vnd": combo.get("combined_nonzero_listed_price_vnd"),
            "test_eligible_baskets_committed": combo.get("test_eligible_baskets"),
            "test_pair_occurrences_committed": combo.get("pair_occurrences"),
            "test_support_committed": combo.get("support"), "test_lift_committed": combo.get("lift"),
        })
    frame = pd.DataFrame(result)
    if test_aggregates is not None:
        test_columns = ["combo_name", "test_eligible_baskets", "pair_occurrences", "support", "lift"]
        available = [column for column in test_columns if column in test_aggregates.columns]
        test_map = test_aggregates[available].drop_duplicates("combo_name").rename(columns={
            "test_eligible_baskets": "test_eligible_baskets_committed",
            "pair_occurrences": "test_pair_occurrences_committed",
            "support": "test_support_committed", "lift": "test_lift_committed",
        })
        frame = frame.drop(columns=[
            "test_eligible_baskets_committed", "test_pair_occurrences_committed",
            "test_support_committed", "test_lift_committed",
        ], errors="ignore").merge(test_map, on="combo_name", how="left", validate="one_to_one")
    rank_specs = [
        ("dev_support", False), ("dev_lift", False), ("monthly_support_cv", True),
        ("median_recognized_basket_revenue_vnd", False),
    ]
    ranks = []
    for column, ascending in rank_specs:
        ranks.append(frame[column].rank(pct=True, ascending=ascending, method="average").fillna(.5))
    frame["bundle_discussion_rank_score"] = pd.concat(ranks, axis=1).mean(axis=1)
    frame["bundle_discussion_rank"] = frame["bundle_discussion_rank_score"].rank(ascending=False, method="min").astype(int)
    return frame.sort_values("bundle_discussion_rank")


def analyze(
    orders: list[dict], frozen: pd.DataFrame, *, plan_sha256: str,
    test_aggregates: pd.DataFrame | None = None,
) -> dict[str, pd.DataFrame | dict]:
    baskets, names = prepare_baskets(orders)
    first, second = customer_first_baskets(baskets)
    mature_customers = {row["customer_key"] for row in first}
    repeat_customers = {row["customer_key"] for row in second}
    first_rows = [{**row, "repeat_180d": int(row["customer_key"] in repeat_customers)} for row in first]
    first_item_counts: Counter[str] = Counter(key for row in first_rows for key in row["items"])
    products = sorted(key for key, count in first_item_counts.items() if count >= MIN_N)
    first_stats = []
    for key in products:
        stats = _bootstrap_product_stats(first_rows, key)
        first_stats.append({
            "product": names.get(key, "Tên sản phẩm chưa có"), **stats,
            "suppression_note": "n<30 trong ít nhất một nhóm; chỉ số ước lượng bị ẩn" if stats["suppressed"] else "",
        })

    transitions: Counter[tuple[str, str]] = Counter()
    gaps: dict[tuple[str, str], list[int]] = defaultdict(list)
    for row in second:
        for a in row["first_items"]:
            for b in row["second_items"]:
                transitions[(a, b)] += 1
                gaps[(a, b)].append(row["gap_days"])
    top_pairs = sorted(
        ((pair, n) for pair, n in transitions.items() if n >= MIN_N),
        key=lambda value: (-value[1], names.get(value[0][0], ""), names.get(value[0][1], "")),
    )[:20]
    journey_rows = []
    for (a, b), n in top_pairs:
        gap_values = np.asarray(gaps[(a, b)], dtype=float)
        rng = np.random.default_rng(SEED + len(journey_rows))
        boot = np.asarray([np.median(rng.choice(gap_values, len(gap_values), replace=True)) for _ in range(DRAWS)])
        journey_rows.append({
            "first_order_product": names.get(a, "Tên sản phẩm chưa có"),
            "next_order_product": names.get(b, "Tên sản phẩm chưa có"), "customers": n,
            "median_gap_days": float(np.median(gap_values)),
            "median_gap_ci_lower_95": float(np.quantile(boot, .025)),
            "median_gap_ci_upper_95": float(np.quantile(boot, .975)),
        })

    # Product roles use all eligible DEV baskets; revenue remains at order level.
    second_order_products = Counter(key for row in second for key in row["second_items"])
    all_order_products: dict[str, list[float]] = defaultdict(list)
    for row in baskets:
        for key in row["items"]:
            all_order_products[key].append(row["recognized_revenue"])
    roles = []
    for key, count in sorted(first_item_counts.items(), key=lambda item: (-item[1], names.get(item[0], ""))):
        if count < MIN_N:
            continue
        vals = all_order_products.get(key, [])
        roles.append({
            "product": names.get(key, "Tên sản phẩm chưa có"), "first_basket_customers": count,
            "first_basket_share": count / len(first_rows) if first_rows else np.nan,
            "second_order_customers": second_order_products[key],
            "median_order_recognized_revenue_vnd": float(np.median(vals)) if len(vals) >= MIN_N else None,
            "orders_containing_product": len(vals) if len(vals) >= MIN_N else "<30",
        })

    monthly_combo = combo_metrics(baskets, names, frozen, test_aggregates)
    return {
        "first_basket_product_repeat": pd.DataFrame(first_stats),
        "next_product_pairs": pd.DataFrame(journey_rows),
        "product_roles": pd.DataFrame(roles),
        "frozen_combo_supplement": monthly_combo,
        "meta": {
            "analysis_plan_sha256": plan_sha256, "status": "exploratory_dev_only_not_confirmed_out_of_sample",
            "test_raw_or_labels_read": False,
            "test_aggregate_source": "outputs/tables/test_combos_frozen.csv" if test_aggregates is not None else None,
            "seed": SEED, "bootstrap_draws": DRAWS,
            "valid_dev_baskets": len(baskets), "eligible_dev_baskets_for_combos": sum(len(row["items"]) >= 2 for row in baskets),
            "mature_first_basket_customers": len(mature_customers), "repeat_customers_within_180d": len(repeat_customers),
            "first_basket_products_tested_n_ge_30": len(products), "first_basket_products_suppressed": sum(x["suppressed"] for x in first_stats),
            "unique_directed_transitions": len(transitions), "directed_transitions_n_ge_30": sum(n >= MIN_N for n in transitions.values()),
            "next_product_pairs_reported": len(journey_rows), "frozen_combo_count": len(monthly_combo),
            "dev_month_count": len({row["month"] for row in baskets}),
        },
    }


def main() -> int:
    orders, _, _ = load_dev_orders()
    frozen = pd.read_csv(ROOT / "outputs" / "tables" / "combos_v2.csv")
    test_aggregates = pd.read_csv(ROOT / "outputs" / "tables" / "test_combos_frozen.csv")
    if len(frozen) != 24:
        raise ValueError("Expected the frozen set of exactly 24 combos")
    plan = ROOT / "docs" / "analysis_plan_wp3.md"
    digest = hashlib.sha256(plan.read_bytes()).hexdigest()
    result = analyze(orders, frozen, plan_sha256=digest, test_aggregates=test_aggregates)
    out_tables = ROOT / "outputs" / "tables"
    allowlist = {
        "first_basket_product_repeat": "first_basket_product_repeat_dev.csv",
        "next_product_pairs": "next_product_pairs_dev.csv",
        "product_roles": "product_roles_dev.csv",
        "frozen_combo_supplement": "frozen_combo_supplement_dev.csv",
    }
    for key, filename in allowlist.items():
        frame = result[key]
        frame.to_csv(out_tables / filename, index=False, float_format="%.6f")
    metrics_path = ROOT / "outputs" / "metrics" / "product_journey_dev.json"
    metrics_path.write_text(json.dumps(result["meta"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["meta"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
