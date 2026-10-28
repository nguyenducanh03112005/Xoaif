# Đăng ký trước 06-HO2 — kiểm chứng ngoài thời gian trên snapshot hiện có

- **Trạng thái:** giao thức chuẩn bị ở Gate B; chưa mở nhãn HO2, chưa chạy đánh giá nào. Hash của file này và YAML/lock đi kèm được ghi vào hồ sơ Gate B.
- **Định danh:** `06-HO2` phân biệt giao thức này với mục lịch sử `06 — Probe metadata Pancake` trong `docs/amendment_log.md`; không viết lại lịch sử hoặc đổi các khóa cũ.
- **Cohort/thời gian:** snapshot `20261024T052943Z`, múi giờ `Asia/Ho_Chi_Minh`; T2=`2026-04-20`; feature chỉ từ đơn hợp lệ có ngày địa phương `< T2`; nhãn, nếu được mở sau phê duyệt riêng, là mua lại status 3 không quà với ngày địa phương `(T2, 2026-10-17]` theo định nghĩa mua lại F1. Ngày kết thúc này là đúng 180 ngày sau T2, bao gồm cả ngày 2026-10-17. Không đọc đơn/nhãn/hành vi trong cửa sổ này trước lệnh mở riêng.
- **Ủy quyền lịch sử:** dữ liệu cũ thuộc cửa sổ test đã đóng `[2025-10-22, 2026-04-20)` được phép dùng làm lịch sử feature tại T2. Tuyệt đối không dùng nhãn test cũ để fit, chọn, hiệu chỉnh hoặc thay ngưỡng. Khi quét snapshot, chỉ đọc `inserted_at` trước khi quyết định bỏ qua mọi trường khác; nếu ngày địa phương `>= T2`, bỏ ngay.
- **Loại đánh giá:** một lần chấm khóa các cấu hình có thể tái tạo; không fit/chọn lại bằng nhãn HO2. Mô hình/chiến lược cần được lưu hoặc định nghĩa đầy đủ trước khi mở. Mô hình không có artifact/định nghĩa/tham số hợp lệ tại Gate B bị loại khỏi xác nhận; không bổ sung sau khi xem HO2.

## Giả thuyết và tiêu chí

Hai giả thuyết chính tạo một họ kiểm định, Holm family-wise alpha 0.05, kiểm định một phía:

1. **H1:** AUC ROC của D-005 > 0.55. Báo AUC và cận dưới một phía điều chỉnh Holm; đạt nếu cận dưới điều chỉnh vượt 0.55.
2. **H2:** tỷ số nguy cơ mua lại ở khách frequency≥2 so với frequency=1 > 1.5. Báo RR và cận dưới một phía điều chỉnh Holm; đạt nếu cận dưới vượt 1.5. Định nghĩa frequency là số đơn status-3 không quà trước T2.

Holm áp dụng theo p-value một phía chưa điều chỉnh, sắp tăng dần: kiểm định nhỏ nhất so với .025, kế tiếp so với .05. Cận dưới báo cáo được suy ra bằng đảo kiểm định cùng phương pháp; báo p thô, p Holm, cận và tiêu chí cho cả hai.

Các giả thuyết phụ, không thay đổi tiêu chí sau mở:

3. **H3:** với từng S1/S3/S6 đã khóa, cận dưới CI 95% của lift top-decile và precision@10% vượt tỷ lệ nền HO2. Hiệu chỉnh Holm không áp dụng cho H3; kết quả là hỗ trợ phụ, không tuyên bố xác nhận nếu nhiều so sánh.
4. **H4:** xếp hạng các ô S6 và nhóm RFM theo tỷ lệ mua lại có cùng chiều với thứ hạng ghi trong DEV; báo tương quan thứ hạng và đảo chiều từng cặp, mô tả do cỡ mẫu hữu hạn.
5. **H5:** tỷ lệ trong 24 combo đóng băng đạt bộ lọc DEV (`lift>1`, Kulczynski≥0.5, IR≤0.5) ít nhất 1/24. Báo tử số/mẫu số; không khám phá combo mới.
6. **H6:** AOV, đơn/khách, khách mới/tháng và tỷ lệ mua lại khách mới nằm trong dải dựa trên ngoại suy xu hướng DEV. Dải phải được tính và ghi vào lock trước khi mở; nếu xu hướng/độ phủ DEV không hỗ trợ ước lượng hữu ích, H6 bị đánh dấu không khả thi và không thay bằng khoảng tĩnh.

