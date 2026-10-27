"""Write an aggregate-only cohort comparison from the read-only DEV warehouse."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]


def validate_order_funnel(total_orders: int, status3_orders: int, other_orders: int) -> bool:
    """Check the order-level partition without mixing it with customer counts."""
    return total_orders == status3_orders + other_orders


def cohort_bridge_deltas(preflight: int, dev_status3: int, scoring: int) -> tuple[int, int, int]:
    """Return arithmetic deltas and the total delta not attributed to verified filters."""
    first = preflight - dev_status3
    second = dev_status3 - scoring
    return first, second, first + second


def _read_preflight() -> tuple[int, str]:
    with (ROOT / "outputs/tables/eligibility_preflight.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    row = next(row for row in rows if row["candidate"] == "N180")
    return int(row["eligible_customers"]), row["test_start"]


def main() -> int:
    db = ROOT / "data/restricted/xoaif_dev.duckdb"
    con = duckdb.connect(str(db), read_only=True)
    total, status3, other, all_customers, customers, other_status_customers, status3_other_overlap, pre_analysis_customers, post_T_customers, missing_id_status3_orders = con.execute("""
        WITH per_customer AS (
            SELECT customer_key,
                   BOOL_OR(status_code = 3) AS has_status3,
                   BOOL_OR(status_code <> 3) AS has_other_status,
                   BOOL_OR(status_code = 3 AND local_date < DATE '2024-04-01') AS has_pre_analysis_status3,
                   BOOL_OR(status_code = 3 AND local_date >= DATE '2025-10-22') AS has_post_T_status3
            FROM fact_orders
            WHERE customer_key IS NOT NULL
            GROUP BY customer_key
        )
        SELECT
            (SELECT COUNT(DISTINCT order_key) FROM fact_orders),
            (SELECT COUNT(DISTINCT order_key) FROM fact_orders WHERE status_code = 3),
            (SELECT COUNT(DISTINCT order_key) FROM fact_orders WHERE status_code <> 3),
            COUNT(DISTINCT customer_key),
            COUNT(DISTINCT customer_key) FILTER (WHERE has_status3),
            COUNT(DISTINCT customer_key) FILTER (WHERE has_other_status),
            COUNT(DISTINCT customer_key) FILTER (WHERE has_status3 AND has_other_status),
            COUNT(DISTINCT customer_key) FILTER (WHERE has_pre_analysis_status3),
            COUNT(DISTINCT customer_key) FILTER (WHERE has_post_T_status3),
            (SELECT COUNT(DISTINCT order_key) FROM fact_orders WHERE status_code = 3 AND customer_key IS NULL)
        FROM per_customer
    """).fetchone()
    con.close()

    total, status3, other, all_customers, customers, other_status_customers, status3_other_overlap, pre_analysis_customers, post_T_customers, missing_id_status3_orders = map(
        int,
        (total, status3, other, all_customers, customers, other_status_customers, status3_other_overlap, pre_analysis_customers, post_T_customers, missing_id_status3_orders),
    )
    if not validate_order_funnel(total, status3, other):
        raise ValueError("DEV order funnel does not reconcile")
    preflight, preflight_date = _read_preflight()
    scoring = json.loads((ROOT / "outputs/metrics/day2_segmentation.json").read_text(encoding="utf-8"))["customer_count"]
    preflight_delta, scoring_delta, unexplained_total = cohort_bridge_deltas(preflight, customers, scoring)

    report = f"""# Đối soát cohort (aggregate-only)

Ngày chạy: 2026-10-27. Kho DuckDB được mở `read_only=True`; truy vấn chỉ trả số đếm aggregate, không xuất khóa hay bản ghi.

