# Đăng ký trước F5 — cây động lực doanh thu và kịch bản độ nhạy

- **Phạm vi:** exploratory DEV-only, chưa xác nhận ngoài mẫu; dùng `load_dev_orders()` và đơn status 3 không quà, local date<2025-10-22. Không đọc test raw/labels.
- **Cohort cơ sở:** khách mua đầu trong các tháng đủ 180 ngày; định nghĩa mua lại là ngày địa phương sau ngày đơn đầu. Tính doanh thu ghi nhận 180 ngày, số đơn ở ngày sau, AOV các đơn đó và CLV mô tả; bootstrap 2.000 lần theo khách, seed 20261028. Tháng không đủ 180 ngày bị loại khỏi mô hình cơ sở.
- **Tornado cơ học cố định:** (1) số khách mới +10%; (2) AOV +5%; (3) repeat rate +1/+3/+5 điểm phần trăm, mỗi khách tăng thêm giả định tạo một đơn ở AOV cơ sở; (4) nhóm high-value khóa theo A1 RFM (nhóm “giá trị cao” theo ngưỡng monetary p90 DEV 830.000₫), trong phần khách đủ 180 ngày: giả định giữ thêm 5 điểm phần trăm khách, mỗi khách giữ lại tạo doanh thu bằng CLV180 quan sát của nhóm high-value nếu n≥30. Tất cả chỉ là giả định minh họa, không dự báo/không phải lợi nhuận.
- **Phân rã:** 180-day revenue = eligible new customers × mean 180-day revenue/customer; per-customer value = AOV × orders/customer. Cũng tính tỷ trọng doanh thu đơn đầu trên giá trị 180 ngày, theo cùng customer bootstrap.
- **Kênh thu hút:** dùng `channel_behavior_dev.csv` đã aggregate; chỉ phần có nguồn kênh, coverage theo A3 là 62,64%, n<30 không kết luận. Kênh được xem là trường đơn đầu gán cho khách, không phải bằng chứng đóng góp nhân quả.
- **Số phép so sánh:** 12 tháng đủ maturity theo cohort CLV; 4 scenario classes, repeat-rate có 3 mức; 3 nhóm channel rows đã lưu. Không tối ưu/tìm ngưỡng.
- **Đầu ra:** monthly drivers, tornado rows với CI bootstrap theo khách, channel table, báo cáo/canonical numbers. Giả định tách khỏi quan sát; không tính lợi nhuận/ROI.
