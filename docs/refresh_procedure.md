# Quy trình làm mới dữ liệu theo lô

Quy trình này mô tả lần refresh thủ công theo snapshot. Nó không được chạy như một phần của bàn giao.

1. **Extractor:** dùng client GET-only hiện có để lấy các trang nguồn theo cửa sổ đã duyệt; không ghi key vào repo. API hiện không cung cấp snapshot token, vì vậy quá trình nhiều trang không bảo đảm ảnh chụp đồng thời và không phải real-time.
2. **Manifest/checksum:** hoàn tất snapshot vào thư mục riêng; xác nhận số trang, tổng bản ghi, mốc thời gian và checksum với manifest trước khi sử dụng. Dừng nếu checksum hoặc số lượng không khớp.
3. **DuckDB:** chạy bước build warehouse đã khóa trên snapshot đã xác minh; kiểm tra schema, khoảng ngày, khóa HMAC và các tổng hợp chất lượng. Không ghi đè warehouse hiện hành khi xác minh thất bại.
4. **Aggregate:** chạy các builder đã duyệt cho bảng/metric aggregate. Không đưa khóa khách, dữ liệu đơn, địa chỉ hoặc văn bản tự do vào deliverables; ẩn/gộp ô có n < 5.
5. **Kiểm tra:** chạy `scripts/run_all.py` trong môi trường dự án với `PYTHONDONTWRITEBYTECODE=1`; kiểm tra lock, pytest, PII và dashboard smoke. Review diff và các artifact trước khi tạo commit.

Refresh phải có ngày chốt và manifest riêng. API không có snapshot token, nên không thể xem kết quả là luồng real-time hay snapshot nguyên tử; cần lưu giới hạn này trong báo cáo mỗi lần refresh.
