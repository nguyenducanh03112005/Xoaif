# Đăng ký trước phân tích WP5 — mô hình mua lại DEV

- **Trạng thái:** đăng ký trước; tạo ngày 2026-10-28, trước khi chạy phân tích WP5 mới.
- **Phạm vi:** khám phá DEV, chưa xác nhận ngoài mẫu. Không đọc lại nhãn/hành vi/đơn từ cửa sổ test; nếu đối chiếu test chỉ dùng bảng aggregate đã commit. Không chạy `scripts/evaluate_test_once.py`.
- **Cohort nguồn:** đơn mua hợp lệ DEV theo quy ước hiện hành, trước `2025-10-22`; loại quà theo quy tắc đã khóa. Cửa sổ nhãn N=180 ngày, khoảng đệm L=7 ngày.

## Giả thuyết đăng ký

1. Mẫu nhãn hiện tại có một snapshot trên mỗi khách tại mốc đủ điều kiện đầu tiên; do đó lịch sử quan sát và phân phối recency/frequency có thể khác snapshot scoring DEV đa mốc.
2. Tạo snapshot đa mốc có thể thay đổi metric DEV so với mẫu hiện tại. Đây là giả thuyết về độ nhạy thiết kế, không phải giả thuyết rằng mô hình mới sẽ tốt hơn.
3. ROC-AUC baseline OOF pooled 0,536 có thể phát sinh vì baseline hiện hành phát xác suất prevalence khác nhau ở mỗi fold; gộp điểm giữa fold tạo thứ hạng xuyên fold dù baseline không phân biệt khách trong fold.
4. Bằng chứng hiện tại không đủ để quy chênh lệch ROC-AUC DEV ~0,51 và test ~0,70 cho nguyên nhân cụ thể. Không chọn mô hình hoặc kết luận dựa trên test.

## Định nghĩa snapshot và nhãn

- Dựng các mốc T theo tháng, dùng lịch mốc historical DEV đã đóng băng trong pipeline hiện tại; đưa vào mỗi T mọi khách có ít nhất một đơn mua hợp lệ, không quà, có ID trước T.
- Tạo đặc trưng chỉ từ đơn có ngày `< T`. Nhãn là có/không đơn mua hợp lệ, không quà trong `(T, T+180 ngày]`, theo định nghĩa DEV hiện hành.
- Chỉ giữ T mà `T + (N+L) < 2025-10-22`; không đưa ngày từ cửa sổ test vào feature hay label. N=180, L=7 không đổi.
- Trong temporal CV, validation theo thứ tự T. Mẫu train chỉ được dùng khi nhãn train đã trưởng thành trước validation T, tức `train_T + N + L < validation_T`. Một khách được phép xuất hiện ở nhiều T, kể cả ở các fold khác nhau; hàm/fold cũ không sửa. Viết hàm fold mới dành riêng v3 và kiểm thử ranh giới thời gian/leakage.
- Báo số snapshot và số khách duy nhất riêng. Các snapshot của cùng khách không được xem là độc lập trong CI; bootstrap lấy mẫu theo khách, giữ các snapshot của khách được lấy cùng nhau.

## Tập mô hình cố định và số phép so sánh

Chỉ bốn chiến lược xếp hạng, cùng temporal folds và cùng tập snapshot đủ điều kiện:

1. **Baseline hằng số chung:** xác suất cố định bằng prevalence trong phần train của fold đầu tiên; dùng đúng một giá trị cho toàn bộ validation OOF. Không fit trên validation. ROC-AUC phải 0,5 nếu có cả hai lớp; metric pooled không tạo thứ hạng chéo fold.
2. **Chỉ recency:** Logistic Regression với duy nhất đặc trưng recency ngày.
3. **Chỉ frequency:** Logistic Regression với duy nhất đặc trưng frequency.
4. **Logistic Regression v3:** Logistic Regression trên đặc trưng point-in-time đã đăng ký: recency, frequency, monetary tổng tích lũy hợp lệ, average gap, số ngày từ lần đầu đến T, và lịch tháng T. Dùng các biến đã có thể dựng trước T; không dùng trạng thái/sản phẩm/đơn phát sinh sau T.

Ba mô hình Logistic Regression dùng cùng pipeline tiền xử lý fit riêng trong train fold, `class_weight="balanced"`, `C=10`, `solver="lbfgs"`, `max_iter=2000`, `random_state=20261028`. Không tuning, không thêm/bớt biến theo kết quả. Nếu trường đặc trưng đăng ký không dựng được từ schema DEV hiện có, dừng và ghi rõ sai khác trước khi chạy mô hình; không thay thế hậu nghiệm.

**Số phép so sánh:** 4 chiến lược xếp hạng; 3 so sánh mô hình với baseline chung. Thống kê phân phối recency/frequency có 3 universe cố định: mẫu hiện tại, DEV snapshot đa mốc, và bảng aggregate test đã commit nếu bảng đó chứa đúng metric/định nghĩa tương thích. Tái dựng baseline legacy prevalence-per-fold chỉ là một chẩn đoán giao thức duy nhất, không tính là mô hình thứ năm và không dùng để chọn mô hình. Mọi metric/fold đã chạy, kể cả kết quả bất lợi hoặc thất bại, phải được lưu và báo cáo.

## Metric, bất định và seed

- Tách ROC-AUC, average precision (AP), prevalence và Brier score theo từng fold; báo macro/trung bình fold và pooled OOF riêng, kèm số mẫu và số dương mỗi fold.
- Đánh giá xếp hạng v3 bằng gain/lift theo decile, precision@top-5%, @10%, @20%; top-k làm tròn theo quy tắc cố định `ceil(k*n)` trong từng fold rồi tổng hợp. Ghi rõ đây là tỷ lệ bắt gặp trong DEV validation, không phải uplift nhân quả.
- Calibration: Brier score và bảng observed vs predicted theo 10 nhóm xác suất cố định theo quantile trên OOF; nhóm không đủ mẫu gộp theo quy tắc đã đăng ký trong mã và công bố n.
- Khoảng bất định 95% bằng percentile bootstrap theo khách, 2.000 lần, seed `20261028`; mọi snapshot của khách cùng nằm trong một bootstrap draw. Nếu lớp/điều kiện cần cho metric bị thiếu trong một draw, ghi số draw không tính được; không âm thầm loại trường hợp.
- Recency/frequency: báo phân phối và mẫu số cho ba universe. Chỉ so sánh với test aggregate nếu schema có số tóm tắt cùng định nghĩa; nếu không, ghi rõ không so sánh được, không mở test raw để bổ sung.

## Nguyên tắc kết luận

- Báo mức bằng chứng cho nhận định về cohort và chênh lệch DEV/test; không khẳng định nguyên nhân khi so sánh aggregate không tương thích hoặc thiếu phân phối.
- Kết quả v3 luôn ghi “DEV-only, khám phá, chưa xác nhận ngoài mẫu”; D-005 và mô hình chính không thay đổi.
- Không loại bỏ kết quả xấu, không mở thêm phân tích phân nhóm/mô hình sau khi xem kết quả. Mọi sai lệch giao thức phải ghi trước khi chạy phần bị ảnh hưởng.
