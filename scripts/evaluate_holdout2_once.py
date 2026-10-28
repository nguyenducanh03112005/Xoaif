"""Single-open evaluator for 06-HO2. Never reads outcomes on import or by default."""

from __future__ import annotations

from datetime import date, datetime, timezone
import getpass
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import brier_score_loss
from collections import Counter
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from features.day2_data import LABEL_T_CANDIDATES, load_dev_orders  # noqa: E402
from features.holdout2_access import load_authorized_holdout_orders  # noqa: E402
from features.holdout2_features import (attach_holdout2_labels, build_customer_features_at_t,
                                        outcome_eligible)  # noqa: E402
from features.holdout2_metrics import (holm_step_down,
                                       precision_at_k_tie_aware, risk_ratio, roc_auc)  # noqa: E402
from features.repurchase_v3 import build_multisnapshot_samples  # noqa: E402
from models.classify import NUMERIC_COLUMNS as D005_NUMERIC, CATEGORICAL_COLUMNS as D005_CATEGORICAL  # noqa: E402
from models.repurchase_v3 import MODEL_FEATURES  # noqa: E402
from analyze_customer_value_dev import rfm_action_group  # noqa: E402
from evaluate_repurchase_wp5c_dev import _bins, _score_validation  # noqa: E402

REQUIRED_PHRASE = "DUYỆT MỞ HO2"
SEED = 20261028
BOOTSTRAP_DRAWS = 2000


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _config(root: Path = ROOT) -> dict:
    return yaml.safe_load((root / "config/amendment_06_ho2.yaml").read_bytes())


def validate_dry_run_t(value: str, config: dict, dev_end: date = date(2025, 10, 22)) -> date:
    t = date.fromisoformat(value)
    horizon = int(config["label_window"]["horizon_days"])
    t2 = date.fromisoformat(str(config["T2"]))
    if t >= t2:
        raise ValueError("dry-run T2 or later is forbidden")
    if t >= dev_end or t + pd.Timedelta(days=horizon) > dev_end:
        raise ValueError("dry-run T and full label horizon must be inside DEV")
    return t


def _verify_gateb_lock(root: Path = ROOT) -> dict:
    lock_path = root / "config/amendment_06_ho2.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    config = _config(root)
    if lock.get("amendment_id") != "06-HO2" or lock.get("revision") != 2:
        raise RuntimeError("Gate B revision 2 lock is required")
    if lock.get("status") != "prepared_gate_b_not_open" or lock.get("test_opened") is not False:
        raise RuntimeError("Gate B lock must remain closed before opening")
    for rel, expected in lock.get("frozen_source_sha256", {}).items():
        path = root / rel
        if not path.is_file() or _sha(path) != expected:
            raise RuntimeError(f"Gate B frozen hash mismatch: {rel}")
    if config.get("status") != "prepared_gate_b_not_open" or config.get("test_opened") is not False:
        raise RuntimeError("Amendment config is not in closed state")
    return lock


def create_open_lock(root: Path, authorization: str) -> dict:
    if authorization != REQUIRED_PHRASE:
        raise PermissionError("owner authorization phrase did not match")
    _verify_gateb_lock(root)
    lock_path = root / "outputs/metrics/holdout2_opened.lock.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    protected_outputs = (lock_path, root / "outputs/metrics/holdout2_eval.json",
                         root / "docs/holdout2_report.md", root / "outputs/logs/holdout2_access.jsonl")
    if any(path.exists() for path in protected_outputs):
        raise FileExistsError("HO2 open lock already exists; retry is forbidden")
    config_path = root / "config/amendment_06_ho2.yaml"
    protocol_path = root / "docs/analysis_plan_amendment06_ho2.md"
    payload = {
        "amendment_id": "06-HO2", "revision": 2, "status": "opened_once", "test_open_count": 1,
        "opened_at_utc": datetime.now(timezone.utc).isoformat(), "t2": str(_config(root)["T2"]),
        "config_sha256": _sha(config_path), "protocol_sha256": _sha(protocol_path),
        "evaluator_sha256": _sha(root / "scripts/evaluate_holdout2_once.py"),
    }
    with lock_path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
        handle.flush()
    log = root / "outputs/logs/holdout2_access.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"event": "authorized_single_open", "opened_at_utc": payload["opened_at_utc"],
                                "amendment_id": "06-HO2", "count": 1}) + "\n")
    return payload


