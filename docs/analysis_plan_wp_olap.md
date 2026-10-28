# Đăng ký trước A4 — OLAP/DSS từ Kho DEV

- **Trạng thái:** đăng ký trước ngày 2026-10-28, trước khi chạy phân tích OLAP A4. Nhãn: khám phá, chưa xác nhận ngoài mẫu.
- **Kho vật lý:** DuckDB DEV `data/restricted/xoaif_dev.duckdb`, chỉ đọc. Không sửa/rebuild kho. Truy vấn `fact_orders`, `fact_order_items`, `dim_date`, `dim_order_status`, `dim_customer`, `dim_product`; xác minh schema và coverage trước khi tạo cuboid.
- **Enrichment tạm trong RAM:** `load_dev_orders()` date-gated chỉ DEV status 3 và cùng HMAC order key của kho; chỉ thêm doanh thu ghi nhận, trạng thái quà, kênh, tỉnh và dòng hàng cần thiết cho phân tích. `order_key` chỉ dùng để join trong RAM, không xuất. Không đọc test raw/labels/behavior và không ghi bản ghi enrichment ra đĩa.
- **Kỳ:** DEV `[2024-04-01, 2025-10-22)`. Nhóm khách dùng đúng sáu nhóm RFM và ngưỡng đã đăng ký ở A1; không tạo lại/đổi tên ngưỡng theo kết quả A4.
- **Suppression:** ô n<30 khách/đơn bị ẩn ở báo cáo; tỉnh có số đơn toàn DEV <30 gộp thành “Tỉnh khác (gộp)”; UNKNOWN giữ riêng và ghi tỷ lệ bao phủ. Không xuất order/customer/product key hoặc PII. Các bảng chỉ qua allowlist mới được commit.

## Cuboid và câu hỏi quyết định đã cố định

1. **Tháng × kênh × RFM action segment:** đếm đơn status 3 không quà, khách distinct trong cell, doanh thu ghi nhận; trả lời “kênh/nhóm nào đóng góp đơn và doanh thu ghi nhận theo tháng?”. Nhóm không có khóa khách nằm ở “Không phân khúc”; nhóm dưới 30 bị ẩn.
2. **Tháng × cỡ giỏ × RFM action segment:** cỡ giỏ là số product ID distinct sau bỏ dòng quà, bucket `1`, `2`, `3+`; measures như cuboid 1. Trả lời “giá trị ghi nhận tập trung ở giỏ nhỏ/lớn và nhóm nào?”. Không phân bổ doanh thu xuống sản phẩm.
3. **Tỉnh/thành DEV:** đơn status 3 không quà, doanh thu ghi nhận, khách distinct; province unknown riêng, tỉnh nhóm nhỏ gộp theo ngưỡng toàn kỳ. Trả lời “bao phủ địa lý đủ tin cậy để định tuyến hàng/giao nhận chưa?”. Không tạo lát cắt theo tỉnh nếu thiếu địa chỉ quá cao.
4. **Tháng × trạng thái (warehouse physical fact):** số đơn và khách có khóa theo `fact_orders`; không thêm doanh thu/giả định cho trạng thái ngoài status 3. Trả lời “khối lượng đơn theo trạng thái/tháng?”.

## OLAP thao tác và số so sánh

- Triển khai đúng các phép: roll-up (tháng→quý/năm; cỡ giỏ→tổng), drill-down (năm→quý→tháng), slice (chọn tháng hoặc nhóm RFM), dice (lọc đồng thời kênh và nhóm khách), pivot (đổi trục tháng/kênh hoặc tháng/cỡ giỏ). Các phép chạy trên bảng tạm đầy đủ trong RAM; suppression áp dụng sau phép tổng hợp cho màn hình/bảng xuất.
- Bốn cuboid, ba measure cốt lõi (orders, distinct customers, recognized revenue; status cuboid không có revenue), tất cả tháng DEV và mọi bucket đã cố định. Không kiểm định giả thuyết và không chọn tổ hợp đẹp. Dashboard không nằm trong gói A4.
- Nguồn `UNKNOWN` và tỉnh nhỏ chỉ để đánh giá chất lượng bao phủ; không diễn giải tỉnh thành nơi khách cư trú hay tiềm năng thị trường.
- Không có giá vốn nên doanh thu ghi nhận không phải lãi/lợi nhuận. Count khách không cộng được qua tháng vì khách có thể mua nhiều tháng; số tổng phải tính distinct ở cấp tổng.
