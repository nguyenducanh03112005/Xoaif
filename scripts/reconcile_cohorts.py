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


def _read_preflight() -> tuple[int, str]:
    with (ROOT / "outputs/tables/eligibility_preflight.csv").open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    row = next(row for row in rows if row["candidate"] == "N180")
    return int(row["eligible_customers"]), row["test_start"]


def main() -> int:
    db = ROOT / "data/restricted/xoaif_dev.duckdb"
    con = duckdb.connect(str(db), read_only=True)
    total, status3, other, customers = con.execute("""
        SELECT COUNT(*),
               COUNT(*) FILTER (WHERE status_code = 3),
               COUNT(*) FILTER (WHERE status_code <> 3),
               COUNT(DISTINCT customer_key) FILTER (
                   WHERE status_code = 3 AND customer_key IS NOT NULL
               )
        FROM fact_orders
    """).fetchone()
    con.close()

    total, status3, other, customers = map(int, (total, status3, other, customers))
    if not validate_order_funnel(total, status3, other):
        raise ValueError("DEV order funnel does not reconcile")
    preflight, preflight_date = _read_preflight()
    scoring = json.loads((ROOT / "outputs/metrics/day2_segmentation.json").read_text(encoding="utf-8"))["customer_count"]

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

## Kết quả đối soát

- Phễu đơn khớp: {total:,} = {status3:,} status 3 + {other:,} status khác 3.
- Không được trừ số khách khỏi số đơn. Ba cohort khách 5.499, 5.174 và 5.169 không tạo thành funnel đã xác minh.
- 5.174 được tính trực tiếp từ warehouse DEV. 5.499 là preflight từ snapshot ở candidate `{preflight_date}`. 5.169 là cohort scoring sau quy tắc tiền xử lý riêng. Đơn vị của cả ba là khách, nhưng nguồn, mốc và điều kiện khác nhau.
- **Phần chênh lệch 5.499 / 5.174 / 5.169 chưa giải thích được.** Không có bảng cầu nối aggregate cho phép phân rã overlap/exclusive mà không dựng danh sách khách. Kho DEV cũng không chứa cột phân loại quà; vì thế giả thuyết quy tắc quà không thể được định lượng từ kho này.
- Đã loại trừ cách diễn giải rằng 5.499, 5.174, 5.169 là chuỗi giảm đơn giản: hai số đầu đều là khách, không phải số đơn; preflight và DEV/scoring dùng nguồn hoặc quy tắc khác nhau. Chưa thể xác định liệu khác biệt nguồn, ngày chốt hay bộ lọc quà có giải thích độ lớn chênh lệch.

Không gỡ ghi chú chênh lệch cohort khỏi báo cáo nhất quán vì quan hệ giữa ba tập chưa khớp bằng chứng aggregate.
"""
    (ROOT / "docs/cohort_reconciliation.md").write_text(report, encoding="utf-8")
    print(f"Order funnel reconciled: {total} = {status3} + {other}; customer cohort gap remains unexplained.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
