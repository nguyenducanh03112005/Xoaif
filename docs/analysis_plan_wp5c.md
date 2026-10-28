# Đăng ký trước WP5c — S6 bảng tần suất mua lại DEV

- **Phạm vi:** khám phá DEV-only, chưa xác nhận ngoài mẫu. Dùng cùng snapshot/folds WP5, N=180, L=7, cùng định nghĩa nhãn cũ đã đăng ký cho WP5 (không đổi metric WP5 lịch sử); không dùng test raw/labels/behavior và không sửa D-005.
- **Ô cố định:** frequency `{1, 2, >=3}` × recency days `{<=30, 31–90, 91–180, >180}`. Mỗi validation score là tỷ lệ mua lại trong ô sau khi dựng biên ô chỉ từ fold train.
- **Quy tắc gộp khi n_train<100:** trước hết trong cùng frequency, gộp recency band có n nhỏ nhất với band kề có n lớn hơn; nếu hòa chọn band cũ hơn. Lặp cho tới mọi ô ≥100 hoặc chỉ còn một recency band. Nếu ô còn <100, gộp frequency stratum kề có n lớn hơn trong band đó; nếu hòa chọn frequency thấp hơn. Không lấy validation để chọn/gộp. Nếu ô cuối vẫn <100, gộp vào toàn bộ train reference rate và đánh dấu fallback. Ghi mapping/n mỗi fold.
- **Tỷ lệ ô:** empirical train positive/n after merge, không smoothing; nếu n_train=0 dùng prevalence toàn train. Brier/calibration dùng score này.
- **Metric:** cùng 5 outer folds: AP, ROC-AUC, precision@5/10/20%, lift top-decile, gain/decile, Brier, calibration-in-the-large và observed vs predicted theo ô; metric fold và pooled tách riêng. CI pooled bootstrap theo khách 2.000, seed 20261028. Nêu rõ fold-specific mapping khiến pooled score là OOF.
- **Số phép so sánh:** một chiến lược S6, 5 folds, 12 starting cells; không tuning, không xếp hạng/chọn ngưỡng.
- **Đầu ra:** rate table theo fold với n_train, positives, n_validation và mapping; summary metrics, deciles/top-k/calibration; cây mô tả bảng quy tắc để dùng trong kịch bản hòa vốn nếu được duyệt sau này.
- **Giới hạn:** ô hiếm gộp làm mất chi tiết; score là tỷ lệ lịch sử, không dự báo hay uplift. D-005 tiếp tục mô hình chính.