def _positive_probability(model, frame: pd.DataFrame, columns: list[str]) -> np.ndarray:
    scores = model.predict_proba(frame[columns])
    estimator = model.named_steps.get("model", model.named_steps.get("classifier")) if hasattr(model, "named_steps") else model
    classes = list(estimator.classes_)
    return scores[:, classes.index(1)]


def _metric_record(y: np.ndarray, score: np.ndarray) -> dict:
    top = precision_at_k_tie_aware(y, score, .10)
    return {"roc_auc": roc_auc(y, score), "precision_at_10_tie_aware": top["precision"],
            "lift_top_decile_tie_aware": top["lift"], "k_top_decile": top["k"],
            "prevalence": float(np.mean(y)), "mean_score": float(np.mean(score)),
            "brier_descriptive": float(brier_score_loss(y, score))}


def _bootstrap_values(frame: pd.DataFrame, score_col: str, metric: str) -> np.ndarray:
    ids = frame.customer_key.drop_duplicates().to_numpy()
    groups = [frame.index[frame.customer_key == key].to_numpy() for key in ids]
    rng = np.random.default_rng(SEED)
    out = []
    for _ in range(BOOTSTRAP_DRAWS):
        picked = rng.integers(0, len(ids), size=len(ids))
        sample = frame.loc[np.concatenate([groups[i] for i in picked])]
        y, s = sample.label_returned.to_numpy(dtype=int), sample[score_col].to_numpy(dtype=float)
        if metric == "roc_auc":
            value = roc_auc(y, s)
        else:
            result = precision_at_k_tie_aware(y, s, .10)
            value = result["precision"] if metric == "precision_at_10_tie_aware" else result["lift"]
        if value is not None and np.isfinite(value):
            out.append(float(value))
    return np.asarray(out)


def _ci(values: np.ndarray) -> dict:
    return {"lower_95": float(np.quantile(values, .025)) if len(values) else None,
            "upper_95": float(np.quantile(values, .975)) if len(values) else None,
            "lower_one_sided_95": float(np.quantile(values, .05)) if len(values) else None,
            "valid_draws": int(len(values)), "requested_draws": BOOTSTRAP_DRAWS, "seed": SEED}


def _centered_bootstrap_p(values: np.ndarray, observed: float, threshold: float, *, log_scale: bool = False) -> float | None:
    if not len(values) or not np.isfinite(observed):
        return None
    cutoff = observed * observed / threshold if log_scale else 2 * observed - threshold
    return float((np.sum(values >= cutoff) + 1) / (len(values) + 1))