Calibration-in-the-large và tỷ lệ nền HO2 chỉ mô tả, không phải giả thuyết xác nhận. Không diễn giải quan sát thành tác động nhân quả hay lợi nhuận.

## Tập chiến lược cố định

- **D-005:** artifact `outputs/models/day2_dev_final_model.joblib`, recipe và schema từ nguồn đã khóa của D-005; hash artifact ghi tại manifest 06-HO2.
- **v2:** artifact `outputs/models/repurchase_features_v2.joblib`, `C=0.1`, schema/recipe đã ghi trong `outputs/metrics/dev_final_models_v2.json`; hash ghi tại manifest.
- **v3:** recipe logistic regression đã đăng ký WP5 (`C=10`, balanced class weight, lbfgs, 2000 iterations, seed 20261028) và feature builder WP5 đã băm; chỉ được đưa vào xác nhận nếu có artifact đóng băng trước Gate B. Không tái fit trên HO2 hoặc nhãn test cũ.
- **Recency-only / frequency-only:** logistic regression cùng tiền xử lý và seed đã đăng ký WP5, từng chỉ dùng một feature tương ứng; cần artifact được lưu/băm trước Gate B để được xác nhận.
- **S1:** luật `frequency>=2`; **S3:** cây nông đã đăng ký WP5b; **S6:** bảng tỷ lệ theo ô đã đăng ký WP5c. Định nghĩa/script/metric được băm; S6 chỉ dùng rate table DEV đã tạo trước Gate B.
- Ghi rõ trong manifest chiến lược nào đủ điều kiện chấm xác nhận, chiến lược nào chỉ phân tích phụ hoặc bị loại và lý do. Không dùng tên “ứng viên được chọn”; WP5b không chọn ứng viên.
- Đóng băng RFM/phân khúc từ `outputs/models/segmenters_dev_frozen_v1.joblib` và ngưỡng `outputs/metrics/frozen_segmenters_dev.json`; đóng băng 24 combo từ `outputs/tables/combos_v2.csv` cùng bộ lọc trên. Hash từng nguồn.

## Metric, bất định, và phép so sánh

- H1/H3: ROC-AUC, AP, lift/gain theo decile, precision@5/10/20%, Brier và calibration-in-the-large; pooled và subgroup/fold không áp dụng vì đây là một cửa sổ giữ lại.
- H2: tỷ lệ hai nhóm, risk ratio, khoảng tin cậy score/log method đã chỉ định trong script trước mở. Nếu ô bằng 0 hoặc CI không xác định, báo không ước lượng được; không thêm hiệu chỉnh hậu nghiệm.
- Bootstrap percentile theo khách, 2.000 lần, seed `20261028`; nhiều snapshot cùng khách (nếu metric nào dùng snapshot) lấy mẫu theo cụm khách. Không thay CI method sau mở.
- Một lần chấm trên một HO2; 2 kiểm định chính (Holm), 6 nhóm giả thuyết phụ nêu trên; không subgroup khám phá, tuning, threshold search hay feature selection.

## Kiểm tra chính xác/công suất trước khóa

Chỉ dùng số lượng eligible và tần suất trước T2, cộng các prevalence tham chiếu đã công bố DEV 7.4% và test cũ 4.6%. Không đọc/ước lượng nhãn HO2. Bảng Gate B phải có số khách eligible, frequency≥2, frequency=1, expected positives dưới hai prevalence tham chiếu, độ rộng CI tỷ lệ kỳ vọng, và đánh giá công suất H1/H2 theo xấp xỉ được mô tả rõ. Nếu không đủ công suất, H1/H2 được hạ thành giả thuyết phụ hoặc tiêu chí được sửa trước khi khóa; phải ghi căn cứ. Không được sửa sau mở.

## Tính chất và giới hạn

HO2 là cửa sổ thời gian thứ hai trong cùng snapshot đã thu thập, của cùng một cửa hàng; đây không phải tiến cứu thật hoặc thử nghiệm ngẫu nhiên. Dịch chuyển nền, thay đổi vận hành và kiểm duyệt snapshot có thể ảnh hưởng kết quả. Dữ liệu quan sát không chứng minh nhân quả. Giao thức này không thay mô hình chính D-005 và không cho phép mở HO2; cần phê duyệt chủ dự án riêng bằng câu lệnh đã quy định.