| Bước / cohort | Số | Đơn vị | Định nghĩa, nguồn |
|---|---:|---|---|
| DEV hiệu dụng | {total:,} | đơn | `2024-04-01 <= local_date < 2025-10-22`; warehouse `fact_orders`. |
| Status 3 DEV | {status3:,} | đơn | `status_code=3` trong DEV. |
| Status khác 3 DEV | {other:,} | đơn | `status_code<>3` trong DEV. |
| Khách có status 3 DEV | {customers:,} | khách | Distinct customer key không thiếu, status 3; tính aggregate trực tiếp trong warehouse. |
| Eligibility preflight N=180 | {preflight:,} | khách | Candidate `{preflight_date}` trong `outputs/tables/eligibility_preflight.csv`; snapshot và định nghĩa preflight riêng. |
| Cohort scoring đã freeze | {scoring:,} | khách | `outputs/metrics/day2_segmentation.json`; pipeline scoring áp dụng quy tắc loại đơn quà đã khóa. |

## Đếm distinct theo điều kiện trong DuckDB

| Điều kiện (khách có khóa) | Số distinct | Diễn giải |
|---|---:|---|
| Khách distinct trên toàn bộ DEV | {all_customers:,} | Toàn bộ `fact_orders` không thiếu customer key. |
| Có ít nhất một đơn DEV status 3 | {customers:,} | Cohort DEV; mọi hàng kho nằm trong `[2024-04-01, 2025-10-22)`. |
| Có ít nhất một đơn DEV status khác 3 | {other_status_customers:,} | Trong số khách có khóa. |
| Có status 3 và status khác 3 (giao nhau) | {status3_other_overlap:,} | Giao theo customer key; chỉ số count trả ra, không xuất key. |
| Status 3 trước `analysis_start` trong warehouse | {pre_analysis_customers:,} | Bằng 0 vì warehouse đã cắt từ `2024-04-01`; không đo được khách chỉ có lịch sử trước mốc này. |
| Status 3 từ T trở đi trong warehouse | {post_T_customers:,} | Bằng 0 vì warehouse DEV kết thúc trước T. |
| Đơn status 3 thiếu customer key | {missing_id_status3_orders:,} đơn distinct | Không thể gọi là số khách distinct; khóa NULL không phân biệt được cá thể. |
| Có status 3 không quà / bị loại do quà | Không tính được | Schema không có cờ quà hay trường tiền để xác định điều kiện. |

## Cầu số học và giới hạn xác minh

| Bước | Số khách | Delta | Điều kiện dự kiến | Được đếm bằng điều kiện trong kho? |
|---|---:|---:|---|---|
| Eligibility preflight N=180 | {preflight:,} | — | Status 3, có ID, trước `{preflight_date}` trên snapshot; không áp dụng lower bound `analysis_start`. | Aggregate preflight đã lưu; không có cohort key trong warehouse để nối trực tiếp. |
| Sau lower bound vào DEV | {customers:,} | −{preflight_delta:,} | Bỏ người chỉ có giao dịch status 3 trước `2024-04-01`. | Không. Warehouse bắt đầu tại lower bound nên không chứa nhóm bị loại; {pre_analysis_customers} distinct pre-analysis trong kho. Delta là hiệu số aggregate, chưa xác nhận nguyên nhân theo khách. |
| Scoring đã freeze | {scoring:,} | −{scoring_delta:,} | Loại khách không còn đơn status 3 không quà trước T. | Không. DuckDB không có trường quà; chênh lệch delta không chứng minh số khách quà-only. |

Số học khớp: {preflight:,} − {preflight_delta:,} − {scoring_delta:,} = {scoring:,}. Tuy vậy, hai delta chưa được xác nhận bằng COUNT DISTINCT theo đúng điều kiện loại, và các giao nhau với điều kiện quà không có trong schema. **phần dư chưa giải thích: {unexplained_total}** (tổng các delta chưa được gán nguyên nhân bằng truy vấn trên kho). Không được trình bày đây là funnel đã xác minh.

Phễu đơn riêng khớp: {total:,} = {status3:,} status 3 + {other:,} status khác 3.

Không gỡ ghi chú chênh lệch cohort khỏi báo cáo nhất quán: cầu số học đóng nhưng cầu điều kiện/intersection chưa được xác minh.
"""
    (ROOT / "docs/cohort_reconciliation.md").write_text(report, encoding="utf-8")
    print(f"Aggregate counts only: customers={customers}; status3/other overlap={status3_other_overlap}; bridge arithmetic residual={unexplained_total} remains unverified by condition.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