def _h5_eval(orders: list[dict], t2: date, root: Path) -> dict:
    screen = pd.read_csv(root / "outputs/tables/combo_recommendation_screen_f3.csv",
                         usecols=["combo_name", "dev_lift", "dev_kulczynski", "dev_imbalance_ratio"])
    passed_dev = screen[(screen.dev_lift > 1) & (screen.dev_kulczynski >= .5)
                        & (screen.dev_imbalance_ratio <= .5)]
    frozen = pd.read_csv(root / "outputs/tables/combos_v2.csv",
                         usecols=["combo_name", "product_a_key_hmac", "product_b_key_hmac"])
    chosen = passed_dev.merge(frozen, on="combo_name", validate="one_to_one")
    eligible = [o for o in orders if outcome_eligible(o["date"], t2, 180) and o.get("status", 3) == 3
                and not o.get("is_gift") and len(set(o.get("basket_product_keys", o.get("product_keys", [])))) >= 2]
    denominator = len(eligible)
    item_counts = Counter(key for order in eligible for key in set(order.get("basket_product_keys", order.get("product_keys", []))))
    pair_counts = []
    passed_count = 0
    suppressed = False
    for row in chosen.to_dict("records"):
        a, b = str(row["product_a_key_hmac"]), str(row["product_b_key_hmac"])
        pair_n = sum(a in order.get("basket_product_keys", order.get("product_keys", []))
                     and b in order.get("basket_product_keys", order.get("product_keys", [])) for order in eligible)
        if pair_n < 30:
            suppressed = True
            continue
        sa = item_counts[a] / denominator if denominator else 0
        sb = item_counts[b] / denominator if denominator else 0
        sp = pair_n / denominator if denominator else 0
        lift = sp / (sa * sb) if sa and sb else 0
        kulc = (pair_n / item_counts[a] + pair_n / item_counts[b]) / 2 if item_counts[a] and item_counts[b] else 0
        ir = abs(sa - sb) / (sa + sb - sp) if sa + sb - sp else 0
        if lift > 1 and kulc >= .5 and ir <= .5:
            passed_count += 1
        pair_counts.append({"pass": bool(lift > 1 and kulc >= .5 and ir <= .5)})
    k_dev = int(json.loads((root / "outputs/metrics/gateb_r4_dev_calibration.json").read_text(encoding="utf-8"))["h5"]["k_dev"])
    descriptive = k_dev < 4
    threshold = math.ceil(k_dev / 2) if not descriptive else None
    return {"eligible_baskets": denominator, "k_dev": k_dev, "h5_descriptive_only": descriptive,
            "required_pass_count_if_testable": threshold,
            "observed_pass_count": passed_count if not suppressed else None,
            "suppressed_pair_present": suppressed,
            "pass": bool(passed_count >= threshold) if threshold is not None and not suppressed else None,
            "basket_rule": "HO2 date>T2 and <=T2+180; status 3, not order-gift, >=2 distinct product IDs; gift lines excluded by registered prelock order-level rule"}


def _paired_auc_difference(frame: pd.DataFrame, predictions: pd.DataFrame, other: str) -> dict:
    ids = frame.customer_key.drop_duplicates().to_numpy()
    groups = [frame.index[frame.customer_key == key].to_numpy() for key in ids]
    rng = np.random.default_rng(SEED)
    diffs = []
    for _ in range(BOOTSTRAP_DRAWS):
        picked = rng.integers(0, len(ids), size=len(ids))
        idx = np.concatenate([groups[i] for i in picked])
        y = frame.loc[idx, "label_returned"].to_numpy(dtype=int)
        if len(np.unique(y)) < 2:
            continue
        d005_score = predictions.loc[idx, "D-005"].to_numpy(dtype=float)
        other_score = predictions.loc[idx, other].to_numpy(dtype=float)
        diffs.append(roc_auc(y, d005_score) - roc_auc(y, other_score))
    return _ci(np.asarray(diffs))


def _bootstrap_rr_values(frame: pd.DataFrame) -> np.ndarray:
    ids = frame.customer_key.drop_duplicates().to_numpy()
    groups = [frame.index[frame.customer_key == key].to_numpy() for key in ids]
    rng = np.random.default_rng(SEED)
    out = []
    for _ in range(BOOTSTRAP_DRAWS):
        picked = rng.integers(0, len(ids), size=len(ids))
        sample = frame.loc[np.concatenate([groups[i] for i in picked])]
        value = risk_ratio(sample.label_returned, sample.repeat)["rr"]
        if value is not None and np.isfinite(value):
            out.append(float(value))
    return np.asarray(out)


