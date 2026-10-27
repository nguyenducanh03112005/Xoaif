# Đối soát cohort bằng đếm trực tiếp

Phạm vi: snapshot 20261024T052943Z; chỉ status 3 có local_date < T được đưa vào cohort A. Đếm ID khác biệt bằng HMAC chuẩn của dự án trong RAM; không in/lưu ID. DuckDB được mở read-only.

## Cầu nối khách

| Cohort/bước | Định nghĩa | Khách distinct | Đếm trực tiếp và đối chiếu |
|---|---|---:|---|
| A | >=1 đơn status 3, có ID, local_date < 2025-10-22; không cận dưới | 5.499 | khớp với preflight 5.499 |
| A − B | Chỉ có đơn status 3 trước 2024-04-01 | 325 | Trực tiếp từ set HMAC A trừ B; trong đó 325 có ít nhất một đơn thuộc 476 đơn bán thử 2022-06-04 đến 2022-09-21. |
| B | >=1 đơn status 3, ID không NULL, [2024-04-01, 2025-10-22) | 5.174 | khớp với DuckDB 5.174 |
| B bị loại | Mọi đơn status 3 DEV của khách đều là đơn quà theo Amendment 03 | 5 | Trực tiếp bằng cờ is_gift từ assess_order_money |
| Scoring | B trừ khách chỉ có status-3 order quà; customer ID hợp lệ và trước T | 5.169 | So với metric đóng băng 5.169: khớp |

Số học: 5.499 − 325 − 5 = 5.169. **phần dư chưa giải thích: 0**.

Giao điều kiện: A−B với 476 đơn bán thử = 325 khách. A−B với gift-only B = 0; hai nhóm nằm hai phía lower-bound nên rời nhau.

## Bộ lọc pipeline scoring chính

- status 3, ID không NULL, local_date trong [analysis_start,T), rồi giữ khách nếu có ít nhất một đơn không quà. COUNT DISTINCT trực tiếp cho thấy 5 khách B chỉ có đơn quà; còn 5.169.
- exclude_adjusted không bật trong cohort chính (chỉ dùng ở độ nhạy B); không loại thêm khách.
- Có dòng hàng không phải điều kiện tạo customer set; không loại khách thiếu item lines khỏi cohort scoring.
- Có 286 đơn status 3 DEV thiếu ID; đây là số đơn, không phải khách distinct. Số đơn quà status 3 DEV: 22.

## Kiểm tra cấu trúc DuckDB (không phải phát hiện hành vi)

- Đơn DEV: 6.517; status 3: 6.400; status khác 3: 117.
- Customer key NULL: status khác 3 117 đơn; status 3 286 đơn. Đây là kiểm kê cấu trúc kho. Có: builder chỉ tạo `customer_key` trong nhánh `status == 3`; đơn status khác 3 được giữ `customer_key=NULL` (xem `scripts/build_dev_warehouse.py`).
- Khách có status khác 3 trong kho: 0; giao khách status 3/status khác 3: 0. Các số 0 là kiểm tra cấu trúc kho, không phải phát hiện về hành vi.

Nguồn: docs/cohort_definitions.md; outputs/tables/eligibility_preflight.csv; outputs/metrics/day2_segmentation.json; COUNT DISTINCT read-only trong scripts/build_pretest_evidence.py; chính sách cohort ở scripts/prepare_day2.py và src/features/day2_data.py.
