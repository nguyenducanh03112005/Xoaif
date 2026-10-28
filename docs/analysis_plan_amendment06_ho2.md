# Đăng ký 06-HO2 — Gate B revision 2 (nhãn vẫn đóng)

- **Mã/revision:** 06-HO2, revision 2; supersedes lock revision 1 bằng SHA-256 được ghi trong YAML và lock mới.
- **Trạng thái:** chuẩn bị đánh giá; `test_opened: false`, Phase C chưa bắt đầu. Không có nhãn/đơn/hành vi HO2 nào được đọc khi lập protocol này.
- **Cửa sổ:** T2=`2026-04-20`, múi giờ `Asia/Ho_Chi_Minh`; đặc trưng chỉ từ local date `<T2`; outcome là status 3, không phải đơn quà cấp đơn, tại local date `>T2` và `<=T2+180 ngày` (`2026-10-17` inclusive). Ngày đúng T2 bị loại khỏi cả hai.
- **Hồ sơ:** snapshot `20261024T052943Z`; số dòng snapshot đã biết trước khóa là 12.011. Kết quả chỉ áp dụng cho cửa hàng này và giai đoạn này.

## Ranh giới truy cập

1. Trước khi xét bất kỳ trường nào khác của hàng raw, chỉ đọc `inserted_at`; nếu local day không thuộc phạm vi đã đăng ký thì bỏ hàng ngay. Loader HO2 chỉ gọi được khi `outputs/metrics/holdout2_opened.lock.json` hợp lệ, revision=2 và khớp hash config/protocol/evaluator; khóa được tạo bằng chế độ tạo một lần sau đúng ủy quyền chủ dự án. Hết lượt này chưa tạo khóa đó.
2. Mặc định evaluator/import không nạp raw, DuckDB hay nhãn. Không chạy `scripts/evaluate_test_once.py`; không dùng nhãn test cũ để fit/chọn/hiệu chỉnh.
3. Dry-run chỉ nhận T trong DEV với toàn bộ horizon 180 ngày không vượt DEV end; chỉ gọi `load_dev_orders()`, chỉ lưu vào `outputs/dryrun/`, gắn nhãn “kiểm thử mã, không phải kết quả, không dùng để chọn hay tinh chỉnh”, không xuất AUC/metric đánh giá và không đưa vào canonical.
4. Khi được mở sau này, evaluator chạy đúng một lần, ghi aggregate không có customer/order key vào `outputs/metrics/holdout2_eval.json` và `docs/holdout2_report.md`; log một dòng mở tại `outputs/logs/holdout2_access.jsonl`. Nếu lỗi sau khi tạo khóa, không chạy lại.

## Giả thuyết và phép kiểm định

Hai giả thuyết chính được đăng ký trước tạo family-wise alpha 0,05; kiểm định một phía, Holm step-down: p nhỏ nhất so với 0,025, p kế tiếp so với 0,05. p-value thô H1/H2 lấy từ bootstrap theo khách 2.000 lần, seed `20261028`, với phân phối bootstrap được định tâm tại ngưỡng không `H0`; khoảng tin cậy percentile cũng bootstrap cùng đơn vị khách. Cùng khách được lấy cùng nhau nếu có nhiều snapshot.

- **H1 chính:** ROC-AUC của D-005 `>0,55`. Báo điểm, CI 95% hai phía, cận một phía 95%, p thô và p Holm. H1 được hỗ trợ khi điểm AUC>0,55 và p Holm<0,05. Câu khóa trước: **“Đạt H1 không có nghĩa là lặp lại ROC-AUC test 0,70.”** Báo thêm `AUC_HO2−0,70` và CI như chênh lệch mô tả, không là giả thuyết.
- **H2 chính:** tỷ lệ mua lại 180 ngày của nhóm frequency≥2 chia nhóm frequency=1 `>1,5`; frequency đếm đơn status-3 không quà trước T2. Báo tử số/mẫu số mỗi nhóm, RR, bootstrap CI 95%, p thô và p Holm. H2 được hỗ trợ khi RR>1,5 và p Holm<0,05.
- **Quyết định H2 đã khóa trước mở:** RR DEV multi-snapshot=3,473, CI 95% `[2,656;4,520]`. Theo kế hoạch R2, công suất Wald log-RR tại RR bằng cận dưới 2,656 là 100,00% ở nền 7,4% và 99,87% ở nền 4,6%; cả hai ≥80%, RR cận dưới >1,5. Do đó H2 trở lại nhóm chính. Bảng công suất đầy đủ H1/H2 nằm trong `docs/gateb_r2_results.md` và `outputs/metrics/gateb_r2_power.json`.

## Chiến lược chấm đã đóng băng (8)