def _score_strategies(frame: pd.DataFrame, root: Path) -> tuple[pd.DataFrame, dict]:
    frozen = json.loads((root / "outputs/metrics/gateb_r5_strategy_freeze.json").read_text(encoding="utf-8"))
    strategies = frozen["strategy_population_and_fit"]
    for name in ("S3", "S6", "D-005", "v2", "v3"):
        info = strategies[name]
        artifact_path = root / info.get("artifact", info.get("path", ""))
        if not artifact_path.is_file() or _sha(artifact_path) != info["sha256"]:
            raise RuntimeError(f"frozen DEV strategy artifact hash mismatch: {name}")
    predictions = pd.DataFrame({"customer_key": frame.customer_key, "label_returned": frame.label_returned})
    predictions["S1"] = (frame.frequency >= 2).astype(float).to_numpy()
    d005 = __import__("joblib").load(root / strategies["D-005"]["path"])
    v2 = __import__("joblib").load(root / strategies["v2"]["path"])
    s3 = __import__("joblib").load(root / strategies["S3"]["path"])
    v3 = __import__("joblib").load(root / strategies["v3"]["path"])
    predictions["D-005"] = _positive_probability(d005, frame, D005_NUMERIC + D005_CATEGORICAL)
    v2_columns = json.loads((root / "outputs/metrics/dev_final_models_v2.json").read_text(encoding="utf-8"))["repurchase_features_v2"]["feature_columns"]
    predictions["v2"] = _positive_probability(v2, frame, v2_columns)
    predictions["S3"] = _positive_probability(s3, frame, MODEL_FEATURES)
    predictions["v3"] = _positive_probability(v3, frame, MODEL_FEATURES)
    for name in ("recency_only", "frequency_only"):
        item = strategies[name]
        standardized = ((pd.to_numeric(frame[item["feature"]]).to_numpy() - float(item["standardizer_mean"]))
                        / float(item["standardizer_scale"]))
        predictions[name] = standardized * int(item["direction"])
    s6_payload = json.loads((root / strategies["S6"]["artifact"]).read_text(encoding="utf-8"))
    s6 = _score_validation(frame, s6_payload["mapping"], s6_payload["audit"], float(frame.label_returned.mean()))
    predictions["S6"] = s6
    return predictions, frozen


def _dev_h4_rates(root: Path) -> tuple[dict, dict]:
    orders, scope, _ = load_dev_orders()
    if scope.get("test_labels_loaded") or scope.get("test_behavior_loaded"):
        raise RuntimeError("DEV loader reported test access during H4 reference build")
    dev = build_multisnapshot_samples(orders, test_start=date(2025, 10, 22), candidates=LABEL_T_CANDIDATES)
    s6_groups = _bins(dev)
    s6_groups["group"] = s6_groups.freq_bin.astype(str) + "|" + s6_groups.recency_bin.astype(str)
    s6_rates = {k: float(g.label_returned.mean()) for k, g in s6_groups.groupby("group") if len(g) >= 30}
    rfm = dev.apply(lambda r: rfm_action_group(r.recency_days, r.frequency, r.monetary, 830000), axis=1)
    rfm_rates = {str(k): float(g.label_returned.mean()) for k, g in dev.assign(group=rfm).groupby("group") if len(g) >= 30}
    return s6_rates, rfm_rates


def _h4_eval(frame: pd.DataFrame, dev_s6: dict, dev_rfm: dict, r4: dict) -> dict:
    cfg = r4["dev_half_reference"]
    thresholds = {"S6": cfg["s6"]["rho"], "RFM": cfg["rfm"]["rho"]}
    out = {}
    for name, dev_rates, groups in (
        ("S6", dev_s6, _bins(frame).assign(group=lambda d: d.freq_bin.astype(str) + "|" + d.recency_bin.astype(str))),
        ("RFM", dev_rfm, frame.assign(group=frame.apply(lambda r: rfm_action_group(r.recency_days, r.frequency, r.monetary, 830000), axis=1))),
    ):
        ho_rates = {str(k): float(g.label_returned.mean()) for k, g in groups.groupby("group") if len(g) >= 30}
        common = sorted(set(dev_rates) & set(ho_rates))
        rho = float(spearmanr([dev_rates[k] for k in common], [ho_rates[k] for k in common]).statistic) if len(common) >= 4 else None
        testable = len(common) >= 4 and thresholds[name] is not None and thresholds[name] >= .50
        out[name] = {"testable": testable, "groups_n_ge_30": len(ho_rates), "common_groups_n": len(common),
                     "rho_ho2_vs_dev": rho, "rho_dev_half_threshold": thresholds[name],
                     "pass": bool(testable and rho is not None and rho >= thresholds[name])}
    out["overall_testable"] = all(out[k]["testable"] for k in ("S6", "RFM"))
    out["overall_pass"] = bool(out["overall_testable"] and all(out[k]["pass"] for k in ("S6", "RFM")))
    return out


