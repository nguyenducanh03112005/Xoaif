"""Pre-test line-level gift audit, stable FP-Growth pairs and seasonality."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import fpgrowth
from mlxtend.preprocessing import TransactionEncoder

from features.day2_data import load_dev_orders
from features.gift_lines import classify_orders

ROOT = Path(__file__).resolve().parents[2]
SUPPORTS = (0.01, 0.05)
MIN_OCCURRENCES = 5
STABILITY_MIN_CELLS = 4
HOLIDAYS = {
    "Ngày Phụ nữ Việt Nam": (date(2024, 10, 20), date(2025, 10, 20)),
    "Ngày Nhà giáo Việt Nam": (date(2024, 11, 20),),
    "Giáng sinh": (date(2024, 12, 25),),
    "Tết Nguyên đán": (date(2025, 1, 29),),
    "Ngày Quốc tế Phụ nữ": (date(2025, 3, 8),),
}


def _json_decimal(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _mode(values: list[str]) -> str | None:
    if not values:
        return None
    return Counter(values).most_common(1)[0][0]


def _line_source_counts(orders: list[dict[str, Any]]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, float]]:
    lines_by_source: Counter[str] = Counter()
    orders_by_source: dict[str, set[int]] = defaultdict(set)
    month_stats: dict[str, Counter[str]] = defaultdict(Counter)
    size_stats: dict[str, Counter[str]] = defaultdict(Counter)
    gross_values = [float(order["gross_list_value"]) for order in orders if order.get("gross_list_value") is not None]
    thresholds = {
        "p25": float(np.quantile(gross_values, .25)),
        "p50": float(np.quantile(gross_values, .50)),
        "p75": float(np.quantile(gross_values, .75)),
        "p90": float(np.quantile(gross_values, .90)),
    }
    for index, order in enumerate(orders):
        month = order["month"]
        amount = _json_decimal(order.get("gross_list_value"))
        if amount is None or amount <= thresholds["p25"]:
            size_group = "Q1"
        elif amount <= thresholds["p50"]:
            size_group = "Q2"
        elif amount <= thresholds["p75"]:
            size_group = "Q3"
        else:
            size_group = "Q4"
        for line in order["gift_line_records"]:
            source = line["gift_source"]
            lines_by_source[source] += 1
            orders_by_source[source].add(index)
            month_stats[month]["line_count"] += 1
            month_stats[month]["gift_line_count"] += int(line["gift_line"])
            month_stats[month][f"{source}_count"] += 1
            size_stats[size_group]["line_count"] += 1
            size_stats[size_group]["gift_line_count"] += int(line["gift_line"])
            size_stats[size_group][f"{source}_count"] += 1
    sources = ("flag", "zero_price", "inferred_subset", "not_gift")
    audit_rows = [
        {"gift_source": source, "line_count": int(lines_by_source[source]),
         "distinct_order_count": len(orders_by_source[source]),
         "gift_line_count": int(lines_by_source[source] if source != "not_gift" else 0),
         "low_confidence": source == "inferred_subset"}
        for source in sources
    ]
    monthly_rows = []
    for month, stats in sorted(month_stats.items()):
        count = int(stats["line_count"])
        monthly_rows.append({
            "month": month, "line_count": count, "gift_line_count": int(stats["gift_line_count"]),
            "gift_line_rate": float(stats["gift_line_count"] / count) if count else 0.0,
            **{f"{source}_count": int(stats[f"{source}_count"]) for source in sources},
        })
    size_rows = []
    for group, stats in (name for name in sorted(size_stats.items())):
        count = int(stats["line_count"])
        size_rows.append({
            "development_order_value_quartile": group,
            "line_count": count,
            "gift_line_count": int(stats["gift_line_count"]),
            "gift_line_rate": float(stats["gift_line_count"] / count) if count else 0.0,
            **{f"{source}_count": int(stats[f"{source}_count"]) for source in sources},
        })
    return pd.DataFrame(audit_rows), pd.DataFrame(monthly_rows), pd.DataFrame(size_rows), thresholds


def _transactions(orders: list[dict[str, Any]], cleaning: str) -> tuple[list[dict[str, Any]], int, int]:
    transaction_rows: list[dict[str, Any]] = []
    before_count = 0
    after_count = 0
    for order in orders:
        if order["is_gift"]:
            continue
        all_products = {line["product_key"] for line in order["gift_line_records"] if line.get("product_key")}
        if len(all_products) >= 2:
            before_count += 1
        selected = []
        for line in order["gift_line_records"]:
            if not line.get("product_key"):
                continue
            remove = (
                cleaning == "all_gift_sources" and line["gift_line"]
            ) or (
                cleaning == "explicit_only" and line["gift_source"] in {"flag", "zero_price"}
            )
            if not remove:
                selected.append(line["product_key"])
        products = sorted(set(selected))
        if len(products) >= 2:
            after_count += 1
            transaction_rows.append({
                "items": products,
                "month": order["month"],
                "date": order["date"],
                "order_sequence": order["order_sequence"],
            })
    return transaction_rows, before_count, after_count


def _pair_counts(transactions: list[dict[str, Any]], min_support: float) -> dict[tuple[str, str], dict[str, Any]]:
    items = [row["items"] for row in transactions]
    if not items:
        return {}
    encoder = TransactionEncoder()
    matrix = encoder.fit(items).transform(items)
    frame = pd.DataFrame(matrix, columns=encoder.columns_)
    frequent = fpgrowth(frame, min_support=min_support, use_colnames=True, max_len=2)
    denominator = len(items)
    item_counts: Counter[str] = Counter(key for basket in items for key in basket)
    output: dict[tuple[str, str], dict[str, Any]] = {}
    for record in frequent.to_dict("records"):
        pair_values = sorted(record["itemsets"])
        if len(pair_values) != 2:
            continue
        support = float(record["support"])
        occurrences = int(round(support * denominator))
        if occurrences < MIN_OCCURRENCES:
            continue
        a, b = pair_values
        supp_a = item_counts[a] / denominator
        supp_b = item_counts[b] / denominator
        output[(a, b)] = {
            "support": support,
            "occurrences": occurrences,
            "confidence_a_to_b": support / supp_a if supp_a else 0.0,
            "confidence_b_to_a": support / supp_b if supp_b else 0.0,
            "lift": support / (supp_a * supp_b) if supp_a and supp_b else 0.0,
            "leverage": support - supp_a * supp_b,
            "support_a": supp_a,
            "support_b": supp_b,
            "count_a": item_counts[a],
            "count_b": item_counts[b],
            "denominator": denominator,
        }
    return output


def _seasonality(pair: tuple[str, str], transactions: list[dict[str, Any]], product_months: dict[str, set[str]]) -> dict[str, Any]:
    a, b = pair
    overlap_months = product_months.get(a, set()) & product_months.get(b, set())
    overlap_baskets = [row for row in transactions if row["month"] in overlap_months]
    cooccurrences = [row for row in overlap_baskets if a in row["items"] and b in row["items"]]
    support = len(cooccurrences) / len(overlap_baskets) if overlap_baskets else 0.0
    seasonal_name = None
    if len(cooccurrences) >= MIN_OCCURRENCES:
        for holiday, dates in HOLIDAYS.items():
            if any(all(abs((row["date"] - holiday_date).days) <= 14 for row in cooccurrences) for holiday_date in dates):
                seasonal_name = holiday
                break
    return {
        "overlap_month_count": len(overlap_months),
        "overlap_months": ";".join(sorted(overlap_months)),
        "overlap_basket_count": len(overlap_baskets),
        "overlap_pair_occurrences": len(cooccurrences),
        "overlap_support": support,
        "seasonal_label": f"theo mùa: {seasonal_name}" if seasonal_name else "không gắn nhãn theo mùa",
    }


def _profile_products(orders: list[dict[str, Any]], before_transactions: list[dict[str, Any]], p90: float) -> tuple[pd.DataFrame, dict[str, Any]]:
    lines: dict[str, list[dict[str, Any]]] = defaultdict(list)
    product_months: dict[str, set[str]] = defaultdict(set)
    product_order_month: dict[str, dict[int, str]] = defaultdict(dict)
    support_orders: Counter[str] = Counter()
    eligible_count = len(before_transactions)
    for transaction in before_transactions:
        support_orders.update(transaction["items"])
    for order in orders:
        for line in order["gift_line_records"]:
            key = line.get("product_key")
            if not key:
                continue
            lines[key].append({**line, "date": order["date"], "month": order["month"], "order_sequence": order["order_sequence"], "large_order": float(order["gross_list_value"] or 0) >= p90})
            product_months[key].add(order["month"])
    all_rows = []
    price_by_key: dict[str, float | None] = {}
    for product_key, values in lines.items():
        dates = [value["date"] for value in values]
        order_set = {value["order_sequence"] for value in values}
        large_orders = {value["order_sequence"] for value in values if value["large_order"]}
        nonzero_prices = [float(value["retail_price"]) for value in values if value.get("retail_price") is not None and float(value["retail_price"]) > 0]
        categories = sorted({category for value in values for category in value.get("category_ids", [])})
        names = [value["product_name"] for value in values if value.get("product_name")]
        gift_count = sum(bool(value["gift_line"]) for value in values)
        price = float(np.median(nonzero_prices)) if nonzero_prices else None
        price_by_key[product_key] = price
        all_rows.append({
            "product_key_hmac": product_key,
            "product_name_from_order_api": _mode(names),
            "category_ids_from_order_api": ";".join(categories),
            "basket_support_before_gift_removal": float(support_orders[product_key] / eligible_count) if eligible_count else 0.0,
            "line_count": len(values),
            "gift_line_count": gift_count,
            "gift_line_rate": gift_count / len(values) if values else 0.0,
            "first_sold_date": min(dates).isoformat(),
            "last_sold_date": max(dates).isoformat(),
            "active_month_count": len({value["month"] for value in values}),
            "share_of_product_orders_that_are_large": len(large_orders) / len(order_set) if order_set else 0.0,
            "observed_nonzero_retail_price_vnd": price,
            "basket_order_count": int(support_orders[product_key]),
        })
    profile = pd.DataFrame(all_rows)
    if not profile.empty:
        profile = profile.sort_values(["basket_support_before_gift_removal", "line_count", "product_key_hmac"], ascending=[False, False, True]).reset_index(drop=True)
        profile["top20_by_support"] = False
        profile.loc[: min(19, len(profile) - 1), "top20_by_support"] = True
    return profile, price_by_key


def run_day3_pretest() -> dict[str, Any]:
    tables = ROOT / "outputs" / "tables"
    metrics_dir = ROOT / "outputs" / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    tables.mkdir(parents=True, exist_ok=True)
    orders, data_stats, _ = load_dev_orders()
    orders, audit = classify_orders(orders)
    audit_frame, monthly_frame, size_frame, thresholds = _line_source_counts(orders)
    all_transactions, before_count, all_count = _transactions(orders, "all_lines")
    explicit_transactions, _, explicit_count = _transactions(orders, "explicit_only")
    clean_transactions, _, clean_count = _transactions(orders, "all_gift_sources")
    audit_frame.to_csv(tables / "gift_line_audit.csv", index=False, encoding="utf-8-sig")
    monthly_frame.to_csv(tables / "gift_line_rates_monthly.csv", index=False, encoding="utf-8-sig")
    size_frame.to_csv(tables / "gift_line_rates_order_size.csv", index=False, encoding="utf-8-sig")

    profile, price_by_key = _profile_products(orders, all_transactions, thresholds["p90"])
    profile.to_csv(tables / "product_profile.csv", index=False, encoding="utf-8-sig")
    product_names = dict(zip(profile.get("product_key_hmac", []), profile.get("product_name_from_order_api", [])))
    product_months: dict[str, set[str]] = defaultdict(set)
    for order in orders:
        if order["is_gift"]:
            continue
        for line in order["gift_line_records"]:
            if line.get("product_key") and line["gift_source"] == "not_gift":
                product_months[line["product_key"]].add(order["month"])

    cleaning_maps = {
        "all_lines": all_transactions,
        "explicit_only": explicit_transactions,
        "all_gift_sources": clean_transactions,
    }
    cell_pairs: dict[str, dict[tuple[str, str], dict[str, Any]]] = {}
    cell_logs = []
    for cleaning_name, transactions in cleaning_maps.items():
        for support in SUPPORTS:
            cell_name = f"{cleaning_name}_support_{support:.2f}"
            pairs = _pair_counts(transactions, support)
            cell_pairs[cell_name] = pairs
            cell_logs.append({
                "cell": cell_name,
                "cleaning": cleaning_name,
                "min_support": support,
                "eligible_baskets": len(transactions),
                "qualifying_product_pairs": len(pairs),
                "rule_occurrences_floor": MIN_OCCURRENCES,
            })
    stability: Counter[tuple[str, str]] = Counter()
    for pairs in cell_pairs.values():
        stability.update(pairs.keys())
    stable_pairs = {pair for pair, count in stability.items() if count >= STABILITY_MIN_CELLS}
    primary_cell = cell_pairs["all_gift_sources_support_0.05"]
    stable_primary = sorted(stable_pairs & set(primary_cell))

    rule_rows = []
    combo_rows = []
    seasonal_rows = []
    for pair in stable_primary:
        metrics = primary_cell[pair]
        seasonal = _seasonality(pair, clean_transactions, product_months)
        seasonal_rows.append({
            "product_a_key_hmac": pair[0], "product_b_key_hmac": pair[1],
            "product_a": product_names.get(pair[0]), "product_b": product_names.get(pair[1]),
            **seasonal,
        })
        name_a = product_names.get(pair[0]) or "Sản phẩm không tên"
        name_b = product_names.get(pair[1]) or "Sản phẩm không tên"
        price_a, price_b = price_by_key.get(pair[0]), price_by_key.get(pair[1])
        combined_price = price_a + price_b if price_a is not None and price_b is not None else None
        combo_row = {
            "combo_name": f"{name_a} + {name_b}",
            "product_a_key_hmac": pair[0], "product_b_key_hmac": pair[1],
            "product_a": name_a, "product_b": name_b,
            "support": metrics["support"], "confidence_a_to_b": metrics["confidence_a_to_b"],
            "confidence_b_to_a": metrics["confidence_b_to_a"], "lift": metrics["lift"],
            "leverage": metrics["leverage"], "occurrences": metrics["occurrences"],
            "development_eligible_baskets": metrics["denominator"],
            "listed_price_a_vnd": price_a, "listed_price_b_vnd": price_b,
            "combined_nonzero_listed_price_vnd": combined_price,
            "stable_cells": int(stability[pair]), "cells_total": len(cell_pairs),
            "reason": f"Cặp ổn định ở {stability[pair]}/6 cấu hình; tối thiểu 5 giỏ; chỉ là đồng xuất hiện.",
            "seasonal_label": seasonal["seasonal_label"],
            "price_basis": "median observed non-zero retail_price by product_id; no discount allocation",
        }
        combo_rows.append(combo_row)
        rule_rows.extend([
            {"antecedent_product": name_a, "consequent_product": name_b,
             "antecedent_key_hmac": pair[0], "consequent_key_hmac": pair[1],
             "support": metrics["support"], "confidence": metrics["confidence_a_to_b"],
             "lift": metrics["lift"], "leverage": metrics["leverage"],
             "occurrences": metrics["occurrences"], "eligible_baskets": metrics["denominator"],
             "stable_cells": int(stability[pair]), "stability_cells_total": len(cell_pairs),
             **seasonal},
            {"antecedent_product": name_b, "consequent_product": name_a,
             "antecedent_key_hmac": pair[1], "consequent_key_hmac": pair[0],
             "support": metrics["support"], "confidence": metrics["confidence_b_to_a"],
             "lift": metrics["lift"], "leverage": metrics["leverage"],
             "occurrences": metrics["occurrences"], "eligible_baskets": metrics["denominator"],
             "stable_cells": int(stability[pair]), "stability_cells_total": len(cell_pairs),
             **seasonal},
        ])

    pd.DataFrame(rule_rows).to_csv(tables / "rules_v2.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(combo_rows).to_csv(tables / "combos_v2.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(seasonal_rows).to_csv(tables / "seasonal_pair_metrics.csv", index=False, encoding="utf-8-sig")
    product_basket_counts = {key: int(value) for key, value in Counter(item for tx in all_transactions for item in tx["items"]).items()}
    metrics = {
        "amendment_05_sha256": "",  # Filled by the runner after lock verification.
        "snapshot_id": data_stats["snapshot_id"],
        "status3_dev_orders": len(orders),
        "status3_order_gifts_excluded_from_baskets": int(sum(bool(order["is_gift"]) for order in orders)),
        "gift_line_audit": audit,
        "source_counts_by_order": {row["gift_source"]: row["distinct_order_count"] for row in audit_frame.to_dict("records")},
        "gift_line_rates_by_month_path": "outputs/tables/gift_line_rates_monthly.csv",
        "gift_line_rates_by_order_size_path": "outputs/tables/gift_line_rates_order_size.csv",
        "order_value_thresholds_vnd": {key: value for key, value in thresholds.items()},
        "large_order_definition": ">= development p90 of total_price",
        "eligible_baskets_before_gift_line_removal": before_count,
        "eligible_baskets_after_all_gift_line_removal": clean_count,
        "sensitivity_eligible_baskets": {"all_lines": all_count, "explicit_only": explicit_count, "all_gift_sources": clean_count},
        "missing_product_id_line_count": sum(line.get("product_key") is None for order in orders for line in order["gift_line_records"]),
        "min_support_values": list(SUPPORTS),
        "minimum_rule_occurrences": MIN_OCCURRENCES,
        "stable_combo_rule": f"pair present in at least {STABILITY_MIN_CELLS}/6 cleaning x support cells and in primary all_gift_sources support 0.05",
        "sensitivity_cells": cell_logs,
        "qualifying_product_pairs_across_cells": {name: len(pairs) for name, pairs in cell_pairs.items()},
        "stable_pair_count": len(stable_pairs),
        "main_combo_count": len(combo_rows),
        "seasonal_pair_metrics_path": "outputs/tables/seasonal_pair_metrics.csv",
        "tet_cycles_in_development": 1,
        "seasonal_label_window_days": 14,
        "product_profile_top20_support_keys": profile.head(20).get("product_key_hmac", pd.Series(dtype=str)).tolist(),
        "product_profile_path": "outputs/tables/product_profile.csv",
        "test_labels_loaded": False,
        "test_behavior_loaded": False,
    }
    (metrics_dir / "day3_combo_prereg.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return metrics


if __name__ == "__main__":
    print(json.dumps(run_day3_pretest(), indent=2, ensure_ascii=False))