| Chiến lược | Định nghĩa / fit |
|---|---|
| D-005 | Artifact DEV `day2_dev_final_model.joblib`, không fit lại. |
| v2 | Artifact DEV `repurchase_features_v2.joblib`, không fit lại. |
| S1 | Score 1 nếu frequency≥2, ngược lại 0. Tỷ lệ score 1 DEV multi-snapshot 13,93%; luật rời rạc. |
| S3 | Artifact cây final-fit toàn DEV đa mốc: WP5 `MODEL_FEATURES`, median imputer + StandardScaler, depth=3, leaf=50, seed 20261028. |
| S6 | Map rate final-fit toàn DEV đa mốc theo recipe WP5c, ô tần suất/recency và gộp min train n=100. Rate table lịch sử `repurchase_wp5c_train_rates.csv` là theo outer fold, không phải fit final; dùng artifact map riêng đã băm. |
| v3 | Artifact Logistic Regression final-fit toàn DEV đa mốc: `C=10`, balanced, lbfgs, max_iter=2000, seed 20261028, WP5 `MODEL_FEATURES`. |
| Recency-only | Baseline mô tả, score chuẩn hóa recency theo DEV nhân dấu hệ số DEV đã khóa (dấu âm). |
| Frequency-only | Baseline mô tả, score chuẩn hóa frequency theo DEV nhân dấu hệ số DEV đã khóa (dấu dương). |

Chọn phương án A cho S3, S6 và v3: một artifact/map final-fit trên toàn DEV, trước khóa, không dùng metric in-sample làm đánh giá tổng quát. D-005 giữ nguyên vai trò mô hình chính. Không có ứng viên kinh doanh được chọn. Metric D-005 trừ mỗi baseline đơn biến có CI paired bootstrap, chỉ mô tả.

## H3 — thứ hạng top-decile tie-aware (phụ, 6 phép so sánh)

H3 gồm đúng S1/S3/S6 × precision@10%/lift; không hiệu chỉnh multiplicity, kết quả chỉ là hỗ trợ phụ. Với `N` khách, `K=ceil(0,10N)`, cắt theo score giảm dần. `n_above`, `pos_above` là lượng khách/dương có score lớn hơn score tại điểm cắt; `n_tie`, `pos_tie` là lượng khách/dương bằng score tại điểm cắt; `q=(K−n_above)/n_tie`. `precision@10=(pos_above+q×pos_tie)/K`; không bốc thăm trong tie. `lift=precision@10 / prevalence_HO2`. Phép tính lặp nguyên tắc tie-aware trong mỗi bootstrap draw. H3 chỉ được hỗ trợ nếu cận dưới bootstrap 95% precision lớn hơn prevalence HO2 và cận dưới lift lớn hơn 1. ROC-AUC/decile S1, S3, S6 chỉ mô tả vì S1 nhị phân, S3/S6 có ít mức điểm.

## H4 — ổn định thứ hạng nhóm (phụ)

- S6 dùng 12 ô cố định frequency `{1,2,≥3}` × recency `{≤30,31–90,91–180,>180}`. RFM dùng hàm WP5 A1 và cutoff giá trị cao `830.000 VND`.
- DEV tham chiếu chia 6 anchor đầu (2024-05…2024-10) và 6 anchor sau (2024-11…2025-04). Chỉ giữ nhóm có n≥30 trong mỗi nửa. `rho_dev_half` là Spearman giữa thứ hạng tỷ lệ mua lại của hai nửa.
- Ngưỡng được hiệu chuẩn trước mở: S6 `rho_dev_half=0,9761904762` với 8 nhóm; RFM `rho_dev_half=1,0` với 6 nhóm. Hệ nhóm HO2 testable nếu có ≥4 nhóm cố định có n≥30, nhóm được giữ không chọn theo outcome. Hệ đạt nếu Spearman thứ hạng DEV-pooled và HO2 `rho_HO2≥rho_dev_half`; H4 tổng đạt khi cả S6 và RFM testable, đạt. Nếu thiếu nhóm thì ghi không testable, không nới ngưỡng.

## H5 và H6

- **H5:** dùng đúng 24 combo đóng băng; `k_DEV=1` thỏa đồng thời DEV `lift>1`, `Kulczynski≥0,5`, `IR≤0,5`. Vì `k_DEV<4`, H5 chỉ mô tả, không có kiểm định xác nhận. Giỏ HO2 là đơn ngày `>T2` và `≤2026-10-17`, status 3, không phải đơn quà cấp đơn, loại dòng quà theo Amendment 05, gộp biến thể theo product ID, cần ≥2 product ID hàng hóa. Không khám phá combo mới. Nếu số đồng xuất hiện của cặp <30 thì suppress cặp và không tính là qua bộ lọc. Không phân bổ chiết khấu cấp đơn xuống sản phẩm.
- **H6:** không kiểm định. Không có dải xu hướng DEV đáng tin cho AOV, đơn/khách, khách mới/tháng, tỷ lệ mua lại khách mới.
- Prevalence và calibration-in-the-large chỉ mô tả. D-005 so với recency/frequency-only là chênh lệch mô tả kèm CI, không là giả thuyết.

## Giới hạn và số phép thử

Hai kiểm định chính H1/H2 có Holm; H3 có 6 phép so sánh phụ không hiệu chỉnh; H4 có 2 hệ nhóm; H5 là một tỷ lệ mô tả, H6 không test. Không thêm subgroup, threshold, feature, combo hay model. HO2 là khoảng giữ lại hồi cứu trong cùng snapshot/cửa hàng, không tiến cứu hay ngẫu nhiên; số liệu quan sát không chứng minh nhân quả, lợi nhuận hay biên lợi nhuận. Kết quả không xác nhận ngoài cửa hàng/giai đoạn này. Phase C vẫn cần quyết định riêng.