def evaluate_frame(frame: pd.DataFrame, root: Path = ROOT, orders: list[dict] | None = None) -> dict:
    y = frame.label_returned.astype(int).to_numpy()
    predictions, frozen = _score_strategies(frame, root)
    strategy_rows = {}
    wide = predictions.copy()
    for name in [c for c in predictions.columns if c not in {"customer_key", "label_returned"}]:
        score = predictions[name].to_numpy(dtype=float)
        row = _metric_record(y, score)
        metric_frame = predictions[["customer_key", "label_returned"]].copy()
        metric_frame["_score"] = score
        row["ci_95"] = {metric: _ci(_bootstrap_values(metric_frame, "_score", metric))
                        for metric in ("roc_auc", "precision_at_10_tie_aware", "lift_top_decile_tie_aware")}
        strategy_rows[name] = row
    h2 = risk_ratio(y, frame.frequency.to_numpy() >= 2)
    h2_frame = pd.DataFrame({"customer_key": frame.customer_key.astype(str),
                             "label_returned": y,
                             "repeat": (frame.frequency.to_numpy() >= 2).astype(int)})
    h2_values = _bootstrap_rr_values(h2_frame)
    h2_ci = _ci(h2_values)
    h2_p = _centered_bootstrap_p(h2_values, h2["rr"], 1.5, log_scale=True) if h2["rr"] is not None else 1.0
    h1_values = _bootstrap_values(predictions.assign(_score=predictions["D-005"]), "_score", "roc_auc")
    auc = strategy_rows["D-005"]["roc_auc"]
    h1_p = None
    if auc is not None and len(h1_values):
        h1_p = _centered_bootstrap_p(h1_values, auc, .55)
    p_adj = holm_step_down({"H1": h1_p if h1_p is not None else 1.0, "H2": h2_p})
    h3 = {name: {"precision_ci_lower_95": row["ci_95"]["precision_at_10_tie_aware"]["lower_95"],
                 "lift_ci_lower_95": row["ci_95"]["lift_top_decile_tie_aware"]["lower_95"],
                 "supported": bool(row["ci_95"]["precision_at_10_tie_aware"]["lower_95"] is not None
                                    and row["ci_95"]["precision_at_10_tie_aware"]["lower_95"] > row["prevalence"]
                                    and row["ci_95"]["lift_top_decile_tie_aware"]["lower_95"] > 1)}
           for name, row in strategy_rows.items() if name in {"S1", "S3", "S6"}}
    r4 = json.loads((root / "outputs/metrics/gateb_r4_dev_calibration.json").read_text(encoding="utf-8"))
    dev_s6, dev_rfm = _dev_h4_rates(root)
    h4 = _h4_eval(frame, dev_s6, dev_rfm, r4)
    h5 = (_h5_eval(orders, date.fromisoformat(str(_config(root)["T2"])), root)
          if orders is not None else {"status": "not_run_without_authorized_orders"})
    result = {
        "status": "completed_single_open", "cohort": "06-HO2 T2=2026-04-20, labels through 2026-10-17 inclusive",
        "n_customers": int(len(frame)), "positive_customers": int(y.sum()),
        "prevalence_descriptive": float(y.mean()), "strategies": strategy_rows,
        "H1": {"threshold": 0.55, "p_raw": h1_p, "p_holm": p_adj["H1"],
               "one_sided_lower_95": strategy_rows["D-005"]["ci_95"]["roc_auc"]["lower_one_sided_95"],
               "passes_holm_and_effect_threshold": bool(p_adj["H1"] < .05 and
                                                        strategy_rows["D-005"]["ci_95"]["roc_auc"]["lower_one_sided_95"] > .55),
               "auc_minus_0_70_descriptive": (auc - .70) if auc is not None else None,
               "auc_minus_0_70_ci_95": {k: (v - .70 if v is not None else None)
                                          for k, v in strategy_rows["D-005"]["ci_95"]["roc_auc"].items()
                                          if k in {"lower_95", "upper_95", "lower_one_sided_95"}}},
        "H2": {**h2, "threshold": 1.5, "p_raw": h2_p, "p_holm": p_adj["H2"],
               "passes_holm_and_effect_threshold": bool(h2.get("rr") is not None and h2["rr"] > 1.5 and p_adj["H2"] < .05)},
        "H2_ci_95": h2_ci,
        "primary_holm": {"raw_p": {"H1": h1_p, "H2": h2_p}, "adjusted_p": p_adj,
                         "order": sorted(p_adj, key=p_adj.get), "alpha_step_down": [0.025, 0.05]},
        "H3_secondary_six_comparisons_no_adjustment": h3,
        "H4_secondary": h4,
        "H5": h5,
        "D005_vs_univariate_baselines_auc_difference": {
            "D-005_minus_recency_only": _paired_auc_difference(frame, predictions, "recency_only"),
            "D-005_minus_frequency_only": _paired_auc_difference(frame, predictions, "frequency_only"),
        },
        "H6_status": "not_testable",
        "test_opened": True, "old_test_labels_used_for_fit_or_selection": False,
        "seed": SEED, "bootstrap_draws": BOOTSTRAP_DRAWS,
        "limitations": ["one store and one retrospective snapshot window", "observational, not causal",
                        "customer-cluster bootstrap is uncertainty, not representativeness guarantee"],
    }
    return result


