"""Evaluate standardized RFM clusters K=3..5 on the DEV feature snapshot only."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
FEATURE_PATH = ROOT / "outputs" / "tables" / "day2_features_primary.csv"
REPORT_PATH = ROOT / "docs" / "dev_segmentation_objective_i.md"
DEV_FEATURE_AS_OF = "2025-10-22"
K_VALUES = (3, 4, 5)
SEEDS = (13, 42, 87, 2025, 7)


def _validate_dev_features(frame: pd.DataFrame) -> None:
    required = {"customer_key", "as_of", "recency_days", "frequency", "monetary"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"DEV feature snapshot is missing required columns: {sorted(missing)}")
    if frame.empty or frame["customer_key"].duplicated().any():
        raise ValueError("DEV feature snapshot must contain unique customer rows")
    if set(frame["as_of"].dropna().astype(str)) != {DEV_FEATURE_AS_OF}:
        raise ValueError("feature snapshot has an unexpected as_of date")
    if "last_purchase_date" in frame.columns:
        cutoff = pd.Timestamp(DEV_FEATURE_AS_OF)
        last_purchase = pd.to_datetime(frame["last_purchase_date"], errors="coerce")
        if (last_purchase.notna() & last_purchase.ge(cutoff)).any():
            raise ValueError("feature snapshot contains a purchase on or after the DEV cutoff")
    numeric = frame[["recency_days", "frequency", "monetary"]].apply(
        pd.to_numeric, errors="coerce"
    )
    if numeric.isna().any().any() or (numeric["recency_days"] < 0).any():
        raise ValueError("RFM features contain missing or invalid values")
    if (numeric["frequency"] < 1).any():
        raise ValueError("RFM frequency must be at least one")


def _format(value: float) -> str:
    return f"{value:,.4f}"


def main() -> int:
    if not FEATURE_PATH.is_file():
        raise FileNotFoundError(f"DEV feature snapshot not found: {FEATURE_PATH}")
    if REPORT_PATH.exists():
        raise FileExistsError(f"Refusing to overwrite report: {REPORT_PATH}")

    frame = pd.read_csv(FEATURE_PATH)
    _validate_dev_features(frame)
    rfm = frame[["recency_days", "frequency", "monetary"]].astype(float)
    transformed = np.column_stack(
        (
            rfm["recency_days"].to_numpy(),
            np.log1p(rfm["frequency"].to_numpy()),
            np.log1p(rfm["monetary"].clip(lower=0).to_numpy()),
        )
    )
    scaled = StandardScaler().fit_transform(transformed)

    results: dict[int, dict[str, object]] = {}
    for k in K_VALUES:
        scores: list[float] = []
        reference_labels: np.ndarray | None = None
        reference_model: KMeans | None = None
        for seed in SEEDS:
            model = KMeans(
                n_clusters=k, random_state=seed, n_init=20, max_iter=500
            )
            labels = model.fit_predict(scaled)
            score = float(
                silhouette_score(
                    scaled,
                    labels,
                    sample_size=min(1200, len(frame)),
                    random_state=seed,
                )
            )
            scores.append(score)
            if seed == 42:
                reference_labels = labels
                reference_model = model

        assert reference_labels is not None and reference_model is not None
        profiles: list[dict[str, float | int]] = []
        for cluster_id in range(k):
            members = rfm.loc[reference_labels == cluster_id]
            profiles.append(
                {
                    "cluster_id": cluster_id,
                    "customers": int(len(members)),
                    "recency_median_days": float(members["recency_days"].median()),
                    "frequency_median_orders": float(members["frequency"].median()),
                    "monetary_median": float(members["monetary"].median()),
                    "recency_mean_days": float(members["recency_days"].mean()),
                    "frequency_mean_orders": float(members["frequency"].mean()),
                    "monetary_mean": float(members["monetary"].mean()),
                }
            )
        results[k] = {
            "scores": scores,
            "profiles": profiles,
            "inertia": float(reference_model.inertia_),
        }

    single_order_rate = float(rfm["frequency"].eq(1).mean())
    lines = [
        "# DEV customer segmentation — Objective I",
        "",
        "## Scope and method",
        "",
        f"- Input: `{FEATURE_PATH.relative_to(ROOT)}` only; one DEV feature snapshot as of "
        f"`{DEV_FEATURE_AS_OF}`. The snapshot builder filters source orders to dates strictly "
        "before the test boundary.",
        "- No test labels, test behavior, test evaluator, API, synthetic data, or "
        "`data/restricted/test` path is read.",
        "- Features: R, F, M. Recency is untransformed; Frequency and non-negative Monetary "
        "use `log1p`; each transformed column is independently z-standardized on this DEV "
        "snapshot. Thus frequency remains in RFM but is not allowed to dominate by raw scale.",
        f"- Customers: {len(frame):,}; one-order customers: {single_order_rate:.2%}.",
        f"- K values: {', '.join(map(str, K_VALUES))}; seeds: {', '.join(map(str, SEEDS))}; "
        "silhouette uses a deterministic sample of up to 1,200 rows per seed.",
        "",
        "## Silhouette results",
        "",
        "| K | Silhouette by seed (13, 42, 87, 2025, 7) | Mean | Min–max |",
        "|---:|---|---:|---:|",
    ]
    for k, result in results.items():
        scores = result["scores"]
        assert isinstance(scores, list)
        lines.append(
            f"| {k} | {', '.join(_format(score) for score in scores)} | "
            f"{_format(float(np.mean(scores)))} | "
            f"{_format(float(np.min(scores)))}–{_format(float(np.max(scores)))} |"
        )

    lines.extend(
        [
            "",
            "## DEV-only cluster profiles",
            "",
            "Profiles below use the seed-42 assignments; cluster IDs are arbitrary. "
            "Monetary values are reported in the source feature unit (VND).",
            "",
        ]
    )
    for k, result in results.items():
        lines.extend(
            [
                f"### K={k}",
                "",
                "| Cluster | Customers | Median R (days) | Median F (orders) | "
                "Median M (VND) | Mean R | Mean F | Mean M (VND) |",
                "|---:|---:|---:|---:|---:|---:|---:|---:|",
            ]
        )
        profiles = result["profiles"]
        assert isinstance(profiles, list)
        for profile in profiles:
            lines.append(
                f"| {profile['cluster_id']} | {profile['customers']:,} | "
                f"{_format(float(profile['recency_median_days']))} | "
                f"{_format(float(profile['frequency_median_orders']))} | "
                f"{_format(float(profile['monetary_median']))} | "
                f"{_format(float(profile['recency_mean_days']))} | "
                f"{_format(float(profile['frequency_mean_orders']))} | "
                f"{_format(float(profile['monetary_mean']))} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Interpretation",
            "",
            "**No business meaning is established by this experiment.** Silhouette measures "
            "geometric separation in standardized RFM space, not customer value, "
            "actionability, retention, or causal impact. The profiles are descriptive DEV "
            "summaries only; without independent business-outcome or stakeholder validation, "
            "whether these clusters are actionable is unknown. Do not select or name a "
            "production segmentation from silhouette alone.",
            "",
            "## Reproduction",
            "",
            "```powershell",
            r".\.venv\Scripts\python.exe scripts\evaluate_dev_segmentation_objective_i.py",
            "```",
            "",
        ]
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote DEV-only segmentation report: {REPORT_PATH.relative_to(ROOT)}")
    for k, result in results.items():
        scores = result["scores"]
        assert isinstance(scores, list)
        print(f"K={k}: silhouette mean={np.mean(scores):.6f}, range={min(scores):.6f}..{max(scores):.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
