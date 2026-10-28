"""Fixed, DEV-only repurchase v3 comparisons and diagnostics."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

SEED = 20261028
BOOTSTRAP_DRAWS = 2000
MODEL_FEATURES = [
    "recency_days", "frequency", "monetary", "mean_days_between_orders",
    "first_purchase_age_days", "t_month_sin", "t_month_cos",
]
STRATEGIES = {
    "constant_common": [],
    "recency_only": ["recency_days"],
    "frequency_only": ["frequency"],
    "logistic_v3": MODEL_FEATURES,
}


def _metric_bundle(y: np.ndarray, score: np.ndarray) -> dict[str, float]:
    if len(np.unique(y)) < 2:
        return {"roc_auc": float("nan"), "average_precision": float("nan"), "brier": brier_score_loss(y, score)}
    return {
        "roc_auc": float(roc_auc_score(y, score)),
        "average_precision": float(average_precision_score(y, score)),
        "brier": float(brier_score_loss(y, score)),
    }


def _weighted_metric_bundle(y: np.ndarray, score: np.ndarray, weight: np.ndarray) -> dict[str, float]:
    valid = weight > 0
    y, score, weight = y[valid], score[valid], weight[valid].astype(float)
    positive = float(np.dot(weight, y))
    negative = float(np.dot(weight, 1 - y))
    if positive <= 0 or negative <= 0:
        return {"roc_auc": float("nan"), "average_precision": float("nan"),
                "brier": float(np.average((y - score) ** 2, weights=weight))}
    unique_scores, group_id = np.unique(score, return_inverse=True)
    positive_by_score = np.bincount(group_id, weights=weight * y, minlength=len(unique_scores))[::-1]
    negative_by_score = np.bincount(group_id, weights=weight * (1 - y), minlength=len(unique_scores))[::-1]
    tp = np.cumsum(positive_by_score)
    fp = np.cumsum(negative_by_score)
    neg_below = negative - fp
    roc_auc = float(np.dot(positive_by_score, neg_below + 0.5 * negative_by_score) / (positive * negative))
    precision = tp / np.maximum(tp + fp, 1e-15)
    average_precision = float(np.dot(positive_by_score / positive, precision))
    return {
        "roc_auc": roc_auc,
        "average_precision": average_precision,
        "brier": float(np.average((y - score) ** 2, weights=weight)),
    }


def _new_model() -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(
            C=10, class_weight="balanced", solver="lbfgs", max_iter=2000,
            random_state=SEED,
        )),
    ])


def evaluate_fixed_models(
    frame: pd.DataFrame,
    folds: list[dict[str, Any]],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Fit the four preregistered strategies with preprocessing inside folds."""
    if not folds:
        raise ValueError("no eligible temporal validation folds")
    first_train = folds[0]["train"]
    common_probability = float(frame.iloc[first_train]["label_returned"].mean())
    predictions: dict[str, dict[int, float]] = {name: {} for name in STRATEGIES}
    fold_rows: list[dict[str, Any]] = []
    for fold_number, fold in enumerate(folds, start=1):
        train = frame.iloc[fold["train"]]
        valid = frame.iloc[fold["validation"]]
        y_train = train["label_returned"].astype(int).to_numpy()
        y_valid = valid["label_returned"].astype(int).to_numpy()
        valid_indices = np.asarray(fold["validation"], dtype=int)
        predictions["constant_common"].update({int(i): common_probability for i in valid_indices})
        fold_prediction: dict[str, np.ndarray] = {"constant_common": np.full(len(valid), common_probability)}
        for name in ("recency_only", "frequency_only", "logistic_v3"):
            columns = STRATEGIES[name]
            model = _new_model()
            model.fit(train[columns], y_train)
            probability = model.predict_proba(valid[columns])[:, 1]
            predictions[name].update({int(i): float(p) for i, p in zip(valid_indices, probability)})
            fold_prediction[name] = probability
        for name, probability in fold_prediction.items():
            metrics = _metric_bundle(y_valid, probability)
            fold_rows.append({
                "strategy": name,
                "fold": fold_number,
                "validation_T": str(fold["validation_t"]),
                "train_n": len(train),
                "validation_n": len(valid),
                "validation_customers": int(valid["customer_key"].nunique()),
                "train_customers": int(train["customer_key"].nunique()),
                "customer_overlap_train_validation": int(fold["customer_overlap_n"]),
                "validation_positive_n": int(y_valid.sum()),
                "validation_prevalence": float(y_valid.mean()),
                **metrics,
            })

    prediction_rows = []
    for name, scores_by_idx in predictions.items():
        for index, score in scores_by_idx.items():
            row = frame.iloc[index]
            prediction_rows.append({
                "strategy": name,
                "index": index,
                "customer_key": row["customer_key"],
                "as_of": row["as_of"],
                "label_returned": int(row["label_returned"]),
                "score": score,
            })
    pred = pd.DataFrame(prediction_rows)
    return pred, pd.DataFrame(fold_rows), {"common_baseline_probability": common_probability}


