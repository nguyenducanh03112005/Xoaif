"""Build aggregate-only DEV EDA figures from the frozen development warehouse."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "restricted" / "xoaif_dev.duckdb"
FEATURES = ROOT / "outputs" / "tables" / "day2_label_samples_primary.csv"
OUT_JSON = ROOT / "outputs" / "metrics" / "eda_dev_summary.json"
FIG_DIR = ROOT / "outputs" / "figures"
ANALYSIS_START = date(2024, 4, 1)  # D-014; all EDA uses the approved DEV window.


def _q(values: pd.Series, quantiles: list[float]) -> dict[str, int]:
    result = values.quantile(quantiles)
    # VND is reported to the nearest dong; avoid float tails that resemble phone numbers.
    return {str(int(q * 100)): int(round(result.loc[q])) for q in quantiles}


def main() -> int:
    split = yaml.safe_load((ROOT / "config" / "split.yaml").read_text(encoding="utf-8"))
    dev_end = date.fromisoformat(str(split["test_start"]))
    if not DB.is_file() or not FEATURES.is_file():
        raise FileNotFoundError("Required development-only source is missing")

    con = duckdb.connect(str(DB), read_only=True)
    try:
        bounds = con.execute(
            "SELECT count(*), min(local_date), max(local_date), "
            "count(*) FILTER (WHERE local_date < ?), "
            "count(*) FILTER (WHERE local_date >= ?) FROM fact_orders",
            [ANALYSIS_START, dev_end],
        ).fetchone()
        if bounds[3] or bounds[4] or bounds[1] is None or bounds[2] >= dev_end:
            raise ValueError("Development warehouse contains rows outside [analysis_start, test_start)")

        monthly_rows = con.execute(
            "SELECT date_trunc('month', local_date)::DATE AS month_start, count(*) AS orders "
            "FROM fact_orders WHERE status_code = 3 AND local_date >= ? AND local_date < ? "
            "GROUP BY 1 ORDER BY 1",
            [ANALYSIS_START, dev_end],
        ).fetchall()
        status_rows = con.execute(
            "SELECT status_code, count(*) AS orders, "
            "count(*) FILTER (WHERE customer_key IS NULL) AS missing_customer "
            "FROM fact_orders GROUP BY status_code ORDER BY status_code"
        ).fetchall()
        basket_rows = con.execute(
            "SELECT distinct_product_count, count(*) AS orders FROM fact_orders "
            "WHERE status_code = 3 AND local_date >= ? AND local_date < ? "
            "GROUP BY 1 ORDER BY 1",
            [ANALYSIS_START, dev_end],
        ).fetchall()
        customer_frequency_rows = con.execute(
            "WITH per_customer AS (SELECT customer_key, count(*) AS n FROM fact_orders "
            "WHERE status_code = 3 AND local_date >= ? AND local_date < ? "
            "AND customer_key IS NOT NULL GROUP BY customer_key) "
            "SELECT CASE WHEN n = 1 THEN '1' WHEN n = 2 THEN '2' ELSE '3+' END AS band, "
            "count(*) AS customers FROM per_customer GROUP BY 1 ORDER BY 1",
            [ANALYSIS_START, dev_end],
        ).fetchall()
    finally:
        con.close()

    labels = pd.read_csv(
        FEATURES,
        usecols=["as_of", "frequency", "recency_days", "monetary", "average_order_value", "label_returned"],
    )
    required = {"as_of", "frequency", "recency_days", "monetary", "average_order_value", "label_returned"}
    if not required.issubset(labels.columns):
        raise ValueError("DEV label-feature table is missing required aggregate fields")
    if labels.empty or (pd.to_datetime(labels["as_of"]).dt.date >= dev_end).any():
        raise ValueError("EDA label source is empty or reaches the reserved period")
    if not set(labels["label_returned"].dropna().unique()).issubset({0, 1}):
        raise ValueError("Unexpected DEV outcome values")

    label_groups = []
    labels = labels.assign(frequency_band=labels["frequency"].map(lambda n: "1" if n == 1 else "2+"))
    for band, frame in labels.groupby("frequency_band", sort=True):
        label_groups.append({
            "band": str(band), "samples": int(len(frame)),
            "positive": int(frame["label_returned"].sum()),
            "positive_rate": float(frame["label_returned"].mean()),
        })
    recency_edges = [-1, 7, 14, 21, 28, float("inf")]
    recency_names = ["0-7", "8-14", "15-21", "22-28", "29+"]
    labels = labels.assign(recency_band=pd.cut(labels["recency_days"], recency_edges, labels=recency_names))
    recency_groups = []
    for band in recency_names:
        frame = labels[labels["recency_band"] == band]
        recency_groups.append({
            "band_days": band, "samples": int(len(frame)),
            "positive": int(frame["label_returned"].sum()),
            "positive_rate": float(frame["label_returned"].mean()) if len(frame) else None,
        })

    status = {int(code): {"orders": int(n), "missing_customer": int(missing)} for code, n, missing in status_rows}
    basket_counts = {int(size): int(n) for size, n in basket_rows}
    frequency_counts = {str(band): int(n) for band, n in customer_frequency_rows}
    monthly = [{"month": month.isoformat()[:7], "orders": int(n)} for month, n in monthly_rows]
    order_count = sum(basket_counts.values())
    summary = {
        "scope": {
            "source": "data/restricted/xoaif_dev.duckdb (read-only) and outputs/tables/day2_label_samples_primary.csv",
            "period": f"[{ANALYSIS_START.isoformat()}, {dev_end.isoformat()})",
            "filter": "status_code = 3 for order and customer-frequency summaries; historical DEV label samples only for label summaries",
            "test_data_read_by_this_build": False,
            "identifiers_or_row_level_data_written": False,
        },
        "status_orders": {str(k): v for k, v in status.items()},
        "valid_order_count": int(order_count),
        "valid_customer_frequency_counts": frequency_counts,
        "basket": {
            "orders_with_zero_or_one_distinct_product": int(sum(n for size, n in basket_counts.items() if size <= 1)),
            "orders": int(order_count),
            "median_distinct_products": float(pd.Series([size for size, n in basket_counts.items() for _ in range(n)]).median()),
            "p90_distinct_products": float(pd.Series([size for size, n in basket_counts.items() for _ in range(n)]).quantile(0.9)),
            "distribution": [{"distinct_products": size, "orders": n} for size, n in sorted(basket_counts.items())],
        },
        "monthly_valid_orders": monthly,
        "dev_label_samples": {
            "samples": int(len(labels)), "positives": int(labels["label_returned"].sum()),
            "positive_rate": float(labels["label_returned"].mean()),
            "as_of_count": int(labels["as_of"].nunique()),
            "as_of_min": str(labels["as_of"].min()), "as_of_max": str(labels["as_of"].max()),
            "frequency_bands": label_groups, "recency_bands": recency_groups,
            "average_order_value_zero_samples": int((labels["average_order_value"] == 0).sum()),
            "monetary_vnd_quantiles": _q(labels["monetary"], [0.5, 0.9, 0.95, 0.99]),
            "average_order_value_vnd_quantiles": _q(labels["average_order_value"], [0.5, 0.9, 0.95, 0.99]),
        },
    }

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "Arial", "axes.unicode_minus": False})
    months = pd.DataFrame(monthly)
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(months["month"], months["orders"], marker="o", color="#176B87", linewidth=1.8)
    ax.set_title("Đơn status 3 theo tháng — DEV")
    ax.set_xlabel("Tháng địa phương"); ax.set_ylabel("Số đơn")
    ax.tick_params(axis="x", rotation=45); ax.grid(axis="y", alpha=0.25)
    fig.tight_layout(); fig.savefig(FIG_DIR / "eda_dev_monthly_orders.png", dpi=160); plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    sizes = sorted(basket_counts)
    counts = [basket_counts[size] for size in sizes]
    ax.bar([str(x) for x in sizes], counts, color="#73A98F")
    ax.set_title("Số product phân biệt trong mỗi đơn hợp lệ — DEV")
    ax.set_xlabel("Product phân biệt / đơn"); ax.set_ylabel("Số đơn")
    ax.grid(axis="y", alpha=0.25); fig.tight_layout()
    fig.savefig(FIG_DIR / "eda_dev_basket_size.png", dpi=160); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    bands = ["1", "2", "3+"]
    counts = [frequency_counts.get(x, 0) for x in bands]
    ax.bar(bands, counts, color="#E3A64B")
    ax.set_title("Số đơn status 3 trên mỗi khách đã biết — DEV đến trước T")
    ax.set_xlabel("Số đơn / khách"); ax.set_ylabel("Số khách")
    ax.grid(axis="y", alpha=0.25); fig.tight_layout()
    fig.savefig(FIG_DIR / "eda_dev_customer_frequency.png", dpi=160); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    x = [item["band"] for item in label_groups]
    rates = [100 * item["positive_rate"] for item in label_groups]
    bars = ax.bar(x, rates, color="#176B87")
    for bar, item in zip(bars, label_groups):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), f"{item['positive_rate']:.1%}\nn={item['samples']}", ha="center", va="bottom", fontsize=9)
    ax.axhline(100 * summary["dev_label_samples"]["positive_rate"], color="#A14633", linestyle="--", linewidth=1, label="Tỷ lệ nền DEV")
    ax.set_title("Tỷ lệ mua lại DEV theo frequency lịch sử tại T")
    ax.set_xlabel("Số đơn trước T"); ax.set_ylabel("Có mua trong (T, T+180 ngày] (%)")
    ax.legend(frameon=False); ax.grid(axis="y", alpha=0.25); fig.tight_layout()
    fig.savefig(FIG_DIR / "eda_dev_label_rate_by_frequency.png", dpi=160); plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    values = labels["average_order_value"] / 1_000_000
    positive_values = values[values > 0]
    bins = np.geomspace(max(0.001, float(positive_values.min())), float(positive_values.max()), 28)
    ax.hist(positive_values, bins=bins, color="#73A98F", edgecolor="white")
    ax.set_xscale("log"); ax.set_title("Phân phối AOV đặc trưng — mẫu nhãn DEV")
    ax.set_xlabel("AOV (triệu VND, trục log)"); ax.set_ylabel("Số mẫu")
    ax.set_xticks([0.01, 0.1, 1, 10]); ax.set_xticklabels(["0,01", "0,1", "1", "10"])
    if summary["dev_label_samples"]["average_order_value_zero_samples"]:
        ax.text(0.02, 0.98, f"0 VND không hiện trên trục log: n={summary['dev_label_samples']['average_order_value_zero_samples']}", transform=ax.transAxes, va="top", fontsize=8)
    ax.grid(axis="y", alpha=0.25); fig.tight_layout()
    fig.savefig(FIG_DIR / "eda_dev_aov_distribution.png", dpi=160); plt.close(fig)

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote aggregate-only DEV EDA summary and 5 figures; orders={order_count}; label_samples={len(labels)}; positives={int(labels['label_returned'].sum())}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
