"""Open and score the locked test interval exactly once; never fit a model."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal
import csv
import hashlib
import json
from pathlib import Path
import sys
from typing import Any
from zoneinfo import ZoneInfo

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score, confusion_matrix, f1_score, precision_score,
    recall_score, roc_auc_score,
)
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from features.day2_data import (
    canonical_province, load_dev_orders, local_day, make_customer_features,
    normalize_product_name, safe_status,
)
from features.day2b_data import make_repurchase_features
from features.gift_lines import classify_order_lines
from features.money import assess_order_money, decimal_value
from ingest.identifiers import pseudonymize_id
from ingest.settings import load_analytics_hmac_key
from ingest.test_open_lock import TestAlreadyOpenedError, create_test_open_lock
from models.classify import CATEGORICAL_COLUMNS as V1_CATEGORICAL
from models.classify import NUMERIC_COLUMNS as V1_NUMERIC

LOCAL_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
BOOTSTRAP_REPETITIONS = 2000
BOOTSTRAP_SEED = 20261026


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _locked_paths() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    config_path = ROOT / "config" / "amendment_05_test_open.yaml"
    sidecar_path = ROOT / "config" / "amendment_05_test_open.lock.json"
    config = yaml.safe_load(config_path.read_bytes())
    sidecar = _read_json(sidecar_path)
    if sha256(config_path) != sidecar.get("config_sha256"):
        raise ValueError("Test-open configuration hash differs from its lock")
    freeze_path = ROOT / "outputs" / "metrics" / "day3_pretest_freeze.json"
    if sha256(freeze_path) != sidecar.get("frozen_manifest_sha256"):
        raise ValueError("The pre-test freeze manifest changed after preregistration")
    for relative, expected in sidecar.get("frozen_sources_sha256", {}).items():
        if sha256(ROOT / relative) != expected:
            raise ValueError(f"A preregistered source changed: {relative}")
    if config.get("pre_open_evidence", {}).get("test_labels_loaded") is not False:
        raise ValueError("Configuration does not attest zero pre-open label reads")
    if config.get("pre_open_evidence", {}).get("test_behavior_loaded") is not False:
        raise ValueError("Configuration does not attest zero pre-open behavior reads")
    if (ROOT / "outputs" / "metrics" / "test_opened.lock.json").exists():
        raise TestAlreadyOpenedError("The one-time test set has already been opened.")
    if (ROOT / "outputs" / "logs" / "test_eval_access.jsonl").exists():
        raise ValueError("Post-open access log exists without the one-time lock")
    return config, sidecar, _read_json(freeze_path)


def _append_access_event(kind: str, config: dict[str, Any]) -> None:
    path = ROOT / "outputs" / "logs" / "test_eval_access.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "kind": kind,
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "test_interval": config["test_interval"],
        "values_or_identifiers_logged": False,
        "evaluation_run": 1,
    }
    mode = "x" if not path.exists() else "a"
    with path.open(mode, encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def _load_test_window(config: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """After lock creation only: inspect rows whose local dates are in test interval."""
    split = yaml.safe_load((ROOT / "config" / "split.yaml").read_bytes())
    manifest_path = ROOT / "data" / "raw" / "pancake_orders" / split["snapshot_id"] / "manifest.json"
    manifest_bytes = manifest_path.read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != split["snapshot_manifest_sha256"]:
        raise ValueError("Locked snapshot manifest hash mismatch after opening")
    manifest = json.loads(manifest_bytes)
    start = date.fromisoformat(config["test_interval"]["start_inclusive"])
    end = date.fromisoformat(config["test_interval"]["end_exclusive"])
    hmac_key = load_analytics_hmac_key(ROOT / "xoaif.env")
    snapshot_root = manifest_path.parent.resolve()
    seen = 0
    in_window = 0
    status_counts: Counter[str] = Counter()
    result: list[dict[str, Any]] = []
    for page_no, page in enumerate(manifest.get("pages", []), start=1):
        path = (snapshot_root / str(page["file"])).resolve()
        if not path.is_relative_to(snapshot_root):
            raise ValueError("Snapshot page path escaped the locked folder")
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != page.get("sha256"):
            raise ValueError("Snapshot page checksum mismatch after opening")
        payload = json.loads(raw)
        rows = payload.get("data", [])
        if payload.get("page_number") != page_no or len(rows) != page.get("rows"):
            raise ValueError("Snapshot page metadata mismatch after opening")
        for source in rows:
            seen += 1
            if not isinstance(source, dict):
                continue
            # No source field except inserted_at is accessed until the row falls in test.
            day = local_day(source.get("inserted_at"))
            if day is None or day < start or day >= end:
                continue
            in_window += 1
            status = safe_status(source.get("status"))
            status_counts[str(status) if status is not None else "<MISSING>"] += 1
            if status != 3:
                continue
            assessment = assess_order_money(source)
            customer = source.get("customer")
            raw_customer = customer.get("customer_id") if isinstance(customer, dict) else None
            customer_key = (
                pseudonymize_id(raw_customer, key=hmac_key, namespace="xoaif/customer/v1")
                if raw_customer is not None and str(raw_customer).strip() else None
            )
            source_items = source.get("items")
            source_items = source_items if isinstance(source_items, list) else []
            line_records: list[dict[str, Any]] = []
            product_names: dict[str, str] = {}
            quantity = Decimal(0)
            for index, item in enumerate(source_items):
                if not isinstance(item, dict):
                    continue
                raw_product_id = item.get("product_id")
                product_key = (
                    pseudonymize_id(raw_product_id, key=hmac_key, namespace="xoaif/product/v1")
                    if raw_product_id is not None and str(raw_product_id).strip() else None
                )
                variation = item.get("variation_info")
                variation = variation if isinstance(variation, dict) else {}
                product_name = normalize_product_name(variation.get("name"))
                if product_key and product_name:
                    product_names[product_key] = product_name
                item_quantity = decimal_value(item.get("quantity"))
                if item_quantity is not None:
                    quantity += item_quantity
                categories = variation.get("category_ids")
                category_ids = [str(v).strip() for v in categories if v is not None and str(v).strip()] if isinstance(categories, list) else []
                line_records.append({
                    "source_line_index": index,
                    "product_key": product_key,
                    "quantity": item_quantity,
                    "retail_price": decimal_value(variation.get("retail_price")),
                    "product_name": product_name,
                    "category_ids": category_ids,
                    "bonus_flag": item.get("is_bonus_product") if isinstance(item.get("is_bonus_product"), bool) else None,
                    "discount_each_product": decimal_value(item.get("discount_each_product")),
                    "is_discount_percent": item.get("is_discount_percent") if isinstance(item.get("is_discount_percent"), bool) else None,
                    "line_total_discount": decimal_value(item.get("total_discount")),
                    "variation_key": pseudonymize_id(item.get("variation_id"), key=hmac_key, namespace="xoaif/variation/v1") if item.get("variation_id") is not None else None,
                })
            shipping_address = source.get("shipping_address")
            province = canonical_province(shipping_address.get("province_name")) if isinstance(shipping_address, dict) else None
            order = {
                "date": day,
                "month": day.strftime("%Y-%m"),
                "status": status,
                "customer_key": customer_key,
                "is_gift": assessment.is_gift,
                "revenue_recognized": assessment.revenue_recognized,
                "monetary_contribution": assessment.monetary_contribution,
                "total_price_at_snapshot": decimal_value(source.get("total_price")),
                "total_discount_at_snapshot": decimal_value(source.get("total_discount")),
                "gross_list_value": decimal_value(source.get("total_price")),
                "quantity_total": quantity,
                "province": province,
                "items": source_items,
                "gift_line_records": line_records,
                "product_names": product_names,
            }
            order["gift_line_records"] = classify_order_lines(order)
            result.append(order)
    if seen != manifest.get("row_count"):
        raise ValueError("Source snapshot row reconciliation failed after opening")
    return result, dict(status_counts)


def _metric_values(y: np.ndarray, score: np.ndarray, threshold: float) -> dict[str, Any]:
    predicted = (score >= threshold).astype(int)
    matrix = confusion_matrix(y, predicted, labels=[0, 1]).tolist()
    return {
        "precision": float(precision_score(y, predicted, zero_division=0)) if len(y) else None,
        "recall": float(recall_score(y, predicted, zero_division=0)) if len(y) else None,
        "f1": float(f1_score(y, predicted, zero_division=0)) if len(y) else None,
        "roc_auc": float(roc_auc_score(y, score)) if len(np.unique(y)) == 2 else None,
        "average_precision": float(average_precision_score(y, score)) if len(y) else None,
        "confusion_matrix_tn_fp_fn_tp": matrix,
        "threshold": float(threshold),
    }


def _bootstrap(y: np.ndarray, scores: dict[str, np.ndarray], baseline: np.ndarray) -> dict[str, Any]:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    sample_n = len(y)
    names = list(scores)
    collected: dict[str, dict[str, list[float]]] = {
        name: {metric: [] for metric in ("precision", "recall", "f1", "roc_auc", "average_precision")}
        for name in names
    }
    delta: dict[str, list[float]] = {name: [] for name in names if name != "majority_baseline"}
    roc_valid: Counter[str] = Counter()
    for _ in range(BOOTSTRAP_REPETITIONS):
        idx = rng.integers(0, sample_n, sample_n)
        yb = y[idx]
        base_ap = float(average_precision_score(yb, baseline[idx]))
        for name, score in scores.items():
            sb = score[idx]
            pred = (sb >= 0.5).astype(int)
            collected[name]["precision"].append(float(precision_score(yb, pred, zero_division=0)))
            collected[name]["recall"].append(float(recall_score(yb, pred, zero_division=0)))
            collected[name]["f1"].append(float(f1_score(yb, pred, zero_division=0)))
            collected[name]["average_precision"].append(float(average_precision_score(yb, sb)))
            if len(np.unique(yb)) == 2:
                collected[name]["roc_auc"].append(float(roc_auc_score(yb, sb)))
                roc_valid[name] += 1
            if name != "majority_baseline":
                delta[name].append(float(average_precision_score(yb, sb)) - base_ap)

    def interval(values: list[float]) -> dict[str, Any] | None:
        if not values:
            return None
        low, high = np.quantile(np.asarray(values, dtype=float), [0.025, 0.975])
        return {"lower": float(low), "upper": float(high)}

    result: dict[str, Any] = {}
    for name in names:
        result[name] = {
            "metrics_95_ci": {metric: interval(values) for metric, values in collected[name].items()},
            "valid_roc_bootstrap_repetitions": int(roc_valid[name]),
        }
    result["paired_average_precision_delta_vs_baseline_95_ci"] = {
        name: interval(values) for name, values in delta.items()
    }
    result["repetitions"] = BOOTSTRAP_REPETITIONS
    result["seed"] = BOOTSTRAP_SEED
    return result


def _apply_segments(frame: pd.DataFrame, dev: pd.DataFrame, bundle: dict[str, Any], thresholds: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    work = frame.copy()
    reference = dev.copy()
    for k in (2, 3, 4):
        model = bundle["models"][k]
        for cohort in (work, reference):
            features = np.column_stack([
                cohort["recency_days"].astype(float).to_numpy(),
                np.log1p(cohort["frequency"].astype(float).to_numpy()),
                np.log1p(cohort["monetary"].clip(lower=0).astype(float).to_numpy()),
            ])
            raw = model["scaler"].transform(features)
            labels = model["estimator"].predict(raw)
            cohort[f"k{k}_segment"] = [int(model["label_mapping"][int(v)]) for v in labels]

    freq_cut = float(thresholds["frequency_p25"])
    money_cut = float(thresholds["monetary_p75"])
    rule_freq_cut = float(thresholds["frequency_p25"])
    proxy_money = float(thresholds["monetary_p99"])
    proxy_order = float(thresholds["max_order_value_p99"])
    one_order_recency = float(thresholds["one_order_recency_p50"])

    def rule_label(row: pd.Series) -> str:
        proxy = row["frequency"] <= freq_cut and (row["monetary"] >= proxy_money or row["max_order_value"] >= proxy_order)
        if proxy:
            suffix = "Giá trị lớn, tần suất thấp"
        elif row["monetary"] >= money_cut:
            suffix = "Giá trị cao"
        elif row["frequency"] >= 2:
            suffix = "Mua lặp lại"
        elif row["recency_days"] <= one_order_recency:
            suffix = "Mua một lần gần đây"
        else:
            suffix = "Mua một lần đã lâu"
        return "Theo quy tắc nghiệp vụ — " + suffix

    work["rule_segment"] = work.apply(rule_label, axis=1)
    reference["rule_segment"] = reference.apply(rule_label, axis=1)
    dev_rule_labels = set(reference["rule_segment"])
    # The rule label map uses the frozen dev thresholds; no test-derived cut points.
    profiles: list[dict[str, Any]] = []
    comparisons: dict[str, Any] = {}
    schemes: list[tuple[str, str]] = [(f"K={k}", f"k{k}_segment") for k in (2, 3, 4)] + [("Quy tắc nghiệp vụ", "rule_segment")]
    for scheme, column in schemes:
        test_groups = work.groupby(column, sort=True, dropna=False)
        dev_groups = reference.groupby(column, sort=True, dropna=False)
        names = sorted(set(test_groups.groups) | set(dev_groups.groups), key=str)
        t_share = work[column].value_counts(normalize=True, dropna=False).to_dict()
        d_share = reference[column].value_counts(normalize=True, dropna=False).to_dict()
        tv = 0.5 * sum(abs(float(t_share.get(name, 0)) - float(d_share.get(name, 0))) for name in names)
        comparisons[scheme] = {"customer_mix_total_variation_distance": float(tv)}
        for segment in names:
            tg = test_groups.get_group(segment) if segment in test_groups.groups else work.iloc[0:0]
            dg = dev_groups.get_group(segment) if segment in dev_groups.groups else reference.iloc[0:0]
            def row_for(group: pd.DataFrame, label: str, cohort: str) -> dict[str, Any]:
                monetary_sum = float(group["monetary"].sum()) if len(group) else 0.0
                total_monetary = float(work["monetary"].sum()) if cohort == "test_pre_T" else float(reference["monetary"].sum())
                return {
                    "scheme": scheme,
                    "segment": str(label),
                    "cohort": cohort,
                    "customers": int(len(group)),
                    "customer_share": float(len(group) / (len(work) if cohort == "test_pre_T" else len(reference))) if len(group) else 0.0,
                    "pre_T_recognized_revenue_vnd": monetary_sum,
                    "pre_T_revenue_share": monetary_sum / total_monetary if total_monetary else 0.0,
                    "mean_recency_days": float(group["recency_days"].mean()) if len(group) else None,
                    "mean_frequency": float(group["frequency"].mean()) if len(group) else None,
                    "mean_monetary_vnd": float(group["monetary"].mean()) if len(group) else None,
                }
            profiles.append(row_for(dg, segment, "development"))
            profiles.append(row_for(tg, segment, "test_pre_T"))
        for feature in ("recency_days", "frequency", "monetary"):
            if len(work) and len(reference):
                from scipy.stats import wasserstein_distance
                dev_values = reference[feature].astype(float).to_numpy()
                test_values = work[feature].astype(float).to_numpy()
                scale = float(np.quantile(dev_values, .75) - np.quantile(dev_values, .25))
                distance = float(wasserstein_distance(dev_values, test_values))
                comparisons[scheme][f"{feature}_wasserstein_over_dev_iqr"] = distance / scale if scale else None
    return work, pd.DataFrame(profiles), comparisons


def _pair_metrics(baskets: list[set[str]], pair: tuple[str, str]) -> dict[str, Any]:
    denom = len(baskets)
    a, b = pair
    count_a = sum(a in basket for basket in baskets)
    count_b = sum(b in basket for basket in baskets)
    count_ab = sum(a in basket and b in basket for basket in baskets)
    support = count_ab / denom if denom else 0.0
    support_a = count_a / denom if denom else 0.0
    support_b = count_b / denom if denom else 0.0
    return {
        "test_eligible_baskets": denom,
        "pair_occurrences": count_ab,
        "support": support,
        "confidence_a_to_b": count_ab / count_a if count_a else 0.0,
        "confidence_b_to_a": count_ab / count_b if count_b else 0.0,
        "lift": support / (support_a * support_b) if support_a and support_b else None,
        "support_a": support_a,
        "support_b": support_b,
    }


def _write_rows(path: Path, rows: list[dict[str, Any]] | pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = rows if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def _dashboard_aggregates(dev_orders: list[dict[str, Any]], test_orders: list[dict[str, Any]], status_counts: dict[str, int], dev_status_counts: dict[str, int]) -> dict[str, str]:
    sales_orders = [o for o in dev_orders if not o["is_gift"] and o["revenue_recognized"] is not None]
    sales_orders += [o for o in test_orders if not o["is_gift"] and o["revenue_recognized"] is not None]
    monthly: dict[str, dict[str, Any]] = {}
    provinces: dict[str, dict[str, Any]] = {}
    product: dict[str, dict[str, Any]] = {}
    status_rows = [{"period": "development", "status_code": k, "order_count": v} for k, v in dev_status_counts.items()]
    status_rows += [{"period": "test", "status_code": k, "order_count": v} for k, v in status_counts.items()]
    for order in sales_orders:
        month = order["month"]
        recognized = float(order["revenue_recognized"] or Decimal(0))
        row = monthly.setdefault(month, {"month": month, "recognized_revenue_vnd": 0.0, "orders": 0})
        row["recognized_revenue_vnd"] += recognized
        row["orders"] += 1
        province = order.get("province") or "UNKNOWN"
        prow = provinces.setdefault(province, {"province": province, "recognized_revenue_vnd": 0.0, "orders": 0})
        prow["recognized_revenue_vnd"] += recognized
        prow["orders"] += 1
        line_rows = order.get("gift_line_records") or []
        names = order.get("product_names") or {}
        for line in line_rows:
            key = line.get("product_key")
            if not key or line.get("gift_line"):
                continue
            name = names.get(key) or line.get("product_name") or "Sản phẩm không tên"
            prow_product = product.setdefault(key, {"product_name": name, "line_count": 0, "order_count": 0, "quantity": 0.0, "_orders": set()})
            prow_product["line_count"] += 1
            prow_product["quantity"] += float(line.get("quantity") or 0)
            prow_product["_orders"].add(order.get("order_sequence", id(order)))
    product_rows = []
    for row in product.values():
        product_rows.append({k: v for k, v in row.items() if k != "_orders"} | {"order_count": len(row["_orders"])})
    tables = ROOT / "outputs" / "tables"
    _write_rows(tables / "dashboard_sales_monthly.csv", sorted(monthly.values(), key=lambda r: r["month"]))
    _write_rows(tables / "dashboard_sales_province.csv", sorted(provinces.values(), key=lambda r: (-r["recognized_revenue_vnd"], r["province"])))
    _write_rows(tables / "dashboard_product_orders.csv", sorted(product_rows, key=lambda r: (-r["order_count"], r["product_name"])))
    _write_rows(tables / "dashboard_status_counts.csv", status_rows)
    return {
        "sales_monthly": "outputs/tables/dashboard_sales_monthly.csv",
        "sales_province": "outputs/tables/dashboard_sales_province.csv",
        "product_orders": "outputs/tables/dashboard_product_orders.csv",
        "status_counts": "outputs/tables/dashboard_status_counts.csv",
    }


def _development_status_counts() -> dict[str, int]:
    """Status counts for the dev interval; raw scan is date-gated before status access."""
    split = yaml.safe_load((ROOT / "config" / "split.yaml").read_bytes())
    start = date(2024, 4, 1)
    end = date.fromisoformat(str(split["test_start"]))
    manifest_path = ROOT / "data" / "raw" / "pancake_orders" / split["snapshot_id"] / "manifest.json"
    manifest = _read_json(manifest_path)
    status: Counter[str] = Counter()
    for page in manifest["pages"]:
        payload = json.loads((manifest_path.parent / page["file"]).read_bytes())
        for row in payload.get("data", []):
            if not isinstance(row, dict):
                continue
            day = local_day(row.get("inserted_at"))
            if day is None or day < start or day >= end:
                continue
            value = safe_status(row.get("status"))
            status[str(value) if value is not None else "<MISSING>"] += 1
    return dict(status)


def evaluate_once() -> dict[str, Any]:
    config, sidecar, freeze = _locked_paths()
    split = yaml.safe_load((ROOT / "config" / "split.yaml").read_bytes())
    registry = _read_json(ROOT / "outputs" / "metrics" / "dev_final_models_v2.json")
    dev_orders, dev_stats, _ = load_dev_orders()  # Development rows only; timestamp gate is inside loader.
    from features.gift_lines import classify_orders
    dev_orders, _ = classify_orders(dev_orders)
    start = date.fromisoformat(config["test_interval"]["start_inclusive"])
    end = date.fromisoformat(config["test_interval"]["end_exclusive"])
    eligible_keys = {order["customer_key"] for order in dev_orders if order["customer_key"] and not order["is_gift"]}
    if len(eligible_keys) < int(split["min_test_eligible_customers"]):
        raise ValueError("Development-derived test cohort is below the locked minimum")
    samples = [{"customer_key": key, "T": start.isoformat(), "label_returned": 0} for key in sorted(eligible_keys)]
    base = pd.DataFrame(make_customer_features(
        dev_orders, as_of=start, customer_keys=eligible_keys,
        analysis_start=date.fromisoformat(dev_stats["analysis_start"]),
    ))
    if base["customer_key"].duplicated().any() or len(base) != len(eligible_keys):
        raise ValueError("Pre-test RFM features are not one row per eligible customer")
    extended_rows, _ = make_repurchase_features(samples)
    extended = pd.DataFrame(extended_rows)
    extended["as_of"] = extended["T"]
    if extended["customer_key"].duplicated().any() or len(extended) != len(base):
        raise ValueError("Frozen v2 feature assembly does not match the eligible cohort")
    feature_frame = base.merge(extended, on=["customer_key", "as_of"], suffixes=("", "_v2"), validate="one_to_one")
    # The v2 generator returns the common base features plus registered latest-order predictors.
    for name in ("last_order_product_count", "last_order_primary_product_group", "last_order_discount_rate",
                 "last_order_revenue_recognized", "last_order_channel", "last_order_province",
                 "last_order_month", "last_order_month_sin", "last_order_month_cos",
                 "last_order_holiday_distance_days"):
        feature_frame[name] = extended.set_index("customer_key").loc[feature_frame["customer_key"], name].to_numpy()

    # Validate and score the fully frozen pre-T feature matrix before any test row is read.
    old_model = joblib.load(ROOT / "outputs" / "models" / "day2_dev_final_model.joblib")
    v2_model = joblib.load(ROOT / "outputs" / "models" / "repurchase_features_v2.joblib")
    old_scores = old_model.predict_proba(feature_frame[V1_NUMERIC + V1_CATEGORICAL])
    old_scores = old_scores[:, list(old_model.named_steps["model"].classes_).index(1)]
    v2_features = config["classification"]["feature_columns_v2"]
    v2_scores = v2_model.predict_proba(feature_frame[v2_features])
    v2_scores = v2_scores[:, list(v2_model.named_steps["model"].classes_).index(1)]
    segment_bundle = joblib.load(ROOT / config["segmentation"]["model_bundle"])
    dev_features = pd.read_csv(ROOT / "outputs" / "tables" / "day2_features_primary.csv")
    frozen_thresholds = _read_json(ROOT / "outputs" / "metrics" / "frozen_segmenters_dev.json")
    segment_frame = feature_frame[["customer_key", "recency_days", "frequency", "monetary", "max_order_value"]].copy()
    segment_frame["test_window_revenue_vnd"] = 0.0
    segment_frame, segment_profiles, segment_distances = _apply_segments(
        segment_frame, dev_features, segment_bundle, frozen_thresholds["business_rule_thresholds"]
    )
    frozen_combos = pd.read_csv(ROOT / "outputs" / "tables" / "combos_v2.csv")
    if frozen_combos.empty or not {"product_a_key_hmac", "product_b_key_hmac", "support", "lift"}.issubset(frozen_combos.columns):
        raise ValueError("Frozen combo table is empty or missing registered pair fields")
    dev_status_counts = _development_status_counts()

    input_hashes = dict(sidecar["frozen_sources_sha256"])
    open_path = ROOT / "outputs" / "metrics" / "test_opened.lock.json"
    create_test_open_lock(
        open_path,
        split_sha256=sha256(ROOT / "config" / "split.yaml"),
        test_open_config_sha256=sidecar["config_sha256"],
        input_hashes=input_hashes,
    )
    _append_access_event("label_load", config)
    _append_access_event("behavior_load", config)
    test_orders, status_counts = _load_test_window(config)

    label_by_customer: dict[str, int] = defaultdict(int)
    revenue_by_customer: dict[str, Decimal] = defaultdict(Decimal)
    test_customers_seen: set[str] = set()
    for order in test_orders:
        if order["customer_key"]:
            test_customers_seen.add(order["customer_key"])
            if not order["is_gift"]:
                if order["customer_key"] in eligible_keys:
                    label_by_customer[order["customer_key"]] = 1
                revenue_by_customer[order["customer_key"]] += max(order["revenue_recognized"] or Decimal(0), Decimal(0))
    y = np.asarray([label_by_customer.get(key, 0) for key in feature_frame["customer_key"]], dtype=int)
    baseline_score = np.full(len(y), float(registry["repurchase_features_v2"]["positive_rate"]))
    scores = {
        "majority_baseline": baseline_score,
        "amendment_03_logistic_regression": old_scores,
        "repurchase_features_v2_logistic_regression": v2_scores,
    }
    model_metrics = {
        name: {
            **_metric_values(y, score, 0.5),
            "customer_count": int(len(y)),
            "positive_count": int(y.sum()),
            "positive_rate": float(y.mean()) if len(y) else None,
        }
        for name, score in scores.items()
    }
    bootstrap = _bootstrap(y, scores, baseline_score)
    dev_rate = float(registry["repurchase_features_v2"]["positive_rate"])
    test_rate = float(y.mean()) if len(y) else None
    v2_delta_ci = bootstrap["paired_average_precision_delta_vs_baseline_95_ci"]["repurchase_features_v2_logistic_regression"]
    v2_roc_ci = bootstrap["repurchase_features_v2_logistic_regression"]["metrics_95_ci"]["roc_auc"]
    signal = bool(v2_roc_ci and v2_delta_ci and v2_roc_ci["lower"] > 0.55 and v2_delta_ci["lower"] > 0)

    # Frozen segmentation assignment: one feature frame, one frozen bundle, no fitting.
    segment_frame["test_window_revenue_vnd"] = segment_frame["customer_key"].map(lambda key: float(revenue_by_customer.get(key, Decimal(0))))
    for scheme, column in [(f"K={k}", f"k{k}_segment") for k in (2, 3, 4)] + [("Quy tắc nghiệp vụ", "rule_segment")]:
        grouped = segment_frame.groupby(column, sort=True)["test_window_revenue_vnd"].sum()
        total = float(segment_frame["test_window_revenue_vnd"].sum())
        for label, amount in grouped.items():
            segment_profiles.loc[(segment_profiles["scheme"] == scheme) & (segment_profiles["cohort"] == "test_pre_T") & (segment_profiles["segment"] == str(label)), "test_window_recognized_revenue_vnd"] = float(amount)
            segment_profiles.loc[(segment_profiles["scheme"] == scheme) & (segment_profiles["cohort"] == "test_pre_T") & (segment_profiles["segment"] == str(label)), "test_window_revenue_share"] = float(amount / total) if total else 0.0
    _write_rows(ROOT / "outputs" / "tables" / "test_segment_profiles.csv", segment_profiles)

    eligible_baskets: list[set[str]] = []
    test_line_count = 0
    for order in test_orders:
        if order["is_gift"]:
            continue
        test_line_count += len(order["gift_line_records"])
        products = {line["product_key"] for line in order["gift_line_records"] if line.get("product_key") and not line.get("gift_line")}
        if len(products) >= 2:
            eligible_baskets.append(products)
    combo_rows: list[dict[str, Any]] = []
    dev_combo_rows = frozen_combos.to_dict("records")
    for row in dev_combo_rows:
        pair = (str(row["product_a_key_hmac"]), str(row["product_b_key_hmac"]))
        test_metrics = _pair_metrics(eligible_baskets, pair)
        combo_rows.append({
            "combo_name": row["combo_name"],
            "product_a": row["product_a"],
            "product_b": row["product_b"],
            **{f"dev_{k}": row.get(k) for k in ("support", "confidence_a_to_b", "confidence_b_to_a", "lift", "occurrences", "development_eligible_baskets")},
            **test_metrics,
            "delta_support": test_metrics["support"] - float(row["support"]),
            "delta_confidence_a_to_b": test_metrics["confidence_a_to_b"] - float(row["confidence_a_to_b"]),
            "delta_confidence_b_to_a": test_metrics["confidence_b_to_a"] - float(row["confidence_b_to_a"]),
            "delta_lift": test_metrics["lift"] - float(row["lift"]) if test_metrics["lift"] is not None else None,
            "test_lift_gt_1": bool(test_metrics["lift"] is not None and test_metrics["lift"] > 1),
            "interpretation": "đồng xuất hiện; không hàm ý quan hệ nhân quả",
        })
    _write_rows(ROOT / "outputs" / "tables" / "test_combos_frozen.csv", combo_rows)

    dashboard = _dashboard_aggregates(dev_orders, test_orders, status_counts, dev_status_counts)
    metrics: dict[str, Any] = {
        "status": "completed_single_test_open",
        "opened_at_utc": _read_json(open_path)["opened_at_utc"],
        "test_open_count": 1,
        "test_interval": config["test_interval"],
        "effective_post_T_calendar_dates": (end - start).days - 1,
        "split_boundary_note": "Locked end is exclusive; labels include dates > T and < test_end_exclusive; the nominal 180-day interval contributes 179 post-T dates.",
        "cohort": {
            "eligible_customers_with_pre_T_purchase": int(len(eligible_keys)),
            "test_positive_customers": int(y.sum()),
            "test_positive_rate": test_rate,
            "development_positive_rate": dev_rate,
            "test_minus_dev_positive_rate": test_rate - dev_rate if test_rate is not None else None,
            "development_positive_rate_source": "outputs/metrics/dev_final_models_v2.json",
            "test_window_orders_by_status": status_counts,
            "eligible_test_window_orders_status3": int(sum(1 for order in test_orders if not order["is_gift"])),
            "order_gifts_excluded_from_labels": int(sum(1 for order in test_orders if order["is_gift"])),
        },
        "models": model_metrics,
        "development_reference": {
            "positive_rate": dev_rate,
            "amendment_03_logistic_regression": _read_json(ROOT / "outputs" / "metrics" / "dev_final_model.json")["models"]["logistic_regression"]["out_of_fold_metrics"],
            "repurchase_features_v2_logistic_regression": registry["repurchase_features_v2"]["selected_oof_metrics"],
            "repurchase_features_v2_bootstrap_ci": registry["repurchase_features_v2"]["selected_model_bootstrap_ci"],
        },
        "bootstrap_95_ci": bootstrap,
        "preregistered_signal_rule": config["classification"]["signal_rule"],
        "feature_v2_signal_supported": signal,
        "feature_v2_conclusion": "có tín hiệu theo quy tắc ghi trước" if signal else "chưa đủ bằng chứng theo quy tắc ghi trước",
        "segmentation": {
            "assignment": "frozen dev model/thresholds applied to pre-T features; no refit",
            "kmeans_and_rule_comparison": segment_distances,
            "profiles_path": "outputs/tables/test_segment_profiles.csv",
            "test_eligible_customers": int(len(segment_frame)),
            "test_window_recognized_revenue_vnd": float(segment_frame["test_window_revenue_vnd"].sum()),
            "test_labels_loaded": True,
        },
        "association_rules": {
            "frozen_combo_count": int(len(combo_rows)),
            "test_eligible_basket_count": int(len(eligible_baskets)),
            "test_status3_line_count_audited": int(test_line_count),
            "combo_metrics_path": "outputs/tables/test_combos_frozen.csv",
            "test_lift_gt_1_count": int(sum(row["test_lift_gt_1"] for row in combo_rows)),
            "no_new_rules_selected": True,
        },
        "dashboard_tables": dashboard,
        "access_audit": {
            "pre_open_reserved_log_sha256": config["pre_open_evidence"]["reserved_access_log_sha256"],
            "pre_open_reserved_log_entries": config["pre_open_evidence"]["reserved_access_log_entries"],
            "post_open_access_log": "outputs/logs/test_eval_access.jsonl",
            "test_labels_and_behavior_read_after_exclusive_open_lock": True,
            "raw_values_or_customer_identifiers_written": False,
        },
        "limitations": [
            "development contains only one complete Tet cycle; test includes Tet 2026",
            "line-level inferred_subset gift assignments are low confidence and may be wrong",
            "current order status is not a historical status timeline",
            "no unit cost is available, so combo profitability cannot be estimated",
            "association rules describe co-occurrence and not causation",
        ],
    }
    out = ROOT / "outputs" / "metrics" / "test_eval.json"
    out.write_text(json.dumps(metrics, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    return metrics


def main() -> int:
    if (ROOT / "outputs" / "metrics" / "test_opened.lock.json").exists():
        print("Refusing: the one-time test lock already exists. No data was read.")
        return 2
    result = evaluate_once()
    report_path = ROOT / "docs" / "test_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    ci = result["bootstrap_95_ci"]["repurchase_features_v2_logistic_regression"]["metrics_95_ci"]
    delta = result["bootstrap_95_ci"]["paired_average_precision_delta_vs_baseline_95_ci"]["repurchase_features_v2_logistic_regression"]
    report = f'''# Đánh giá test một lần\n\n\
## Phạm vi và kiểm soát\n\n\
Test được mở đúng một lần lúc `{result["opened_at_utc"]}` cho khoảng `[2025-10-22, 2026-04-20)` theo Asia/Ho_Chi_Minh. Kết thúc là mốc loại trừ; vì vậy cửa sổ danh nghĩa 180 ngày có 179 ngày địa phương sau T. Nhãn dương là có ít nhất một đơn status 3, không phải đơn quà cấp đơn, trong phần ngày test quan sát được. Không điều chỉnh mô hình/ngưỡng, không fit lại và không chọn luật mới.\n\n\
Trước mở, log vùng dành riêng có {result["access_audit"]["pre_open_reserved_log_entries"]} bản ghi `eligibility_count`, không có lượt đọc nhãn/hành vi test. Khóa mở test được tạo độc quyền trước khi nạp các trường test; access log sau mở chỉ ghi loại sự kiện, khoảng ngày và thời điểm, không lưu giá trị/định danh.\n\n\
## Mô hình mua lại\n\n\
Nhóm đủ điều kiện: {result["cohort"]["eligible_customers_with_pre_T_purchase"]:,} khách đã mua trước T. Test có {result["cohort"]["test_positive_customers"]:,} khách dương ({result["cohort"]["test_positive_rate"]:.2%}) so với dev {result["cohort"]["development_positive_rate"]:.2%}; chênh lệch {result["cohort"]["test_minus_dev_positive_rate"]:+.2%}. Ngưỡng mọi mô hình cố định ở 0,5.\n\n\
| Mô hình | Precision | Recall | F1 | ROC-AUC (95% CI) | PR-AUC (95% CI) | TN / FP / FN / TP |\n|---|---:|---:|---:|---:|---:|---:|\n{_model_markdown_rows(result)}\n\n\
Feature-v2 có cận ROC-AUC {ci["roc_auc"]["lower"] if ci["roc_auc"] else float("nan"):.3f}–{ci["roc_auc"]["upper"] if ci["roc_auc"] else float("nan"):.3f}; chênh PR-AUC với baseline {delta["lower"]:+.3f}–{delta["upper"]:+.3f}. Cổng ghi trước yêu cầu cận dưới ROC-AUC > 0,55 và cận dưới chênh PR-AUC > 0. Kết luận: **{result["feature_v2_conclusion"]}**.\n\n\
Khoảng tin cậy percentile bootstrap 95% theo khách, 2.000 lượt, seed 20261026; chênh PR-AUC bootstrap ghép cặp. Dev OOF feature-v2: ROC-AUC {result["development_reference"]["repurchase_features_v2_logistic_regression"]["roc_auc"]:.3f}, PR-AUC {result["development_reference"]["repurchase_features_v2_logistic_regression"]["pr_auc"]:.3f}; CI dev được ghi trong `outputs/metrics/dev_final_models_v2.json`.\n\n\
## Phân khúc\n\n\
Gán K-Means K=2/3/4 và phân khúc quy tắc bằng scaler, mô hình và ngưỡng đã đóng băng trên dev. Không fit lại. Quy mô, tỷ trọng doanh thu ghi nhận và R/F/M nằm trong `outputs/tables/test_segment_profiles.csv`. Độ lệch phân phối chỉ mô tả bằng khoảng cách TV của tỷ trọng nhóm và Wasserstein-1 chuẩn hóa theo IQR dev: `{json.dumps(result["segmentation"]["kmeans_and_rule_comparison"], ensure_ascii=False)}`. Nhóm “khách doanh nghiệp” chỉ là proxy giá trị lớn/tần suất thấp, không phải xác minh danh tính doanh nghiệp.\n\n\
## Luật kết hợp\n\n\
Đã chấm đúng {result["association_rules"]["frozen_combo_count"]} cặp đóng băng trên {result["association_rules"]["test_eligible_basket_count"]:,} giỏ test đủ điều kiện sau khi loại dòng quà. Có {result["association_rules"]["test_lift_gt_1_count"]} cặp có lift > 1 trong test. Bảng đầy đủ support, confidence hai hướng, lift và delta dev-test: `outputs/tables/test_combos_frozen.csv`. Luật chỉ biểu thị đồng xuất hiện, không phải quan hệ nhân quả; không chọn luật mới.\n\n\
## Diễn giải và hạn chế\n\n\
Nếu test khác dev rõ, đây là dấu hiệu tính không dừng có thể liên quan cửa sổ test và Tết 2026; không dùng kết quả để điều chỉnh mô hình. Tập dev có một mùa Tết trọn vẹn. Suy luận tập con gán quà có thể sai; dữ liệu hiện trạng không lưu lịch sử thay đổi trạng thái; chưa có giá vốn nên không đánh giá được hiệu quả kinh tế combo.\n'''
    report_path.write_text(report, encoding="utf-8")
    print(f"Single test evaluation complete: eligible={result['cohort']['eligible_customers_with_pre_T_purchase']}; positive={result['cohort']['test_positive_customers']}; feature-v2={result['feature_v2_conclusion']}.")
    print(f"Metrics: outputs/metrics/test_eval.json; report: docs/test_report.md; one-time lock is present.")
    return 0


def _model_markdown_rows(result: dict[str, Any]) -> str:
    labels = {
        "majority_baseline": "Baseline majority",
        "amendment_03_logistic_regression": "Logistic Regression C=10 (đóng băng)",
        "repurchase_features_v2_logistic_regression": "Logistic Regression v2 C=0,1 (đóng băng)",
    }
    lines = []
    bootstrap = result["bootstrap_95_ci"]
    for name, metrics in result["models"].items():
        ci = bootstrap[name]["metrics_95_ci"]
        def fmt(metric: str, digits: int = 3) -> str:
            value = metrics.get(metric)
            return "NA" if value is None else f"{value:.{digits}f}"
        def fmt_ci(metric: str) -> str:
            value = ci.get(metric)
            return "NA" if value is None else f"{value['lower']:.3f}–{value['upper']:.3f}"
        tn, fp = metrics["confusion_matrix_tn_fp_fn_tp"][0]
        fn, tp = metrics["confusion_matrix_tn_fp_fn_tp"][1]
        lines.append(f"| {labels[name]} | {fmt('precision')} | {fmt('recall')} | {fmt('f1')} | {fmt_ci('roc_auc')} | {fmt_ci('average_precision')} | {tn} / {fp} / {fn} / {tp} |")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
