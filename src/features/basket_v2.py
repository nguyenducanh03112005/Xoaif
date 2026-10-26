"""Zero-price-cleaned Day 2B basket rules and companion-product proposals."""

from __future__ import annotations

from collections import Counter, defaultdict
import json
from pathlib import Path
from typing import Any
import unicodedata

import pandas as pd
from mlxtend.frequent_patterns import association_rules, fpgrowth
from mlxtend.preprocessing import TransactionEncoder

from features.day2_data import load_dev_orders

ROOT = Path(__file__).resolve().parents[2]
SUPPORT_CANDIDATES = (0.005, 0.01, 0.02, 0.03, 0.05)
MIN_OCCURRENCES = 5
PACKAGING_TERMS = ("túi", "giấy", "bao bì", "hộp", "gói", "bịch", "mica")
ACCESSORY_TERMS = ("phụ kiện", "portcard", "bảng tên", "thẻ", "tag", "que", "kẹp", "móc")


def _fold_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.casefold())
    return "".join(char for char in normalized if unicodedata.category(char) != "Mn")


def _mine(transactions: list[list[str]]) -> tuple[pd.DataFrame, list[dict[str, Any]], float]:
    if not transactions:
        return pd.DataFrame(), [], SUPPORT_CANDIDATES[0]
    encoder = TransactionEncoder()
    matrix = encoder.fit(transactions).transform(transactions)
    basket_frame = pd.DataFrame(matrix, columns=encoder.columns_)
    trials: list[dict[str, Any]] = []
    chosen: pd.DataFrame | None = None
    selected_support = SUPPORT_CANDIDATES[0]
    for support in SUPPORT_CANDIDATES:
        itemsets = fpgrowth(basket_frame, min_support=support, use_colnames=True, max_len=4)
        has_pairs = not itemsets.empty and bool(itemsets["itemsets"].map(len).ge(2).any())
        rules = association_rules(itemsets, metric="confidence", min_threshold=0.0) if has_pairs else pd.DataFrame()
        if not rules.empty:
            rules["occurrences"] = (rules["support"] * len(transactions)).round().astype(int)
            rules = rules[(rules["occurrences"] >= MIN_OCCURRENCES) & (rules["lift"] > 1.0)].copy()
        trials.append({
            "min_support": support,
            "qualifying_rule_count": int(len(rules)),
            "minimum_rule_occurrences": MIN_OCCURRENCES,
        })
        if len(rules) >= 5:
            chosen = rules
            selected_support = support
    if chosen is None:
        selected_support = SUPPORT_CANDIDATES[0]
        itemsets = fpgrowth(basket_frame, min_support=selected_support, use_colnames=True, max_len=4)
        has_pairs = not itemsets.empty and bool(itemsets["itemsets"].map(len).ge(2).any())
        chosen = association_rules(itemsets, metric="confidence", min_threshold=0.0) if has_pairs else pd.DataFrame()
        if not chosen.empty:
            chosen["occurrences"] = (chosen["support"] * len(transactions)).round().astype(int)
            chosen = chosen[(chosen["occurrences"] >= MIN_OCCURRENCES) & (chosen["lift"] > 1.0)].copy()
    return chosen, trials, selected_support


def _median_positive(values: list[float]) -> float | None:
    usable = sorted(value for value in values if value > 0)
    if not usable:
        return None
    middle = len(usable) // 2
    return usable[middle] if len(usable) % 2 else (usable[middle - 1] + usable[middle]) / 2


