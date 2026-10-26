"""Serialize development-fitted segmenters for the one-time test assignment."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
SEED = 42


def _matrix(frame: pd.DataFrame) -> np.ndarray:
    return np.column_stack([
        frame["recency_days"].astype(float).to_numpy(),
        np.log1p(frame["frequency"].astype(float).to_numpy()),
        np.log1p(frame["monetary"].clip(lower=0).astype(float).to_numpy()),
    ])


def _align_labels(reference: np.ndarray, candidate: np.ndarray, k: int) -> tuple[dict[int, int], float]:
    confusion = np.zeros((k, k), dtype=int)
    for ref, fitted in zip(reference, candidate):
        confusion[int(fitted), int(ref)] += 1
    rows, cols = linear_sum_assignment(confusion.max() - confusion)
    mapping = {int(row): int(col) for row, col in zip(rows, cols)}
    agreement = float(adjusted_rand_score(reference, candidate))
    return mapping, agreement


def freeze_dev_segmenters() -> dict[str, Any]:
    tables = ROOT / "outputs" / "tables"
    metrics_dir = ROOT / "outputs" / "metrics"
    models_dir = ROOT / "outputs" / "models"
    primary = pd.read_csv(tables / "day2_features_primary.csv")
    frozen_k2 = pd.read_csv(tables / "segments.csv")
    segments_v2 = pd.read_csv(tables / "segments_v2.csv")
    if primary.empty or primary["customer_key"].duplicated().any():
        raise ValueError("development segmentation frame is empty or has duplicate customers")
    reference_labels = {
        2: frozen_k2.set_index("customer_key").loc[primary["customer_key"], "cluster_id"].astype(int).to_numpy(),
        3: segments_v2.set_index("customer_key").loc[primary["customer_key"], "cluster_id_k3"].astype(int).to_numpy(),
        4: segments_v2.set_index("customer_key").loc[primary["customer_key"], "cluster_id_k4"].astype(int).to_numpy(),
    }
    recipes = {2: {"n_init": 20, "max_iter": 500}, 3: {"n_init": 10, "max_iter": 500}, 4: {"n_init": 10, "max_iter": 500}}
    models: dict[int, dict[str, Any]] = {}
    agreement: dict[str, dict[str, Any]] = {}
    raw = _matrix(primary)
    for k in (2, 3, 4):
        scaler = StandardScaler()
        scaled = scaler.fit_transform(raw)
        estimator = KMeans(n_clusters=k, random_state=SEED, n_init=recipes[k]["n_init"], max_iter=recipes[k]["max_iter"])
        fitted = estimator.fit_predict(scaled)
        label_mapping, ari = _align_labels(reference_labels[k], fitted, k)
        exact_share = float(np.mean(np.asarray([label_mapping[int(value)] for value in fitted]) == reference_labels[k]))
        if ari < 0.999999 or exact_share < 0.999999:
            raise ValueError(f"development-frozen K={k} predictions do not reproduce registered development assignments")
        models[k] = {"scaler": scaler, "estimator": estimator, "label_mapping": label_mapping, "recipe": recipes[k]}
        agreement[str(k)] = {"development_ari": ari, "aligned_assignment_agreement": exact_share, "seed": SEED}
    bundle = {"feature_order": ["recency_days", "log1p(frequency)", "log1p(max(monetary,0))"], "models": models}
    model_path = models_dir / "segmenters_dev_frozen_v1.joblib"
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, model_path)
    digest = hashlib.sha256(model_path.read_bytes()).hexdigest()
    active_registry = json.loads((ROOT / "outputs" / "metrics" / "day2b_segmentation.json").read_text(encoding="utf-8"))
    business_rule = active_registry["rule_based_quantile_thresholds"]
    proxy_thresholds = active_registry["business_like_proxy_thresholds"]
    result = {
        "status": "development_fitted_and_frozen_before_test",
        "model_path": "outputs/models/segmenters_dev_frozen_v1.joblib",
        "model_sha256": digest,
        "seed": SEED,
        "kmeans_recipe": recipes,
        "development_assignment_reproduction": agreement,
        "business_rule_thresholds": business_rule,
        "business_like_proxy_thresholds": proxy_thresholds,
        "no_test_features_or_labels_used": True,
        "test_labels_loaded": False,
        "test_behavior_loaded": False,
    }
    (metrics_dir / "frozen_segmenters_dev.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(freeze_dev_segmenters(), indent=2, ensure_ascii=False))
