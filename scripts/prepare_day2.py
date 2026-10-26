"""Build development-only customer features and the pre-registered dev label cohort."""

from __future__ import annotations
from collections import Counter
from datetime import date
import json
from pathlib import Path
import sys

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from features.day2_data import build_label_samples, load_dev_orders, make_customer_features, write_csv


def main() -> int:
    try:
        split = yaml.safe_load((ROOT / "config" / "split.yaml").read_bytes())
        orders, stats, products = load_dev_orders()
        test_start = date.fromisoformat(str(split["test_start"]))
        samples, label_summary = build_label_samples(orders, test_start=test_start)
        # The internal customer-key set is used only for in-memory assertions; it is not an output.
        label_summary.pop("unique_customer_keys", None)
        customer_keys = {row["customer_key"] for row in orders if row["customer_key"] and not row["is_gift"]}
        variants = {
            "primary": {"monetary_variant": "primary", "exclude_adjusted": False},
            "A": {"monetary_variant": "A", "exclude_adjusted": False},
            "B": {"monetary_variant": "primary", "exclude_adjusted": True},
        }
        latest_by_variant = {}
        for variant, options in variants.items():
            latest_by_variant[variant] = make_customer_features(
                orders, as_of=test_start, customer_keys=customer_keys, **options
            )
            write_csv(ROOT / "outputs" / "tables" / f"day2_features_{variant}.csv", latest_by_variant[variant])

        sample_features: dict[str, dict[tuple[str, str], dict]] = {name: {} for name in variants}
        samples_by_t: dict[str, list[str]] = {}
        for sample in samples:
            samples_by_t.setdefault(sample["T"], []).append(sample["customer_key"])
        for t_text, keys in samples_by_t.items():
            t = date.fromisoformat(t_text)
            key_set = set(keys)
            for variant, options in variants.items():
                feature_rows = make_customer_features(
                    orders, as_of=t, customer_keys=key_set, **options
                )
                for feature in feature_rows:
                    sample_features[variant][(feature["customer_key"], t_text)] = feature

        label_by_key = {(row["customer_key"], row["T"]): row["label_returned"] for row in samples}
        for variant in variants:
            combined = []
            for sample in samples:
                key = (sample["customer_key"], sample["T"])
                feature = sample_features[variant].get(key)
                if feature is None:
                    raise ValueError("pre-registered sample did not receive a feature row")
                combined.append({**feature, "label_returned": label_by_key[key]})
            write_csv(ROOT / "outputs" / "tables" / f"day2_label_samples_{variant}.csv", combined)

        primary = latest_by_variant["primary"]
        freq_counts = Counter(str(int(row["frequency"])) for row in primary)
        money = np.asarray([row["monetary"] for row in primary], dtype=float)
        order_max = np.asarray([row["max_order_value"] for row in primary], dtype=float)
        monetary_p99 = float(np.quantile(money, 0.99)) if len(money) else None
        max_order_p99 = float(np.quantile(order_max, 0.99)) if len(order_max) else None
        large_keys = {
            row["customer_key"] for row in primary
            if (monetary_p99 is not None and row["monetary"] >= monetary_p99)
            or (max_order_p99 is not None and row["max_order_value"] >= max_order_p99)
        }
        labels_positive = int(label_summary["positive_samples"])
        label_summary["frequency_distribution_at_test_start"] = dict(sorted(freq_counts.items(), key=lambda pair: int(pair[0])))
        label_summary["large_value_customer_proxy"] = {
            "rule": "Monetary >= development p99 OR maximum order value >= development p99",
            "monetary_p99": monetary_p99,
            "maximum_order_value_p99": max_order_p99,
            "customers": len(large_keys),
            "share": len(large_keys) / len(primary) if primary else None,
        }
        label_summary["label_threshold_decision"] = {
            "under_100_positive_or_under_5_percent": labels_positive < 100 or (label_summary["positive_rate"] or 0) < 0.05,
            "under_30_positive_stop": labels_positive < 30,
            "action_if_under_100_or_5_percent": "temporal_cross_validation_and_customer_bootstrap_CI; no_strong_claims",
            "action_if_under_30": "stop_before_models_and_report_alternative_second_purchase_question",
        }
        label_summary["label_definition"] = "at least one non-gift status-3 order in (T,T+180 days]"
        label_summary["feature_cutoff_rule"] = "all feature orders have local_date < T"
        label_summary["customer_keys_disjoint_by_construction"] = True
        label_summary["test_labels_loaded"] = False
        label_summary["test_behavior_loaded"] = False
        (ROOT / "outputs" / "metrics").mkdir(parents=True, exist_ok=True)
        (ROOT / "outputs" / "metrics" / "day2_preprocessing.json").write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
        (ROOT / "outputs" / "metrics" / "day2_label_audit.json").write_text(json.dumps(label_summary, indent=2) + "\n", encoding="utf-8")
        product_summary = {
            "product_count_with_pseudonym": len(products),
            "product_count_with_list_price": sum(product["retail_price"] is not None for product in products.values()),
            "no_product_id_rows_are_omitted_from_baskets": True,
        }
        (ROOT / "outputs" / "metrics" / "day2_product_metadata_summary.json").write_text(json.dumps(product_summary, indent=2) + "\n", encoding="utf-8")
        print(
            f"Day 2 preparation: status3={stats['status3_dev_orders']}, missing_customer={stats['missing_customer_id_orders']}, "
            f"gifts={stats['gift_orders']}, no_line_items={stats['orders_without_line_items']}; "
            f"label_samples={label_summary['customer_samples']}, positives={labels_positive} ({label_summary['positive_rate']:.2%})."
        )
        if labels_positive < 30:
            print("STOP: fewer than 30 positive development labels; no Day 2 modeling was started.")
            return 5
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"Day 2 preparation stopped ({type(exc).__name__}); no order identifiers or customer data were printed.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

