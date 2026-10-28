# Đăng ký trước WP5b — chiến lược mua lại DEV

- **Trạng thái:** đăng ký trước, trước mọi fit/đánh giá mới; khám phá, chưa xác nhận ngoài mẫu.
- **Cohort:** cùng mẫu snapshot tháng đa mốc và temporal folds đã tạo ở WP5 (`build_multisnapshot_samples`, `build_multisnapshot_folds`), DEV status 3 không quà; N=180, L=7; điều kiện nhãn train trưởng thành `train_T + N + L < validation_T`. Không đọc test raw/nhãn/hành vi và không chạy evaluator test.
- **Mục tiêu:** so sánh năm chiến lược cố định về thứ hạng và calibration, tập trung giả thuyết `class_weight="balanced"` làm xác suất v3 lệch khỏi prevalence. Không thay D-005.

## Chiến lược cố định

1. **S1 — luật tần suất:** điểm 1 nếu `frequency >= 2`, còn lại 0.
2. **S2 — luật kết hợp tần suất và recency:** mỗi fold chọn đúng một ngưỡng recency trong `{30, 60, 90, 180}` ngày, dùng các snapshot đã trưởng thành trong train của fold làm các inner validation theo thời gian; chọn ngưỡng có AP trung bình fold lớn nhất, hòa chọn ngưỡng nhỏ hơn. Sau đó điểm validation là 1 nếu `frequency >= 2` và `recency_days <= ngưỡng`. Nếu không có inner fold hợp lệ thì ghi thất bại cho fold; không chọn bằng outer validation.
3. **S3 — cây nông:** `DecisionTreeClassifier(max_depth=3, min_samples_leaf=50, random_state=20261028)`, đặc trưng v3 cố định, preprocessing fit train-only; in cấu luật IF–THEN từ từng outer fit. Không tuning.
4. **S4 — Logistic Regression không cân bằng lớp + sigmoid:** solver `lbfgs`, `C=10`, `max_iter=2000`, seed 20261028, pipeline imputer median + StandardScaler fit trong inner train. Dùng fold thời gian bên trong outer train để lấy score OOF; fit sigmoid logistic một biến trên các score OOF và nhãn train tương ứng. Outer validation được chấm bởi base model từ inner-train và sigmoid fit trên inner OOF; không dùng outer validation để fit. Nếu outer train không có đủ inner folds hoặc score OOF không có hai lớp, ghi thất bại, không thay bằng cách fit khác.
5. **S5 — Logistic Regression v3 tham chiếu:** tái chạy đúng đặc trưng, preprocessing và tham số WP5 (C=10, `class_weight="balanced"`, lbfgs, 2000 iterations, seed 20261028), cùng outer fold.

## Chọn ứng viên (chỉ đề xuất kiểm chứng sau này)

Ứng viên là chiến lược có **AP trung bình theo outer fold cao nhất** trong S1–S5 có tỷ lệ mua lại theo 10 decile điểm giảm đơn điệu từ decile cao nhất xuống thấp nhất (đồng hạng cho phép); baseline hằng số không đủ điều kiện. Nếu không có chiến lược đạt tính đơn điệu, không chọn ứng viên. Hòa AP trong 0,001 chọn theo thứ tự đơn giản S1, S2, S3, S4, S5. Quy tắc chỉ dùng DEV temporal CV và không tự cho phép HO2.

## Metric, bất định, phép so sánh

- Mỗi chiến lược báo theo từng outer fold và pooled OOF riêng: ROC-AUC, AP, prevalence, Brier; n, số dương và số khách.
- Bảng pooled và theo fold cho cumulative gain/lift theo decile, precision@5/10/20%; top-k dùng `ceil(k*n)`.
- Calibration báo Brier, calibration intercept/slope (logit nhãn theo logit xác suất, pooled OOF; theo fold khi đủ cả hai lớp và đủ biến thiên điểm), observed/predicted theo decile. Điểm 0/1 của S1/S2 không diễn giải slope như xác suất đã hiệu chỉnh.
- Tính monotonicity bằng số vi phạm liền kề trên tỷ lệ mua lại decile, điểm cao hơn phải có tỷ lệ không thấp hơn decile dưới; báo thẳng trường hợp hòa do điểm rời rạc.
- CI 95% pooled bằng bootstrap cụm khách 2.000 lượt, seed 20261028; giữ mọi snapshot khách được lấy cùng nhau. Không tính CI cho luật S2 chọn ngưỡng nếu outer folds quá ít để tái tạo inner-selection ổn định; mọi thất bại được lưu.
- **Số phép so sánh đã đăng ký:** 5 chiến lược trên cùng outer folds; 4 chiến lược S1–S4 so với S5 về AP (mô tả, không kiểm định xác nhận); 4 ngưỡng S2 trong inner CV; 4 so sánh chiến lược đạt monotonicity theo quy tắc chọn. Không thêm subgroup, feature, threshold hay model sau khi xem kết quả.

## Giới hạn và kết luận

Chỉ DEV; kết quả là “khám phá, chưa xác nhận ngoài mẫu”. Kết quả OOF calibration S4 không được xem là kiểm chứng độc lập do dùng inner temporal CV của cùng DEV. Chênh metric không suy ra nhân quả, lợi nhuận hoặc hiệu quả chiến dịch. Calibration của S4 chỉ so với S5 cùng outer validation; Brier của các điểm thô S1/S2/S3 không được xem là đối chiếu công bằng với xác suất hiệu chỉnh. D-005 tiếp tục là mô hình chính bất kể kết quả.
