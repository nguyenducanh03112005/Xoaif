# Đăng ký trước F1 — thống nhất sự kiện mua lại

- **Phạm vi:** chỉ DEV, khám phá, chưa xác nhận ngoài mẫu; dùng `load_dev_orders()` hiện hành (status 3, không quà, local date < 2025-10-22). Không đọc test raw/nhãn/hành vi.
- **Định nghĩa thống nhất:** khách mua lại nếu có đơn status 3 không quà với **ngày địa phương lớn hơn ngày địa phương của đơn đầu hợp lệ**. Đơn tách cùng ngày không tính là mua lại. Đếm riêng số khách/đơn tách cùng ngày.
- **Phân tích cố định:** tái tính Kaplan–Meier 30/60/90/180 ngày sau khi loại sự kiện cùng ngày; retention tháng mua đầu theo logic cũ; so sánh hai định nghĩa cạnh nhau với A1 cũ, bảng first-basket A2 và nhãn WP5. Không thay đổi nguồn, horizons, cohort maturity, bootstrap khách 2.000, seed 20261028.
- **Câu hỏi:** chênh Kaplan–Meier ngày 30 với retention ngày 30 giải thích được bao nhiêu bởi cùng-ngày và bao nhiêu bởi cohort/mẫu số khác nhau?
- **Đầu ra:** báo cáo so sánh, aggregate metric/table mới; giữ các file và số A1/A2/WP5 cũ nguyên vẹn. Mọi số có n/đơn vị/cohort và CI nếu ước lượng chính.
- **Giới hạn:** KM theo khách đầu tiên theo thứ tự ngày; ngày địa phương đồng nhất tạo ties. Không kết luận nhân quả. Kiểm tra không đổi file khóa trước/sau.
- **Mã nguồn:** script mới `scripts/analyze_repeat_definition_f1.py`; metric cũ được đọc từ artifact đã commit; không ghi ID khách.
