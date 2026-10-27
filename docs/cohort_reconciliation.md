# Đối soát cohort (aggregate-only)

Ngày chạy: 2026-10-27. Kho DuckDB được mở `read_only=True`; truy vấn chỉ trả số đếm aggregate, không xuất khóa hay bản ghi.

| Bước / cohort | Số | Đơn vị | Định nghĩa, nguồn |
|---|---:|---|---|
| DEV hiệu dụng | 6,517 | đơn | `2024-04-01 <= local_date < 2025-10-22`; warehouse `fact_orders`. |
| Status 3 DEV | 6,400 | đơn | `status_code=3` trong DEV. |
| Status khác 3 DEV | 117 | đơn | `status_code<>3` trong DEV. |
| Khách có status 3 DEV | 5,174 | khách | Distinct customer key không thiếu, status 3; tính aggregate trực tiếp trong warehouse. |
| Eligibility preflight N=180 | 5,499 | khách | Candidate `2025-10-22` trong `outputs/tables/eligibility_preflight.csv`; snapshot và định nghĩa preflight riêng. |
| Cohort scoring đã freeze | 5,169 | khách | `outputs/metrics/day2_segmentation.json`; pipeline scoring áp dụng quy tắc loại đơn quà đã khóa. |

## Đếm distinct theo điều kiện trong DuckDB

| Điều kiện (khách có khóa) | Số distinct | Diễn giải |
|---|---:|---|
| Khách distinct trên toàn bộ DEV | 5,174 | Toàn bộ `fact_orders` không thiếu customer key. |
| Có ít nhất một đơn DEV status 3 | 5,174 | Cohort DEV; mọi hàng kho nằm trong `[2024-04-01, 2025-10-22)`. |
| Có ít nhất một đơn DEV status khác 3 | 0 | Trong số khách có khóa. |
| Có status 3 và status khác 3 (giao nhau) | 0 | Giao theo customer key; chỉ số count trả ra, không xuất key. |
| Status 3 trước `analysis_start` trong warehouse | 0 | Bằng 0 vì warehouse đã cắt từ `2024-04-01`; không đo được khách chỉ có lịch sử trước mốc này. |
| Status 3 từ T trở đi trong warehouse | 0 | Bằng 0 vì warehouse DEV kết thúc trước T. |
| Đơn status 3 thiếu customer key | 286 đơn distinct | Không thể gọi là số khách distinct; khóa NULL không phân biệt được cá thể. |
| Có status 3 không quà / bị loại do quà | Không tính được | Schema không có cờ quà hay trường tiền để xác định điều kiện. |

## Cầu số học và giới hạn xác minh

| Bước | Số khách | Delta | Điều kiện dự kiến | Được đếm bằng điều kiện trong kho? |
|---|---:|---:|---|---|
| Eligibility preflight N=180 | 5,499 | — | Status 3, có ID, trước `2025-10-22` trên snapshot; không áp dụng lower bound `analysis_start`. | Aggregate preflight đã lưu; không có cohort key trong warehouse để nối trực tiếp. |
| Sau lower bound vào DEV | 5,174 | −325 | Bỏ người chỉ có giao dịch status 3 trước `2024-04-01`. | Không. Warehouse bắt đầu tại lower bound nên không chứa nhóm bị loại; 0 distinct pre-analysis trong kho. Delta là hiệu số aggregate, chưa xác nhận nguyên nhân theo khách. |
| Scoring đã freeze | 5,169 | −5 | Loại khách không còn đơn status 3 không quà trước T. | Không. DuckDB không có trường quà; chênh lệch delta không chứng minh số khách quà-only. |

Số học khớp: 5,499 − 325 − 5 = 5,169. Tuy vậy, hai delta chưa được xác nhận bằng COUNT DISTINCT theo đúng điều kiện loại, và các giao nhau với điều kiện quà không có trong schema. **phần dư chưa giải thích: 330** (tổng các delta chưa được gán nguyên nhân bằng truy vấn trên kho). Không được trình bày đây là funnel đã xác minh.

Phễu đơn riêng khớp: 6,517 = 6,400 status 3 + 117 status khác 3.

Không gỡ ghi chú chênh lệch cohort khỏi báo cáo nhất quán: cầu số học đóng nhưng cầu điều kiện/intersection chưa được xác minh.
