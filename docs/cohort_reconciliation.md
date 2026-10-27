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

## Kết quả đối soát

- Phễu đơn khớp: 6,517 = 6,400 status 3 + 117 status khác 3.
- Không được trừ số khách khỏi số đơn. Ba cohort khách 5.499, 5.174 và 5.169 không tạo thành funnel đã xác minh.
- 5.174 được tính trực tiếp từ warehouse DEV. 5.499 là preflight từ snapshot ở candidate `2025-10-22`. 5.169 là cohort scoring sau quy tắc tiền xử lý riêng. Đơn vị của cả ba là khách, nhưng nguồn, mốc và điều kiện khác nhau.
- **Phần chênh lệch 5.499 / 5.174 / 5.169 chưa giải thích được.** Không có bảng cầu nối aggregate cho phép phân rã overlap/exclusive mà không dựng danh sách khách. Kho DEV cũng không chứa cột phân loại quà; vì thế giả thuyết quy tắc quà không thể được định lượng từ kho này.
- Đã loại trừ cách diễn giải rằng 5.499, 5.174, 5.169 là chuỗi giảm đơn giản: hai số đầu đều là khách, không phải số đơn; preflight và DEV/scoring dùng nguồn hoặc quy tắc khác nhau. Chưa thể xác định liệu khác biệt nguồn, ngày chốt hay bộ lọc quà có giải thích độ lớn chênh lệch.

Không gỡ ghi chú chênh lệch cohort khỏi báo cáo nhất quán vì quan hệ giữa ba tập chưa khớp bằng chứng aggregate.