def _dry_run(value: str, root: Path = ROOT) -> dict:
    config = _config(root)
    t = validate_dry_run_t(value, config)
    orders, scope, _ = load_dev_orders()
    if scope.get("test_labels_loaded") or scope.get("test_behavior_loaded"):
        raise RuntimeError("DEV-only loader reported test access")
    frame = build_customer_features_at_t(orders, t, analysis_start=date(2024, 4, 1))
    labeled = attach_holdout2_labels(frame, orders, t, int(config["label_window"]["horizon_days"]))
    if not len(labeled) or not (pd.to_datetime(labeled.latest_feature_date).dt.date < t).all():
        raise RuntimeError("dry-run feature boundary check failed")
    report = {"code_run": True, "mode": "dry_run_dev_only",
              "label": "kiểm thử mã, không phải kết quả, không dùng để chọn hay tinh chỉnh",
              "T": t.isoformat(), "feature_rows": int(len(labeled)),
              "feature_dates_strictly_before_T": True,
              "label_horizon_end": (t + pd.Timedelta(days=int(config["label_window"]["horizon_days"]))).isoformat(),
              "scope": scope.get("scope", "DEV-only")}
    path = root / "outputs/dryrun/holdout2_code_dryrun.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def _open_and_evaluate(root: Path, authorization: str) -> dict:
    create_open_lock(root, authorization)
    orders, audit = load_authorized_holdout_orders(root)
    cfg = _config(root)
    t2 = date.fromisoformat(str(cfg["T2"]))
    features = build_customer_features_at_t(orders, t2, analysis_start=date(2024, 4, 1))
    frame = attach_holdout2_labels(features, orders, t2, int(cfg["label_window"]["horizon_days"]))
    result = evaluate_frame(frame, root, orders=orders)
    result["access_audit"] = audit
    metrics_path = root / "outputs/metrics/holdout2_eval.json"
    metrics_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path = root / "docs/holdout2_report.md"
    report_path.write_text("# Kết quả HO2\n\n" + json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run-T")
    parser.add_argument("--open", action="store_true", help="single-open; requires exact owner phrase")
    args = parser.parse_args(argv)
    if args.dry_run_T:
        print(json.dumps(_dry_run(args.dry_run_T), ensure_ascii=False, indent=2))
        return 0
    if args.open:
        phrase = getpass.getpass("Owner authorization: ")
        print(json.dumps(_open_and_evaluate(ROOT, phrase), ensure_ascii=False, indent=2))
        return 0
    print("HO2 remains closed. Use --dry-run-T inside DEV, or --open after owner authorization.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
