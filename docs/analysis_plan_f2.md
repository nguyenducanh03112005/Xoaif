# Đăng ký trước F2 — dịch chuyển tỷ lệ nền trong DEV

- **Phạm vi:** khám phá, chưa xác nhận ngoài mẫu; chỉ DEV status 3 không quà qua `load_dev_orders()`. Không truy cập test raw/nhãn/hành vi.
- **Cohort cố định:** tỷ lệ mua lại 180 ngày theo tháng mua đầu chỉ cho cohort-month đủ 180 ngày đến trước DEV end (tháng kết thúc +180 < 2025-10-22), định nghĩa sự kiện ngày địa phương sau đơn đầu. WP5/WP5b: dùng đúng outer folds WP5; tính prevalence trên train và validation từng fold từ snapshot labels đã tạo DEV-only.
- **Phép mô tả xu hướng:** OLS slope của tỷ lệ cohort-month theo thứ tự tháng, đơn vị điểm phần trăm/tháng; CI percentile bootstrap 2.000 lần, seed 20261028, resample khách trong từng cohort month và tính lại các tỷ lệ/slope. Không kiểm định nhiều dạng xu hướng và không chọn điểm gãy.
- **Số phép so sánh:** một xu hướng theo cohort-month; năm cặp train-vs-validation prevalence (WP5 fold, WP5b chung fold); không kiểm định giả thuyết/nhân quả.
- **Đầu ra:** bảng đủ cohort n/số dương/tỷ lệ; bảng tỷ lệ train/validation theo fold WP5 và WP5b; metric trend và CI; cập nhật giải thích cạnh tranh với class_weight trong cohort mismatch report.
- **Giới hạn:** cohort maturity thay đổi mẫu số; trend tuyến tính chỉ tóm tắt, không chứng minh dịch chuyển nguyên nhân. Prevalence train khác validation phản ánh thiết kế thời gian và có thể ảnh hưởng calibration pooled. Mọi nhãn chỉ DEV.