def _ranking_tables(pred: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    deciles: list[dict[str, Any]] = []
    grouped = [
        (str(strategy), str(fold), group)
        for (strategy, fold), group in pred.groupby(["strategy", "as_of"], sort=True)
        if strategy != "constant_common"
    ] + [
        (str(strategy), "pooled", group)
        for strategy, group in pred.groupby("strategy", sort=True)
        if strategy != "constant_common"
    ]
    for strategy, label, group in grouped:
        ordered = group.sort_values(["score", "customer_key"], ascending=[False, True]).reset_index(drop=True)
        base = float(ordered["label_returned"].mean())
        for decile in range(1, 11):
            start = math.floor((decile - 1) * len(ordered) / 10)
            end = math.floor(decile * len(ordered) / 10)
            subset = ordered.iloc[start:end]
            rate = float(subset["label_returned"].mean()) if len(subset) else float("nan")
            deciles.append({
                "strategy": strategy, "fold_or_pooled": label,
                "decile_from_top": decile, "n": len(subset),
                "positive_n": int(subset["label_returned"].sum()),
                "positive_rate": rate,
                "cumulative_gain": float(ordered.iloc[:end]["label_returned"].sum() / max(ordered["label_returned"].sum(), 1)),
                "lift": rate / base if base > 0 else None,
            })
    top_k: list[dict[str, Any]] = []
    for strategy, label, group in grouped:
        ordered = group.sort_values(["score", "customer_key"], ascending=[False, True]).reset_index(drop=True)
        prevalence = float(ordered["label_returned"].mean())
        for pct in (5, 10, 20):
            n_top = max(1, math.ceil(len(ordered) * pct / 100))
            selected = ordered.iloc[:n_top]
            precision = float(selected["label_returned"].mean())
            top_k.append({
                "strategy": strategy, "fold_or_pooled": label, "top_pct": pct,
                "n": n_top, "positive_n": int(selected["label_returned"].sum()),
                "precision": precision,
                "lift_vs_prevalence": precision / prevalence if prevalence else None,
            })
    return pd.DataFrame(deciles), pd.DataFrame(top_k)


def _bootstrap_ci(pred: pd.DataFrame, *, draws: int = BOOTSTRAP_DRAWS, seed: int = SEED) -> dict[str, Any]:
    rng = np.random.default_rng(seed)
    rows: dict[str, dict[str, list[float]]] = {}
    for strategy, subset in pred.groupby("strategy", sort=True):
        ids = subset["customer_key"].drop_duplicates().to_numpy()
        customer_index = pd.Index(ids).get_indexer(subset["customer_key"])
        y = subset["label_returned"].to_numpy(dtype=int)
        score = subset["score"].to_numpy(dtype=float)
        order = np.argsort(-score, kind="stable")
        y_sorted = y[order]
        customer_sorted = customer_index[order]
        extra_metrics = [] if strategy == "constant_common" else [
            *(f"precision_at_{pct}pct" for pct in (5, 10, 20)),
            *(f"top_decile_rate_{decile}" for decile in range(1, 11)),
        ]
        rows[strategy] = {key: [] for key in ("roc_auc", "average_precision", "brier", *extra_metrics)}
        for _ in range(draws):
            multiplicity = rng.multinomial(len(ids), np.full(len(ids), 1 / len(ids)))
            weight = multiplicity[customer_index]
            valid = weight > 0
            metrics = _weighted_metric_bundle(y, score, weight)
            sorted_weights = weight[order]
            total_weight = float(sorted_weights.sum())
            cumulative = np.cumsum(sorted_weights)
            previous = np.concatenate(([0.0], cumulative[:-1]))
            if strategy != "constant_common":
                for pct in (5, 10, 20):
                    target = total_weight * pct / 100
                    full = int(np.searchsorted(cumulative, target, side="left"))
                    positive_mass = float(np.dot(sorted_weights[:full], y_sorted[:full]))
                    remaining = target - float(cumulative[full - 1] if full else 0.0)
                    if full < len(y_sorted):
                        positive_mass += remaining * y_sorted[full]
                    metrics[f"precision_at_{pct}pct"] = positive_mass / target
                for decile in range(1, 11):
                    low = total_weight * (decile - 1) / 10
                    high = total_weight * decile / 10
                    start = int(np.searchsorted(cumulative, low, side="right"))
                    end = min(len(sorted_weights), int(np.searchsorted(cumulative, high, side="left")) + 1)
                    indices = np.arange(start, end)
                    segment_weights = np.maximum(
                        0.0,
                        np.minimum(cumulative[indices], high) - np.maximum(previous[indices], low),
                    )
                    denominator = max(0.0, high - low)
                    metrics[f"top_decile_rate_{decile}"] = (
                        float(np.dot(segment_weights, y_sorted[indices]) / denominator)
                        if denominator else float("nan")
                    )
            for metric, value in metrics.items():
                if math.isfinite(value):
                    rows[strategy][metric].append(value)
    result: dict[str, Any] = {}
    for strategy, metrics in rows.items():
        result[strategy] = {}
        for metric, values in metrics.items():
            result[strategy][metric] = {
                "lower_95": float(np.quantile(values, 0.025)) if values else None,
                "upper_95": float(np.quantile(values, 0.975)) if values else None,
                "valid_draws": len(values),
            }
    return result


def summarize_predictions(pred: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    pooled = []
    for strategy, group in pred.groupby("strategy", sort=True):
        values = _metric_bundle(group["label_returned"].to_numpy(), group["score"].to_numpy())
        pooled.append({
            "strategy": strategy, "n": len(group),
            "customers": int(group["customer_key"].nunique()),
            "positive_n": int(group["label_returned"].sum()),
            "prevalence": float(group["label_returned"].mean()),
            **values,
        })
    deciles, top_k = _ranking_tables(pred)
    calibration: list[dict[str, Any]] = []
    for strategy, group in pred.groupby("strategy", sort=True):
        if group["score"].nunique() == 1:
            bins = pd.DataFrame({"score": group["score"], "label_returned": group["label_returned"], "bin": 1})
        else:
            bins = group.assign(bin=pd.qcut(group["score"], q=10, labels=False, duplicates="drop") + 1)
        for bin_id, values in bins.groupby("bin", sort=True):
            calibration.append({
                "strategy": strategy, "bin": int(bin_id), "n": len(values),
                "mean_predicted": float(values["score"].mean()),
                "observed_rate": float(values["label_returned"].mean()),
            })
    return pd.DataFrame(pooled), deciles, top_k, {"calibration": calibration, "bootstrap_95": _bootstrap_ci(pred)}