def run_baskets_v2() -> dict[str, Any]:
    tables = ROOT / "outputs" / "tables"
    metrics_dir = ROOT / "outputs" / "metrics"
    tables.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    orders, _, products = load_dev_orders()
    raw_item_prices: dict[str, list[float]] = defaultdict(list)
    clean_transactions: list[list[str]] = []
    category_transactions: list[list[str]] = []
    category_name_map: dict[str, str] = {}
    product_support_counts: Counter[str] = Counter()
    removed_zero_lines = 0
    before_baskets = 0
    after_baskets = 0
    gift_orders = 0
    no_line_orders = 0
    under_two_before = 0
    under_two_after = 0

    for order in orders:
        if order["is_gift"]:
            gift_orders += 1
            continue
        if not order["items_present"]:
            no_line_orders += 1
            continue
        original_keys = {item["product_key"] for item in order["items"] if item.get("product_key")}
        if len(original_keys) >= 2:
            before_baskets += 1
        else:
            under_two_before += 1
        retained: dict[str, dict[str, Any]] = {}
        for item in order["items"]:
            key = item.get("product_key")
            if not key:
                continue
            price = item.get("retail_price")
            if price is not None and float(price) == 0:
                removed_zero_lines += 1
                continue
            retained[key] = item
            if price is not None and float(price) > 0:
                raw_item_prices[key].append(float(price))
            category = item.get("category")
            if category is not None and str(category).strip():
                category_name_map[str(category)] = f"Danh mục mã {category}"
        keys = sorted(retained)
        if len(keys) < 2:
            under_two_after += 1
            continue
        after_baskets += 1
        clean_transactions.append(keys)
        product_support_counts.update(keys)
        categories = sorted({
            str(item.get("category")) for item in retained.values()
            if item.get("category") is not None and str(item.get("category")).strip()
        })
        if len(categories) >= 2:
            category_transactions.append(categories)

    names = {key: products.get(key, {}).get("name", "Sản phẩm không tên") for key in product_support_counts}
    categories = {key: products.get(key, {}).get("category") for key in product_support_counts}
    prices = {key: _median_positive(raw_item_prices.get(key, [])) for key in product_support_counts}
    supports = {key: count / after_baskets if after_baskets else 0.0 for key, count in product_support_counts.items()}

    companion_rows = []
    companion_keys: set[str] = set()
    for key in sorted(supports, key=lambda k: (-supports[k], str(names.get(k, "")))):
        name = str(names.get(key, "Sản phẩm không tên"))
        folded = _fold_text(name)
        packaging_hit = next((term for term in PACKAGING_TERMS if _fold_text(term) in folded), None)
        accessory_hit = next((term for term in ACCESSORY_TERMS if _fold_text(term) in folded), None)
        if packaging_hit:
            proposed_type = "Bao bì/đóng gói"
        elif accessory_hit:
            proposed_type = "Phụ kiện"
        elif supports[key] > 0.30:
            proposed_type = "Sản phẩm phổ biến/đi kèm theo support"
        else:
            proposed_type = "Sản phẩm chính hoặc chưa rõ"
        is_companion = bool(packaging_hit or accessory_hit or supports[key] > 0.30)
        if is_companion:
            companion_keys.add(key)
        companion_rows.append({
            "product_name": name,
            "support": supports[key],
            "basket_occurrences": product_support_counts[key],
            "retail_price_vnd": prices[key],
            "auto_proposed_type": proposed_type,
            "proposed_companion": is_companion,
            "owner_confirmation": "pending",
        })
    companion_rows = companion_rows[:20]
    # Classification applies to the whole product set; retain companion keys even if below top 20.
    all_companion_keys = companion_keys

    rules, support_trials, selected_support = _mine(clean_transactions)
    product_support_trials = list(support_trials)
    category_support_trials = None
    fallback_triggered = after_baskets < 100 or not support_trials or support_trials[0]["qualifying_rule_count"] < 5
    category_fallback_used = False
    fallback_note = None
    transactions_used = clean_transactions
    if fallback_triggered:
        if category_transactions:
            category_rules, category_trials, category_support = _mine(category_transactions)
            category_support_trials = category_trials
            if not category_rules.empty:
                rules = category_rules
                support_trials = category_trials
                selected_support = category_support
                transactions_used = category_transactions
                category_fallback_used = True
                fallback_note = "Category-code fallback used once; category names are not available and confidence is low."
            else:
                fallback_note = "Category fallback attempted once but yielded no qualifying rules."
        else:
            fallback_note = "Category fallback was unavailable because fewer than two known category codes occurred in any basket."

    records: list[dict[str, Any]] = []
    combo_map: dict[str, dict[str, Any]] = {}
    if not rules.empty:
        for _, rule in rules.iterrows():
            antecedents = set(rule["antecedents"])
            consequents = set(rule["consequents"])
            all_products = antecedents | consequents
            if category_fallback_used:
                item_names = sorted(category_name_map.get(str(key), f"Danh mục mã {key}") for key in all_products)
                retail_total = None
                companion_names: list[str] = []
            else:
                item_names = sorted({names.get(key, "Sản phẩm không tên") for key in all_products})
                price_values = [prices.get(key) for key in all_products]
                retail_total = sum(price_values) if price_values and all(value is not None and value > 0 for value in price_values) else None
                companion_names = sorted({names.get(key, "Sản phẩm không tên") for key in all_products if key in all_companion_keys})
            record = {
                "antecedent_products": " + ".join(sorted({names.get(key, category_name_map.get(str(key), str(key))) for key in antecedents})),
                "consequent_products": " + ".join(sorted({names.get(key, category_name_map.get(str(key), str(key))) for key in consequents})),
                "combo_name": " + ".join(item_names),
                "support": float(rule["support"]),
                "confidence": float(rule["confidence"]),
                "lift": float(rule["lift"]),
                "leverage": float(rule["leverage"]),
                "basket_occurrences": int(rule["occurrences"]),
                "combined_retail_price_vnd": retail_total,
                "companion_products_in_combo": " + ".join(companion_names),
                "owner_companion_confirmation": "pending",
                "price_note": "sum of observed positive retail_price per distinct product; zero-priced lines removed; no adjustment allocation",
                "interpretation": "co-occurrence only; no causal, discount, margin, or profit estimate",
                "confidence_note": "low confidence: category codes only" if category_fallback_used else "product-level rule; owner has not confirmed the companion proposal",
            }
            records.append(record)
            key = " + ".join(item_names)
            if key not in combo_map or (record["basket_occurrences"], record["lift"]) > (combo_map[key]["basket_occurrences"], combo_map[key]["lift"]):
                combo_map[key] = record
    records.sort(key=lambda row: (row["lift"], row["basket_occurrences"], row["confidence"]), reverse=True)
    combos = sorted(combo_map.values(), key=lambda row: (row["basket_occurrences"], row["lift"]), reverse=True)
    columns = [
        "antecedent_products", "consequent_products", "combo_name", "support", "confidence", "lift", "leverage",
        "basket_occurrences", "combined_retail_price_vnd", "companion_products_in_combo", "owner_companion_confirmation",
        "price_note", "interpretation", "confidence_note",
    ]
    pd.DataFrame(records, columns=columns).to_csv(tables / "rules_v2.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(combos, columns=columns).to_csv(tables / "combos_v2.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(companion_rows, columns=[
        "product_name", "support", "basket_occurrences", "retail_price_vnd", "auto_proposed_type", "proposed_companion", "owner_confirmation",
    ]).to_csv(tables / "companion_products_v2.csv", index=False, encoding="utf-8-sig")

    metrics = {
        "status3_dev_orders": len(orders),
        "gift_orders_excluded": gift_orders,
        "no_line_orders_excluded": no_line_orders,
        "eligible_baskets_before_zero_price_removal": before_baskets,
        "zero_price_item_lines_removed": removed_zero_lines,
        "eligible_baskets_after_zero_price_removal": after_baskets,
        "baskets_lost_below_two_products_after_cleaning": under_two_after,
        "support_denominator_baskets_used": len(transactions_used),
        "product_count_in_support_summary": len(supports),
        "top_20_companion_proposals": companion_rows,
        "companion_proposal_count_all_products": len(all_companion_keys),
        "owner_confirmation_pending": True,
        "support_trials": product_support_trials,
        "category_fallback_support_trials": category_support_trials,
        "selected_support_scope": "category_codes" if category_fallback_used else "product_ids",
        "selected_min_support": selected_support,
        "minimum_rule_occurrences": MIN_OCCURRENCES,
        "rule_count": len(records),
        "combo_count": len(combos),
        "category_fallback_triggered": fallback_triggered,
        "category_fallback_used": category_fallback_used,
        "category_fallback_note": fallback_note,
        "product_price_rule": "median observed positive retail_price per distinct product; unknown stays null; zero line items are excluded",
        "interpretation": "co-occurrence only; no discount allocation or profitability",
        "trial_runs_used": 1,
        "test_labels_loaded": False,
        "test_behavior_loaded": False,
    }
    (metrics_dir / "day2b_baskets.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return metrics


if __name__ == "__main__":
    run_baskets_v2()
