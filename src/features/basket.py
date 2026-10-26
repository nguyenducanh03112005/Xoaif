"""Frequent product co-occurrences on development-only non-gift baskets."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any

import pandas as pd
from mlxtend.frequent_patterns import association_rules, fpgrowth
from mlxtend.preprocessing import TransactionEncoder

ROOT = Path(__file__).resolve().parents[2]
SUPPORT_CANDIDATES = (0.005, 0.01, 0.02, 0.03, 0.05)
MIN_RULE_OCCURRENCES = 5


def _discover_rules(transactions: list[list[str]]) -> tuple[pd.DataFrame, dict[str, Any]]:
    encoder = TransactionEncoder()
    encoded = encoder.fit(transactions).transform(transactions)
    baskets = pd.DataFrame(encoded, columns=encoder.columns_)
    support_trials = []
    selected = None
    selected_support = None
    for support in SUPPORT_CANDIDATES:
        itemsets = fpgrowth(baskets, min_support=support, use_colnames=True, max_len=4)
        if itemsets.empty:
            rules = pd.DataFrame()
        else:
            rules = association_rules(itemsets, metric="confidence", min_threshold=0.0)
            if not rules.empty:
                rules["occurrences"] = (rules["support"] * len(transactions)).round().astype(int)
                rules = rules[(rules["occurrences"] >= MIN_RULE_OCCURRENCES) & (rules["lift"] > 1.0)]
        count = int(len(rules))
        support_trials.append({"min_support": support, "eligible_rule_count": count, "minimum_occurrences": MIN_RULE_OCCURRENCES})
        if count >= 5:
            selected = rules
            selected_support = support
    if selected is None:
        selected_support = SUPPORT_CANDIDATES[0]
        itemsets = fpgrowth(baskets, min_support=selected_support, use_colnames=True, max_len=4)
        selected = association_rules(itemsets, metric="confidence", min_threshold=0.0) if not itemsets.empty else pd.DataFrame()
        if not selected.empty:
            selected["occurrences"] = (selected["support"] * len(transactions)).round().astype(int)
            selected = selected[(selected["occurrences"] >= MIN_RULE_OCCURRENCES) & (selected["lift"] > 1.0)]
    note = {
        "supports_tried": support_trials,
        "selected_min_support": selected_support,
        "selection_rule": "highest min_support that still produces at least five rules with lift > 1 and at least five basket occurrences; if none, use the lowest tested support and report the small rule set",
        "minimum_rule_occurrences": MIN_RULE_OCCURRENCES,
    }
    return selected, note


def _name_set(items, products: dict[str, dict[str, Any]]) -> list[str]:
    return sorted({products.get(key, {}).get("name", "Sản phẩm không tên") for key in items})


def _price_total(items, products: dict[str, dict[str, Any]]) -> float | None:
    total = 0.0
    for key in items:
        price = products.get(key, {}).get("retail_price")
        if price is None:
            return None
        total += float(price)
    return total


def run_baskets(orders: list[dict[str, Any]] | None = None, products: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    if orders is None or products is None:
        from features.day2_data import load_dev_orders
        orders, _, products = load_dev_orders()
    tables = ROOT / "outputs" / "tables"
    metrics_dir = ROOT / "outputs" / "metrics"
    tables.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    all_transactions = []
    eligible_orders = 0
    excluded_gift = 0
    excluded_no_lines = 0
    excluded_less_two = 0
    category_transactions = []
    for order in orders:
        if order["is_gift"]:
            excluded_gift += 1
            continue
        if not order["items_present"]:
            excluded_no_lines += 1
            continue
        product_keys = sorted(set(order["product_keys"]))
        if len(product_keys) < 2:
            excluded_less_two += 1
            continue
        eligible_orders += 1
        all_transactions.append(product_keys)
        categories = sorted({
            item["category"] for item in order["items"] if item.get("category")
        })
        if len(categories) >= 2:
            category_transactions.append(categories)

    use_categories = len(all_transactions) < 30
    transactions = category_transactions if use_categories else all_transactions
    if not transactions:
        metrics = {
            "status3_dev_orders": len(orders), "eligible_product_baskets": eligible_orders,
            "baskets_used": 0, "rule_count": 0, "category_fallback_used": use_categories,
            "basket_stage_counts": {"excluded_gifts": excluded_gift, "excluded_no_lines": excluded_no_lines, "excluded_less_than_two_distinct_products": excluded_less_two},
            "note": "No baskets with at least two usable products/categories; no association rules estimated.",
            "test_labels_loaded": False, "test_behavior_loaded": False,
        }
        _write_empty(tables)
        (metrics_dir / "day2_baskets.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
        print("Baskets: eligible=0; no rules estimated.")
        return metrics

    rules, selection = _discover_rules(transactions)
    names = products
    if use_categories:
        names = {category: {"name": f"Danh mục mã {category}", "retail_price": None} for basket in transactions for category in basket}
    records = []
    combos = {}
    for _, row in rules.iterrows():
        antecedents = set(row["antecedents"])
        consequents = set(row["consequents"])
        all_items = antecedents | consequents
        labels_a = _name_set(antecedents, names)
        labels_c = _name_set(consequents, names)
        labels_all = _name_set(all_items, names)
        price = _price_total(all_items, names)
        record = {
            "antecedent_products": " + ".join(labels_a),
            "consequent_products": " + ".join(labels_c),
            "combo_name": " + ".join(labels_all),
            "support": float(row["support"]),
            "confidence": float(row["confidence"]),
            "lift": float(row["lift"]),
            "basket_occurrences": int(row["occurrences"]),
            "combined_retail_price_vnd": price,
            "price_basis": "sum of median observed variation retail_price per distinct product; no adjustment allocation",
            "confidence_note": "low confidence: category codes only; no category names or list prices" if use_categories else "product-level rules; price_adjustment stays at order level",
        }
        records.append(record)
        key = " + ".join(labels_all)
        old = combos.get(key)
        if old is None or (record["lift"], record["basket_occurrences"]) > (old["lift"], old["basket_occurrences"]):
            combos[key] = record
    records.sort(key=lambda row: (row["lift"], row["basket_occurrences"], row["confidence"]), reverse=True)
    combo_rows = sorted(combos.values(), key=lambda row: (row["basket_occurrences"], row["lift"]), reverse=True)
    output_columns = ["antecedent_products", "consequent_products", "combo_name", "support", "confidence", "lift", "basket_occurrences", "combined_retail_price_vnd", "price_basis", "confidence_note"]
    pd.DataFrame(records, columns=output_columns).to_csv(tables / "rules.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(combo_rows, columns=output_columns).to_csv(tables / "combos.csv", index=False, encoding="utf-8-sig")
    metrics = {
        "status3_dev_orders": len(orders),
        "eligible_product_baskets": eligible_orders,
        "baskets_used": len(transactions),
        "basket_eligibility_rate": len(transactions) / len(orders) if orders else None,
        "rule_count": len(records),
        "combo_count": len(combo_rows),
        "basket_stage_counts": {
            "excluded_gifts": excluded_gift,
            "excluded_no_lines": excluded_no_lines,
            "excluded_less_than_two_distinct_products": excluded_less_two,
        },
        "category_fallback_used": use_categories,
        "category_fallback_note": "low confidence: category names and list prices unavailable; source exposes category codes only" if use_categories else None,
        "selection": selection,
        "interpretation": "co-occurrence only; does not establish causal effect or profitability",
        "product_price_basis": "retail_price summaries; price_adjustment is order-level and is not allocated to products",
        "test_labels_loaded": False,
        "test_behavior_loaded": False,
    }
    (metrics_dir / "day2_baskets.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Baskets: eligible={eligible_orders}, used={len(transactions)}, rules={len(records)}, support={selection['selected_min_support']}.")
    return metrics


def _write_empty(tables: Path) -> None:
    pd.DataFrame(columns=["antecedent_products", "consequent_products", "combo_name", "support", "confidence", "lift", "basket_occurrences", "combined_retail_price_vnd", "price_basis", "confidence_note"]).to_csv(tables / "rules.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(columns=["antecedent_products", "consequent_products", "combo_name", "support", "confidence", "lift", "basket_occurrences", "combined_retail_price_vnd", "price_basis", "confidence_note"]).to_csv(tables / "combos.csv", index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    run_baskets()
