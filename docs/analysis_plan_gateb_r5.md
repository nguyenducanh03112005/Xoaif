# Đăng ký trước Gate B R5 — chiến lược và artifact DEV

- **Ngày:** 2026-10-28. Commit kế hoạch này phải có trước khi tạo artifact, ước lượng hệ số hoặc tính metric R5.
- **Phạm vi:** chỉ DEV multi-snapshot 21.638 hàng / 3.508 khách, 12 mốc T, N=180, L=7; outcome định nghĩa như WP5. Cấm đọc HO2/test. Các fit bên dưới chỉ tạo bộ chấm cố định chuẩn bị cho một phép đánh giá tương lai, không đánh giá kết quả HO2.
- **Quy tắc chung:** không chọn đặc trưng, tham số hay ngưỡng sau fit. Lưu hash artifact, mã và tên/cột đặc trưng. Không ghi model binary vào Git.

## Tập chiến lược đã định

| Chiến lược | Trạng thái và cách chấm đã đăng ký |
|---|---|
| S1 | Eligible, quy tắc cố định: score=1 nếu `frequency>=2`, nếu không score=0. |
| S3 | Chọn phương án A: tạo một artifact final-fit từ toàn bộ DEV multi-snapshot dùng `MODEL_FEATURES` của WP5 v3, median imputer + StandardScaler + `DecisionTreeClassifier(max_depth=3,min_samples_leaf=50,random_state=20261028)`. Cùng quy tắc áp dụng v3. Lý do: WP5b chỉ fit cây trong từng outer fold để chấm OOF; không có một cây final-fit duy nhất. |
| S6 | Eligible theo cùng phương án A: ánh xạ tần suất/recency fit từ toàn bộ DEV multi-snapshot bằng `_train_mapping` WP5c không sửa đổi, gồm ngưỡng gộp `MIN_TRAIN=100`; đóng băng map và score rate. Bảng `repurchase_wp5c_train_rates.csv` là fold-specific, không phải quần thể full DEV. |
| D-005 | Eligible bằng artifact DEV đã đóng băng `outputs/models/day2_dev_final_model.joblib`; không fit lại, đối chiếu SHA-256 với amendment 04. |
| v2 | Eligible bằng artifact DEV đã đóng băng `outputs/models/repurchase_features_v2.joblib`; không fit lại, đối chiếu SHA-256 với metadata v2. |
| v3 | Chọn phương án A như S3: final-fit trên toàn bộ DEV multi-snapshot, `MODEL_FEATURES`, median imputer + StandardScaler + LogisticRegression `C=10`, `class_weight="balanced"`, `solver="lbfgs"`, `max_iter=2000`, `random_state=20261028`. |
| Recency-only / frequency-only | Baseline mô tả: mỗi biến riêng fit một LogisticRegression C=10, balanced, lbfgs, max_iter=2000, seed 20261028 trên toàn bộ DEV multi-snapshot; preprocessing median + StandardScaler. Sau fit, hướng xếp hạng được khóa đúng bằng dấu hệ số đã học: score là giá trị chuẩn hóa nhân dấu hệ số (không dùng xác suất). Ghi hệ số, dấu và hash bảng đặc tả vào result. Không là giả thuyết, không artifact chấm độc lập. |

## Metric và số phép so sánh

- Tập chấm cuối: S1, S3, S6, D-005, v2, v3, recency-only, frequency-only; 8 chiến lược cố định. D-005 được báo riêng với hai baseline đơn biến bằng chênh lệch mô tả, không chọn mô hình.
- Lưu nguồn fit DEV, cỡ mẫu, số khách, số dương, danh sách feature, tham số, SHA-256 artifact; với baseline đơn biến lưu dấu hệ số thực tế. Tất cả chỉ là định nghĩa chấm, chưa có kết quả HO2.
- Không đánh giá metric mới trên test/HO2 ở gói R5. Hạng mục này không thay D-005 là mô hình chính, không ước lượng uplift hay nhân quả.

## Giới hạn

S3/S6/v3 fit cả DEV để tạo artifact cuối, do đó không được dùng metric in-sample DEV của chúng như đánh giá tổng quát. D-005/v2 là artifact của các quy trình lịch sử khác nhau; khác biệt hiệu năng về sau chỉ có tính mô tả trên cùng HO2 nếu có phép mở riêng. Bảng rate S6 là quy tắc nhóm, không xác suất đã hiệu chuẩn.
