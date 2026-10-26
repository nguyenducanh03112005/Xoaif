"""Development-only RFM segmentation with seeded stability and money sensitivities."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
SEEDS = (13, 42, 87, 2025, 7)


def _matrix(frame: pd.DataFrame) -> np.ndarray:
    return np.column_stack([
        frame["recency_days"].astype(float).to_numpy(),
        np.log1p(frame["frequency"].astype(float).to_numpy()),
        np.log1p(frame["monetary"].clip(lower=0).astype(float).to_numpy()),
    ])


def _cluster(frame: pd.DataFrame, k: int, seed: int = 42) -> tuple[np.ndarray, np.ndarray, float]:
    raw = _matrix(frame)
    scaler = StandardScaler()
    scaled = scaler.fit_transform(raw)
    model = KMeans(n_clusters=k, random_state=seed, n_init=20, max_iter=500)
    labels = model.fit_predict(scaled)
    sample_size = min(1200, len(frame))
    score = float(silhouette_score(scaled, labels, sample_size=sample_size, random_state=seed)) if len(set(labels)) > 1 else -1.0
    return labels, scaled, score


def _aligned_change_rate(reference: np.ndarray, candidate: np.ndarray, k: int) -> float:
    confusion = np.zeros((k, k), dtype=int)
    for a, b in zip(reference, candidate):
        confusion[int(a), int(b)] += 1
    row_ind, col_ind = linear_sum_assignment(confusion.max() - confusion)
    matched = int(confusion[row_ind, col_ind].sum())
    return 1.0 - matched / len(reference) if len(reference) else 0.0


def _rule_segment(row: pd.Series, monetary_p99: float, order_p99: float) -> str:
    if int(row["frequency"]) <= 1:
        return "Khách mua một lần"
    if int(row["frequency"]) <= 2 and (row["monetary"] >= monetary_p99 or row["max_order_value"] >= order_p99):
        return "Giá trị lớn, tần suất thấp"
    return "Khách mua lặp lại"


def run_segmentation() -> dict[str, Any]:
    tables = ROOT / "outputs" / "tables"
    figures = ROOT / "outputs" / "figures"
    metrics_dir = ROOT / "outputs" / "metrics"
    figures.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    frames = {name: pd.read_csv(tables / f"day2_features_{name}.csv") for name in ("primary", "A", "B")}
    primary = frames["primary"].copy()
    if primary.empty or primary["customer_key"].duplicated().any():
        raise ValueError("segmentation input is empty or repeats a customer key")
    rfm = primary[["recency_days", "frequency", "monetary"]].copy()
    single_rate = float((rfm["frequency"] == 1).mean())
    ks = list(range(2, 9))
    elbow = []
    silhouettes = []
    stability = []
    raw = _matrix(rfm)
    scaled = StandardScaler().fit_transform(raw)
    for k in ks:
        inertias = []
        scores = []
        runs = []
        for seed in SEEDS:
            model = KMeans(n_clusters=k, random_state=seed, n_init=10, max_iter=500)
            labels = model.fit_predict(scaled)
            inertias.append(float(model.inertia_))
            if len(set(labels)) > 1:
                scores.append(float(silhouette_score(scaled, labels, sample_size=min(1200, len(primary)), random_state=seed)))
            runs.append(labels)
        elbow.append(float(np.mean(inertias)))
        silhouettes.append(float(np.mean(scores)) if scores else -1.0)
        pair_scores = [adjusted_rand_score(runs[i], runs[j]) for i in range(len(runs)) for j in range(i + 1, len(runs))]
        stability.append(float(np.mean(pair_scores)) if pair_scores else 1.0)
    chosen_k = ks[int(np.argmax(silhouettes))]
    primary_labels, primary_scaled, chosen_silhouette = _cluster(primary, chosen_k, seed=42)
    primary["cluster_id"] = primary_labels.astype(int)
    monetary_p99 = float(primary["monetary"].quantile(0.99))
    order_p99 = float(primary["max_order_value"].quantile(0.99))
    primary["rule_segment"] = primary.apply(lambda row: _rule_segment(row, monetary_p99, order_p99), axis=1)
    primary["business_like_proxy"] = (primary["monetary"].ge(monetary_p99) | primary["max_order_value"].ge(order_p99)).astype(int)
    total_monetary = float(primary["monetary"].sum())
    profiles = primary.groupby("cluster_id").agg(
        customers=("customer_key", "count"),
        mean_recency_days=("recency_days", "mean"),
        median_recency_days=("recency_days", "median"),
        mean_frequency=("frequency", "mean"),
        median_frequency=("frequency", "median"),
        mean_monetary=("monetary", "mean"),
        median_monetary=("monetary", "median"),
        mean_order_value=("average_order_value", "mean"),
        mean_distinct_products=("distinct_products", "mean"),
        business_like_customers=("business_like_proxy", "sum"),
        cluster_monetary=("monetary", "sum"),
    ).reset_index()
    overall_p75_money = float(primary["monetary"].quantile(.75))
    names = {}
    for profile in profiles.to_dict("records"):
        if profile["median_frequency"] <= 1:
            name = "Chủ yếu mua một lần"
        elif profile["mean_monetary"] >= overall_p75_money and profile["mean_frequency"] <= float(primary["frequency"].median()) + 1:
            name = "Giá trị cao, tần suất thấp"
        else:
            name = "Khách mua lặp lại"
        names[int(profile["cluster_id"])] = name
    primary["cluster_name"] = primary["cluster_id"].map(names)
    profiles["cluster_name"] = profiles["cluster_id"].map(names)
    profiles["revenue_share"] = profiles["cluster_monetary"] / total_monetary if total_monetary else 0.0
    profiles.to_csv(tables / "segment_profiles.csv", index=False, encoding="utf-8-sig")
    primary["cluster_revenue_share"] = primary["cluster_id"].map(profiles.set_index("cluster_id")["revenue_share"])
    primary.to_csv(tables / "segments.csv", index=False, encoding="utf-8-sig")

    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    ax.plot(ks, elbow, marker="o", color="#315e9e")
    ax.set_xlabel("Số cụm K")
    ax.set_ylabel("Inertia")
    ax.set_title("Elbow — RFM chuẩn hóa (log cho Frequency/Monetary)")
    ax.grid(alpha=.25)
    fig.tight_layout()
    fig.savefig(figures / "segments_elbow.png", dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(8.5, 5.2))
    ax.plot(ks, silhouettes, marker="o", color="#b7791f", label="Silhouette trung bình")
    ax.plot(ks, stability, marker="s", color="#44715d", label="ARI ổn định theo seed")
    ax.axvline(chosen_k, color="#b42318", linestyle="--", label=f"K chọn = {chosen_k}")
    ax.set_xlabel("Số cụm K")
    ax.set_ylabel("Điểm")
    ax.set_title("Silhouette và độ ổn định")
    ax.legend(frameon=False)
    ax.grid(alpha=.25)
    fig.tight_layout()
    fig.savefig(figures / "segments_silhouette.png", dpi=160)
    plt.close(fig)

    sensitivity_metrics = {}
    for name in ("A", "B"):
        candidate = frames[name].copy()
        labels, _, score = _cluster(candidate, chosen_k, seed=42)
        sensitivity_metrics[name] = {
            "silhouette": score,
            "silhouette_delta_from_primary": score - chosen_silhouette,
            "aligned_customer_cluster_change_rate": _aligned_change_rate(primary_labels, labels, chosen_k),
        }
    metrics = {
        "customer_count": int(len(primary)),
        "single_order_customer_rate": single_rate,
        "single_order_customer_count": int((primary["frequency"] == 1).sum()),
        "k_candidates": ks,
        "elbow_inertia_by_k": dict(zip(map(str, ks), elbow)),
        "mean_silhouette_by_k": dict(zip(map(str, ks), silhouettes)),
        "seed_stability_ari_by_k": dict(zip(map(str, ks), stability)),
        "chosen_k": chosen_k,
        "chosen_silhouette": chosen_silhouette,
        "chosen_seed": 42,
        "cluster_names_by_id": {str(key): value for key, value in names.items()},
        "rule_segment_counts": {key: int(value) for key, value in primary["rule_segment"].value_counts().items()},
        "business_like_proxy": {"rule": "Monetary or maximum order value at/above development p99", "customers": int(primary["business_like_proxy"].sum()), "p99_monetary": monetary_p99, "p99_max_order_value": order_p99},
        "large_value_customers_by_cluster": {str(int(key)): int(value) for key, value in primary.groupby("cluster_id")["business_like_proxy"].sum().items()},
        "sensitivity": sensitivity_metrics,
        "dbscan_geography": {"run": False, "reason": "Nguồn chỉ có tỉnh/thành; không có tọa độ hoặc mã vùng đủ chi tiết cho DBSCAN."},
        "test_labels_loaded": False,
        "test_behavior_loaded": False,
    }
    (ROOT / "outputs" / "metrics" / "day2_segmentation.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Segmentation: customers={len(primary)}, single_order={single_rate:.2%}, chosen_K={chosen_k}, silhouette={chosen_silhouette:.3f}.")
    print(f"Sensitivity: A changed={sensitivity_metrics['A']['aligned_customer_cluster_change_rate']:.2%}, B changed={sensitivity_metrics['B']['aligned_customer_cluster_change_rate']:.2%}.")
    return metrics


if __name__ == "__main__":
    run_segmentation()
