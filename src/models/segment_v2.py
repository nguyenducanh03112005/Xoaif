"""Pre-registered Day 2B RFM rule segments and K=3/K=4 stability checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
SEEDS = (13, 42, 87, 2025, 7)
K_VALUES = (3, 4)


def _rfm_matrix(frame: pd.DataFrame) -> np.ndarray:
    return np.column_stack([
        frame["recency_days"].astype(float).to_numpy(),
        np.log1p(frame["frequency"].astype(float).to_numpy()),
        np.log1p(frame["monetary"].clip(lower=0).astype(float).to_numpy()),
    ])


def _labels(frame: pd.DataFrame, k: int, seed: int) -> tuple[np.ndarray, float]:
    scaled = StandardScaler().fit_transform(_rfm_matrix(frame))
    model = KMeans(n_clusters=k, random_state=seed, n_init=10, max_iter=500)
    labels = model.fit_predict(scaled)
    silhouette = float(silhouette_score(scaled, labels, sample_size=min(1200, len(frame)), random_state=seed))
    return labels.astype(int), silhouette


def _business_proxy(frame: pd.DataFrame, thresholds: dict[str, float]) -> pd.Series:
    low_frequency = frame["frequency"].astype(float) <= thresholds["frequency_p25"]
    high_value = frame["monetary"].astype(float).ge(thresholds["monetary_p99"]) | frame["max_order_value"].astype(float).ge(thresholds["max_order_value_p99"])
    return low_frequency & high_value


def _rule_segments(frame: pd.DataFrame) -> tuple[pd.Series, dict[str, float]]:
    thresholds = {
        "frequency_p25": float(frame["frequency"].quantile(.25)),
        "frequency_p50": float(frame["frequency"].quantile(.50)),
        "frequency_p75": float(frame["frequency"].quantile(.75)),
        "monetary_p75": float(frame["monetary"].quantile(.75)),
        "monetary_p99": float(frame["monetary"].quantile(.99)),
        "max_order_value_p99": float(frame["max_order_value"].quantile(.99)),
    }
    proxy = _business_proxy(frame, thresholds)
    single = frame["frequency"].astype(int).eq(1)
    one_order_median_recency = float(frame.loc[single, "recency_days"].median()) if single.any() else float(frame["recency_days"].median())
    thresholds["one_order_recency_p50"] = one_order_median_recency
    labels = []
    for idx, row in frame.iterrows():
        if bool(proxy.loc[idx]):
            name = "Giá trị lớn, tần suất thấp"
        elif float(row["monetary"]) >= thresholds["monetary_p75"]:
            name = "Giá trị cao"
        elif int(row["frequency"]) >= 2:
            name = "Mua lặp lại"
        elif float(row["recency_days"]) <= one_order_median_recency:
            name = "Mua một lần gần đây"
        else:
            name = "Mua một lần đã lâu"
        labels.append("Theo quy tắc nghiệp vụ — " + name)
    return pd.Series(labels, index=frame.index, name="rule_segment_v2"), thresholds


def _cluster_name(profile: dict[str, Any], k: int, overall: pd.DataFrame) -> str:
    med_f = float(profile["median_frequency"])
    mean_r = float(profile["mean_recency_days"])
    mean_m = float(profile["mean_monetary"])
    if med_f >= 2:
        descriptor = f"mua lặp lại, F TB {float(profile['mean_frequency']):.2f}"
    elif mean_m >= float(overall["monetary"].quantile(.75)):
        descriptor = f"giá trị cao, M TB {mean_m:,.0f} VND"
    elif mean_r <= float(overall["recency_days"].median()):
        descriptor = f"đơn lẻ gần đây, R TB {mean_r:.0f} ngày"
    else:
        descriptor = f"đơn lẻ lâu rồi, R TB {mean_r:.0f} ngày"
    return f"K={k} cụm {int(profile['cluster_id'])}: {descriptor}"


def _profile(frame: pd.DataFrame, labels: np.ndarray, scheme: str, names: dict[int, str]) -> list[dict[str, Any]]:
    work = frame.copy()
    work["cluster_id"] = labels
    thresholds = {
        "frequency_p25": float(frame["frequency"].quantile(.25)),
        "monetary_p99": float(frame["monetary"].quantile(.99)),
        "max_order_value_p99": float(frame["max_order_value"].quantile(.99)),
    }
    work["business_like_proxy"] = _business_proxy(frame, thresholds).to_numpy(dtype=bool)
    total_revenue = float(work["monetary"].sum())
    groups = work.groupby("cluster_id", sort=True)
    rows = []
    for cluster_id, group in groups:
        rows.append({
            "scheme": scheme,
            "cluster_id": int(cluster_id),
            "cluster_name": names.get(int(cluster_id), f"cluster {int(cluster_id)}"),
            "customers": int(len(group)),
            "recognized_revenue_vnd": float(group["monetary"].sum()),
            "revenue_share": float(group["monetary"].sum() / total_revenue) if total_revenue else 0.0,
            "mean_recency_days": float(group["recency_days"].mean()),
            "median_recency_days": float(group["recency_days"].median()),
            "mean_frequency": float(group["frequency"].mean()),
            "median_frequency": float(group["frequency"].median()),
            "mean_monetary": float(group["monetary"].mean()),
            "median_monetary": float(group["monetary"].median()),
            "large_value_proxy_customers": int(group["business_like_proxy"].sum()),
        })
    return rows


def run_segmentation_v2() -> dict[str, Any]:
    tables = ROOT / "outputs" / "tables"
    figures = ROOT / "outputs" / "figures"
    metrics_dir = ROOT / "outputs" / "metrics"
    primary = pd.read_csv(tables / "day2_features_primary.csv")
    variant_b = pd.read_csv(tables / "day2_features_B.csv")
    frozen_k2 = pd.read_csv(tables / "segments.csv")[["customer_key", "cluster_id", "cluster_name"]]
    if primary.empty or primary["customer_key"].duplicated().any():
        raise ValueError("Day 2B segmentation requires one row per development customer")
    primary["cluster_id_k2"] = primary["customer_key"].map(frozen_k2.set_index("customer_key")["cluster_id"])
    primary["cluster_name_k2"] = primary["customer_key"].map(frozen_k2.set_index("customer_key")["cluster_name"])
    if primary["cluster_id_k2"].isna().any():
        raise ValueError("frozen K=2 customer assignments are incomplete")
    proxy_thresholds = {
        "frequency_p25": float(primary["frequency"].quantile(.25)),
        "monetary_p99": float(primary["monetary"].quantile(.99)),
        "max_order_value_p99": float(primary["max_order_value"].quantile(.99)),
    }
    rule_labels, rule_thresholds = _rule_segments(primary)
    primary["rule_segment_v2"] = rule_labels
    primary["business_like_proxy_v2"] = _business_proxy(primary, proxy_thresholds).astype(int)

    profiles = []
    original_names = dict(zip(frozen_k2["cluster_id"].astype(int), frozen_k2["cluster_name"].astype(str)))
    profiles.extend(_profile(primary, primary["cluster_id_k2"].astype(int).to_numpy(), "K=2 frozen", original_names))
    primary_profiles: dict[str, dict[int, np.ndarray]] = {}
    b_profiles: dict[str, dict[int, np.ndarray]] = {}
    silhouette_runs: dict[str, list[float]] = {}
    seed_ari: dict[str, dict[str, Any]] = {}
    primary_common: dict[str, dict[int, np.ndarray]] = {}
    b_common: dict[str, dict[int, np.ndarray]] = {}
    common_keys = sorted(set(primary["customer_key"]) & set(variant_b["customer_key"]))
    p_common_frame = primary.set_index("customer_key").loc[common_keys].reset_index()
    b_common_frame = variant_b.set_index("customer_key").loc[common_keys].reset_index()

    for k in K_VALUES:
        p_runs: dict[int, np.ndarray] = {}
        b_runs: dict[int, np.ndarray] = {}
        p_scores: list[float] = []
        b_scores: list[float] = []
        for seed in SEEDS:
            p_labels, p_silhouette = _labels(primary, k, seed)
            b_labels, b_silhouette = _labels(variant_b, k, seed)
            p_runs[seed] = p_labels
            b_runs[seed] = b_labels
            p_scores.append(p_silhouette)
            b_scores.append(b_silhouette)
        pair_scores = [
            float(adjusted_rand_score(p_runs[seed_a], p_runs[seed_b]))
            for i, seed_a in enumerate(SEEDS) for seed_b in SEEDS[i + 1:]
        ]
        p_common_runs = {}
        b_common_runs = {}
        for seed in SEEDS:
            p_common_labels, _ = _labels(p_common_frame, k, seed)
            b_common_labels, _ = _labels(b_common_frame, k, seed)
            p_common_runs[seed] = p_common_labels
            b_common_runs[seed] = b_common_labels
        cross_variant = {
            str(seed): float(adjusted_rand_score(p_common_runs[seed], b_common_runs[seed]))
            for seed in SEEDS
        }
        primary_profiles[str(k)] = p_runs
        b_profiles[str(k)] = b_runs
        primary_common[str(k)] = p_common_runs
        b_common[str(k)] = b_common_runs
        silhouette_runs[str(k)] = p_scores
        seed_ari[str(k)] = {
            "primary_pairwise_ari_mean": float(np.mean(pair_scores)),
            "primary_pairwise_ari_min": float(np.min(pair_scores)),
            "primary_pairwise_ari_values": pair_scores,
            "sensitivity_B_silhouette_mean": float(np.mean(b_scores)),
            "sensitivity_B_primary_ari_by_seed_on_common_customers": cross_variant,
            "sensitivity_B_common_customer_count": len(common_keys),
        }
        chosen_labels = p_runs[42]
        base_profiles = _profile(primary, chosen_labels, f"K={k} seed=42", {})
        names = {row["cluster_id"]: _cluster_name(row, k, primary) for row in base_profiles}
        profiles.extend(_profile(primary, chosen_labels, f"K={k} seed=42", names))
        primary[f"cluster_id_k{k}"] = chosen_labels
        primary[f"cluster_name_k{k}"] = [names[int(label)] for label in chosen_labels]

    rule_proxy_names = sorted(primary.loc[primary["business_like_proxy_v2"].eq(1), "rule_segment_v2"].unique())
    rule_profiles = []
    for name, group in primary.groupby("rule_segment_v2", sort=True):
        total = float(primary["monetary"].sum())
        rule_profiles.append({
            "scheme": "Theo quy tắc nghiệp vụ",
            "cluster_id": name,
            "cluster_name": name,
            "customers": int(len(group)),
            "recognized_revenue_vnd": float(group["monetary"].sum()),
            "revenue_share": float(group["monetary"].sum() / total) if total else 0.0,
            "mean_recency_days": float(group["recency_days"].mean()),
            "median_recency_days": float(group["recency_days"].median()),
            "mean_frequency": float(group["frequency"].mean()),
            "median_frequency": float(group["frequency"].median()),
            "mean_monetary": float(group["monetary"].mean()),
            "median_monetary": float(group["monetary"].median()),
            "large_value_proxy_customers": int(group["business_like_proxy_v2"].sum()),
        })
    profiles.extend(rule_profiles)
    profile_frame = pd.DataFrame(profiles)
    primary.to_csv(tables / "segments_v2.csv", index=False, encoding="utf-8-sig")
    profile_frame.to_csv(tables / "segment_profiles_v2.csv", index=False, encoding="utf-8-sig")
    figure, axis = plt.subplots(figsize=(8.5, 5.2))
    ks = list(K_VALUES)
    silhouette_means = [float(np.mean(silhouette_runs[str(k)])) for k in ks]
    ari_means = [seed_ari[str(k)]["primary_pairwise_ari_mean"] for k in ks]
    axis.plot(ks, silhouette_means, marker="o", label="Silhouette mean (primary)")
    axis.plot(ks, ari_means, marker="s", label="ARI mean across seeds (primary)")
    axis.set_xticks(ks)
    axis.set_xlabel("K (K=2 frozen from Day 2; additions K=3,4)")
    axis.set_ylabel("Score")
    axis.set_title("Day 2B — silhouette and seed stability")
    axis.grid(alpha=.25)
    axis.legend(frameon=False)
    figure.tight_layout()
    figure.savefig(figures / "segments_v2_stability.png", dpi=160)
    plt.close(figure)

    metrics = {
        "customer_count": int(len(primary)),
        "common_primary_B_customer_count": len(common_keys),
        "k2_frozen_from_day2": True,
        "candidate_k": list(K_VALUES),
        "seeds": list(SEEDS),
        "primary_seed_stability_ari": seed_ari,
        "silhouette_mean_by_k_primary": {str(k): float(np.mean(silhouette_runs[str(k)])) for k in K_VALUES},
        "rule_based_quantile_thresholds": rule_thresholds,
        "business_like_proxy_rule": "Monetary >= development p99 OR max order value >= development p99, and Frequency <= development p25",
        "business_like_proxy_thresholds": proxy_thresholds,
        "business_like_proxy_customers": int(primary["business_like_proxy_v2"].sum()),
        "rule_based_segment_counts": {key: int(value) for key, value in primary["rule_segment_v2"].value_counts().items()},
        "business_like_proxy_segment_names": rule_proxy_names,
        "no_churn_risk_label_used": True,
        "test_labels_loaded": False,
        "test_behavior_loaded": False,
    }
    (metrics_dir / "day2b_segmentation.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return metrics


if __name__ == "__main__":
    run_segmentation_v2()
