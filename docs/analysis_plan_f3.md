# Đăng ký trước F3 — bộ lọc khuyến nghị combo và bội so sánh

- **Phạm vi:** chỉ aggregate DEV đã tạo ở A2; không đọc raw/test; khám phá, chưa xác nhận ngoài mẫu. 24 combo giữ nguyên danh sách, rank và phép đo cũ.
- **Bộ lọc khuyến nghị mới:** combo chỉ qua sàng lọc mô tả khi đồng thời `dev_lift > 1`, `dev_kulczynski >= 0.5`, `dev_imbalance_ratio <= 0.5`. Đây là tiêu chí cân bằng đồng xuất hiện, không ngưỡng phổ quát/nhân quả; báo mỗi chỉ tiêu để người đọc thấy lý do qua/không qua. Giá trị NULL không qua.
- **Phân tích 77 sản phẩm giỏ đầu:** không thêm kiểm định hoặc chọn lại kết quả. Ghi số so sánh đã thử n=77, kỳ vọng khoảng 77×0,05=3,85 (xấp xỉ 4) kết quả dương giả nếu 5% kiểm định độc lập dưới giả thuyết không; phụ thuộc giữa sản phẩm khiến đây chỉ là cảnh báo gần đúng. Không hiệu chỉnh Benjamini–Hochberg vì chưa có họ p-value/kiểm định hợp lệ; ghi rõ không hiệu chỉnh và không gọi khác biệt “có ý nghĩa thống kê”.
- **Đầu ra:** bảng combo có cờ sàng lọc; báo cáo giữ hạng gốc, nêu PORTCARD phổ biến ở giỏ đầu (số từ A2 aggregate) và combo hạng 1 lift<1 không qua lọc.
- **Nguồn/số phép so sánh:** `outputs/tables/frozen_combo_supplement_dev.csv`; 24 cặp combo cố định và 77 sản phẩm giỏ đầu. Không phát sinh phép so sánh combo mới.
