"""Build Day 1 development-only gap counts and split timeline figure."""
from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path
import sys

import duckdb
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data/restricted/xoaif_dev.duckdb"
sys.path.insert(0, str(ROOT / "src"))

from ingest.analysis_amendment import load_analysis_amendment


def build_gap_csv() -> list[tuple[date, int, int, int]]:
    con = duckdb.connect(str(DB), read_only=True)
    rows = con.execute("""
        WITH months AS (
          SELECT month_start::DATE AS month_start FROM generate_series(
            DATE '2022-10-01', DATE '2024-03-01', INTERVAL '1 month'
          ) AS t(month_start)
        ), counts AS (
          SELECT date_trunc('month', local_date)::DATE AS month_start,
                 count(*) AS all_orders,
                 count(*) FILTER (WHERE status_code = 3) AS status3_orders,
                 count(*) FILTER (WHERE status_code <> 3) AS other_status_orders
          FROM fact_orders GROUP BY 1
        )
        SELECT m.month_start, coalesce(c.all_orders, 0),
               coalesce(c.status3_orders, 0), coalesce(c.other_status_orders, 0)
        FROM months m LEFT JOIN counts c USING (month_start)
        ORDER BY m.month_start
    """).fetchall()
    con.close()
    path = ROOT / "outputs/tables/day1_gap_2022-10_to_2024-03.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["month", "all_status_orders", "status_3_orders", "other_status_orders"])
        writer.writerows([[d.isoformat()[:7], a, s3, other] for d, a, s3, other in rows])
    return rows


def build_timeline() -> None:
    out = ROOT / "outputs/figures/split_timeline.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(14, 7.2))
    fig.subplots_adjust(left=0.09, right=0.97, top=0.85, bottom=0.32)
    amendment, _, _ = load_analysis_amendment(ROOT)
    start = date.fromisoformat(str(amendment["analysis_start"]))
    cutoff = date(2026, 10, 24)  # exclusive
    test_start = date(2025, 10, 22)
    test_end = date(2026, 4, 20)  # exclusive
    last_test_t = test_end - timedelta(days=1)
    label_end = last_test_t + timedelta(days=180)
    label_asof = label_end + timedelta(days=7)

    ax.axvspan(start, test_start, color="#8cc7a1", alpha=0.48, label="Tập phát triển (EDA chỉ trước test_start)")
    ax.axvspan(test_start, test_end, color="#e9b44c", alpha=0.45, label="Cửa sổ test T: W=180 ngày")
    ax.axvspan(test_end, cutoff, color="#d8e2f1", alpha=0.6, label="Sau cửa sổ T đến DATA_CUTOFF")
    ax.axvline(test_start, color="#b42318", linewidth=2)
    ax.axvline(cutoff, color="#202939", linewidth=2, linestyle="--")
    ax.axvline(last_test_t, color="#b7791f", linewidth=1.3, linestyle=":")
    ax.axvline(label_end, color="#315e9e", linewidth=1.5, linestyle="--")
    ax.axvline(label_asof, color="#6b4c9a", linewidth=1.5, linestyle="--")
    ax.annotate("test_start\n2025-10-22", (test_start, 0.9), xytext=(test_start, 1.08), ha="center",
                arrowprops={"arrowstyle": "-", "color": "#b42318"}, fontsize=9)
    ax.annotate("T cuối test\n2026-04-19", (last_test_t, 0.68), xytext=(date(2026, 3, 1), 1.06), ha="center",
                arrowprops={"arrowstyle": "-", "color": "#b7791f"}, fontsize=9)
    ax.annotate("hết N=180\n2026-10-16", (label_end, 0.47), xytext=(date(2026, 6, 1), 0.98), ha="center",
                arrowprops={"arrowstyle": "-", "color": "#315e9e"}, fontsize=9)
    ax.annotate("hết L=7 / label_asof\n2026-10-23", (label_asof, 0.28), xytext=(date(2026, 8, 1), 0.82), ha="center",
                arrowprops={"arrowstyle": "-", "color": "#6b4c9a"}, fontsize=9)
    ax.annotate("DATA_CUTOFF (loại trừ)\n2026-10-24", (cutoff, 0.05), xytext=(date(2026, 9, 10), 0.66), ha="center",
                arrowprops={"arrowstyle": "-", "color": "#202939"}, fontsize=9)
    ax.text(start, 0.07, "analysis_start / bắt đầu kinh doanh\n2024-04-01", ha="left", fontsize=9)
    ax.set_ylim(0, 1.25)
    ax.set_xlim(start, cutoff + timedelta(days=20))
    ax.set_yticks([])
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.tick_params(axis="x", rotation=25)
    ax.set_title("Ngày 1 — sơ đồ thời gian theo split đã khóa", loc="left", fontsize=15, weight="bold")
    ax.set_xlabel("Thời gian (ngày địa phương Asia/Ho_Chi_Minh)")
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.19), ncol=3, frameon=False, fontsize=9)
    fig.text(0.09, 0.045,
             "Chống rò rỉ: (1) EDA phát triển chỉ dùng ngày [2024-04-01, 2025-10-22).  (2) Đặc trưng tại T chỉ dùng thông tin có trước/đến T; nhãn nhìn về (T,T+N].\n"
             "(3) L=7 là đệm chờ cập nhật hoàn/trạng thái trước khi chốt nhãn; DATA_CUTOFF bao phủ đến 2026-10-23.\n"
             "Lưu ý quy ước đã khóa: N=180 là chân trời nhãn; W=180 là cửa sổ ngày T của test. Độ dài lookback đặc trưng chưa được chốt; test chưa mở/nhãn test chưa nạp.",
             fontsize=9, va="bottom")
    fig.savefig(out, dpi=170, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    if (ROOT / "outputs" / "metrics" / "test_opened.lock.json").exists():
        raise SystemExit("Refusing to rebuild pre-test Day 1 artifacts after the one-time test lock exists.")
    rows = build_gap_csv()
    build_timeline()
    print(f"Wrote development-only monthly gap counts: {len(rows)} months")
    print("Wrote outputs/figures/split_timeline.png")
