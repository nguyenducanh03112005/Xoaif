# Quy trình làm mới dữ liệu theo lô

Chu kỳ đề xuất là tạo snapshot mỗi tuần. Quy trình này là hướng dẫn vận hành; không chạy extractor hay refresh như một phần của bàn giao.

1. **Snapshot mới:** dùng client GET-only đã duyệt; tạo thư mục riêng có timestamp. Không ghi key vào repo. API không có snapshot token và chưa khảo sát lọc theo thời gian cập nhật; snapshot nhiều trang không bảo đảm ảnh chụp đồng thời.
2. **Giữ và so sánh:** không ghi đè/xóa snapshot cũ. Kiểm tra manifest/checksum, số trang, tổng đơn và mốc thời gian. So manifest với lần trước, gồm tổng đơn và số đơn có thay đổi status; điều tra khác biệt trước khi dùng snapshot.
3. **DuckDB:** chạy bước build warehouse đã khóa trên snapshot mới đã xác minh; kiểm tra schema, khoảng ngày, khóa HMAC và tổng hợp chất lượng. Không ghi đè warehouse hiện hành khi xác minh thất bại.
4. **Aggregate:** chạy các builder đã duyệt cho bảng/metric aggregate. Không đưa khóa khách, dữ liệu đơn, địa chỉ hoặc văn bản tự do vào deliverables; ẩn/gộp ô có n < 5.
5. **Kiểm tra:** chạy `scripts/run_all.py` trong môi trường dự án với `PYTHONDONTWRITEBYTECODE=1`; kiểm tra lock, pytest, PII và dashboard smoke. Review diff và artifact trước commit.
6. **Huấn luyện riêng:** không gắn tự động với refresh tuần. Đánh giá huấn luyện lại theo tháng hoặc khi đủ dữ liệu; cần rolling-origin và amendment mới. Không mở lại test cũ.

Nhóm chọn snapshot bất biến để tái lập. API cho phép lấy đơn mới nên gần real-time khả thi; chưa khảo sát lọc theo thời gian cập nhật; chưa tự động hóa trong bản nộp. API không có snapshot token; status hiện tại không phải lịch sử trạng thái; split/test/cohort khóa bằng hash và mô hình chưa có tín hiệu xác nhận.

Không thể tính số đơn/ngày đáng tin cậy từ 12.011 đơn: `day1_analysis_start_profile.json` không cung cấp khoảng ngày tối thiểu/tối đa cho toàn snapshot. Không dùng riêng khoảng DEV hoặc 476 đơn bán thử làm mẫu số thay thế.
