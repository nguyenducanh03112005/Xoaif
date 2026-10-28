# Trạng thái hiện tại

Repo hiện chứa pipeline phân tích Pancake POS, kho DuckDB cục bộ, kết quả aggregate, dashboard offline, báo cáo và tài liệu bảo vệ.

## Có thể sử dụng

- Mở dashboard từ outputs aggregate.
- Sinh lại CSV dữ liệu mẫu tổng hợp.
- Chạy nhánh hậu kiểm an toàn; do holdout đã mở, runner không fit lại mô hình và không gọi evaluator.
- Đọc báo cáo, kết quả, demo và Q&A theo hướng dẫn dự án.

## Kết luận phân tích

- Retention 180 ngày: 10,40% trên cohort đủ thời gian theo dõi.
- K-Means K=2: mô tả chủ yếu nhóm mua một lần và mua lặp lại; chưa xác nhận ý nghĩa kinh doanh.
- Mua lại: các baseline đơn giản không bị mô hình đầy đủ vượt ổn định; chưa chọn mô hình triển khai.
- Giỏ hàng: association chỉ mô tả đồng xuất hiện; một trong 24 cặp qua bộ lọc DEV chặt.
- Phản hồi: chưa đủ nhãn đáng tin để phân loại.
- Chưa có giá vốn nên không tính được lợi nhuận combo.

## Chưa hoàn thành

Cần chủ dự án cung cấp/duyệt giá vốn theo ngày, nguồn phản hồi có quyền sử dụng, nhãn/person chịu trách nhiệm, mục tiêu hành động và ngân sách, chính sách giữ/xóa raw cùng rubric/thời lượng chính thức. Cách xử lý từng việc nằm trong PROJECT_GUIDE mục 7.

Bắt đầu tại [PROJECT_GUIDE.md](PROJECT_GUIDE.md). Để chuẩn bị bảo vệ, dùng [DEFENSE_GUIDE.md](DEFENSE_GUIDE.md).
