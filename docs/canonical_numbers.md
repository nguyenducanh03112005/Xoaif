# Sổ số chuẩn Xoaif Garden

Cập nhật: 2026-10-27. Mỗi số dưới đây gắn với đơn vị, cohort và nguồn aggregate. Dấu chấm phân tách hàng nghìn, dấu phẩy phân tách thập phân. Với số đã làm tròn, nguồn giữ giá trị đầy đủ.

## Cohort và thời gian

| Đại lượng | Số chuẩn và đơn vị/cohort | Nguồn sự thật |
|---|---|---|
| Snapshot hiện hành | 12.011 đơn; 601 trang; `20261024T052943Z` | `outputs/tables/day1_analysis_start_profile.json`: `snapshot_order_count`, `snapshot_id`; 601 trang là metadata snapshot đã ghi trong `docs/api_notes.md`. |
| Trước `analysis_start` | 476 đơn bán thử, 2022-06 đến 2022-09 | `outputs/tables/day1_analysis_start_profile.json`: `pre_analysis_order_count`, `pre_analysis_date_min`, `pre_analysis_date_max`. |
| Kho DEV | 6.517 đơn, `[2024-04-01, 2025-10-22)` | `outputs/tables/day1_analysis_start_profile.json`: `effective_development_order_count`, `analysis_start`, `development_exclusive_end`. |
| DEV status 3 | 6.400 đơn trong cùng khoảng DEV | `outputs/tables/day1_analysis_start_profile.json`: `effective_development_status3_count`; xác nhận trong `outputs/metrics/day2_money_audit.json`: `scope.status3_orders`. |
| DEV status khác 3 | 117 đơn; đối soát đơn: 6.517 = 6.400 + 117 | Aggregate `status_code<>3` trong `fact_orders`; kiểm tra read-only được ghi ở `docs/cohort_reconciliation.md`. |
| Khách DEV có status 3 | 5.174 khách có ID, cohort status 3 DEV | `outputs/tables/day1_development_cohort_summary.json`: `development_customer_count_status3_nonmissing`. |
| Khách distinct toàn bộ warehouse DEV | 5.174 khách có khóa; đều có ít nhất một đơn status 3 trong warehouse | COUNT DISTINCT read-only trên `fact_orders`; đây là kiểm tra cấu trúc kho. |
| Preflight N=180 | 5.499 khách ở mốc 2025-10-22; số tiền kiểm, chưa phải số nhãn/test | `outputs/tables/eligibility_preflight.csv`: dòng `candidate=N180`, cột `eligible_customers`. |
| Cohort scoring/test | 5.169 khách đủ điều kiện trước T | `outputs/metrics/test_eval.json`: `cohort.eligible_customers_with_pre_T_purchase`; đối chiếu pre-open với `outputs/metrics/day2_segmentation.json`: `customer_count`. |
| Cầu nối cohort 5.499 → 5.174 → 5.169 | 5.499 khách trước T − 325 khách chỉ có status 3 trước `analysis_start` = 5.174; − 5 khách B chỉ có đơn quà = 5.169. **phần dư chưa giải thích: 0** | Đếm trực tiếp bằng HMAC chuẩn trên snapshot pre-T và `assess_order_money` Amendment 03; đối chiếu DuckDB, preflight và metric scoring. `docs/cohort_reconciliation.md`; JSON tổng hợp: `outputs/tables/cohort_bridge_verified.json`. |
| Thiếu customer ID | 286 đơn status 3 DEV | `outputs/tables/dev_quality_summary.json`: `valid_status_3_orders_missing_customer_id`; đối chiếu `outputs/metrics/day2_preprocessing.json`: `missing_customer_id_orders`. |
| Cửa sổ test thực thi | `[2025-10-22, 2026-04-20)`; gồm ngày T và 179 ngày lịch sau T | `outputs/metrics/test_eval.json`: `test_interval`, `effective_post_T_calendar_dates`; sai khác quy tắc `>T` ghi ở D-010. |
| DATA_CUTOFF | 2026-10-24, loại trừ | `config/split.yaml` (khóa, chỉ đọc); `docs/PROGRESS.md`. |

## Tiền, nhãn, giỏ và phân khúc

| Đại lượng | Số chuẩn và đơn vị/cohort | Nguồn sự thật |
|---|---|---|
| Quà cấp đơn | 22/6.400 đơn status 3 DEV (0,34%) | `outputs/metrics/day2_money_audit.json`: `gifts.count`, `gifts.rate`, `scope.status3_orders`. |
| Doanh thu âm | 2/6.400 đơn status 3 DEV (0,03%); dưới ngưỡng dừng 1% | `outputs/metrics/day2_money_audit.json`: `negative_revenue.count`, `negative_revenue.rate`, `negative_revenue.stop_threshold`. |
| Nhãn DEV | 3.508 mẫu khách; 260 dương; 7,41% | `outputs/metrics/day2_label_audit.json`: `customer_samples`, `positive_samples`, `positive_rate`. |
| Test | 5.169 khách; 237 dương; 4,59% trong cửa sổ test thực thi | `outputs/metrics/test_eval.json`: `cohort.eligible_customers_with_pre_T_purchase`, `test_positive_customers`, `test_positive_rate`. |
| Dòng hàng DEV | 30.049 dòng = 4 direct zero-price + 903 inferred subset + 29.142 không phải quà | `outputs/metrics/day3_combo_prereg.json`: `gift_line_audit.line_count_by_source`, `gift_line_audit.line_count`. 903 dòng inferred có độ tin cậy thấp. |
| Giỏ Day 3 | 6.031 giỏ trước; 6.006 sau áp dụng phân loại tất cả nguồn quà | `outputs/metrics/day3_combo_prereg.json`: `eligible_baskets_before_gift_line_removal`, `eligible_baskets_after_all_gift_line_removal`. |
| Giỏ Day 2B clean | 5.684 giỏ sau khi bỏ dòng giá niêm yết 0 theo lượt phân tích Day 2B | `outputs/metrics/day2b_baskets.json`: `eligible_baskets_after_zero_price_removal`. Đây là quy tắc làm sạch khác với 6.006 giỏ Day 3 sau phân loại mọi nguồn quà. |
| Combo DEV đã khóa | 24 cặp chính; mỗi cặp đáp ứng quy tắc xuất hiện ít nhất 4/6 ô nhạy cảm và có mặt ở ô chính `all_gift_sources`, support 0,05 | `outputs/metrics/day3_combo_prereg.json`: `stable_combo_rule`, `stable_pair_count`, `main_combo_count`. Không khẳng định mọi cặp có mặt 6/6 ô. |
| Combo test | 24 cặp được chấm; 21/24 có lift > 1 trên 2.174 giỏ test đủ điều kiện | `outputs/metrics/test_eval.json`: `association_rules.frozen_combo_count`, `test_lift_gt_1_count`, `test_eligible_basket_count`. |
| K-Means | K=2; silhouette 0,5075 (báo cáo 0,508), cohort khách scoring DEV | `outputs/metrics/day2_segmentation.json`: `chosen_k`, `chosen_silhouette`, `customer_count`. |
| Một đơn, DEV status-3 | 4.526/5.174 khách = 87,5% | `outputs/tables/day1_development_cohort_summary.json`: `repeat_frequency_distribution["1"]`, `development_customer_count_status3_nonmissing`. |
| Một đơn, cohort scoring | 4.530/5.169 khách = 87,6% | `outputs/metrics/day2_label_audit.json`: `frequency_distribution_at_test_start["1"]`, `unique_customer_count`. |
| Proxy giá trị lớn | 62/5.169 khách scoring (1,20%); ngưỡng p99 theo DEV, không xác minh pháp nhân | `outputs/metrics/day2_label_audit.json`: `large_value_customer_proxy.customers`, `share`; mẫu số `unique_customer_count`. |

## Mô hình DEV và test

Ngưỡng dự đoán test của các classifier là 0,5. Bootstrap test có 2.000 lượt, seed 20261026. CI dưới đây là 95%; ΔAP là paired average precision so với baseline.

| Mô hình và vai trò | Cohort / metric | Số chuẩn | Nguồn / khóa |
|---|---|---|---|
| Logistic Regression C=10 — mô hình chính theo D-005 | DEV OOF, 1.558 mẫu / 94 dương | ROC-AUC 0,5096; AP 0,0699; PR-AUC trung bình 5 fold 0,1093 | `outputs/metrics/dev_final_model.json`: `best_model`, `best_parameters`, `best_model_oof_metrics`, `models.logistic_regression.mean_fold_pr_auc`. |
| Baseline DEV | DEV OOF gộp, cùng 1.558 mẫu / 94 dương | ROC-AUC 0,5362; AP 0,0671 | `outputs/metrics/dev_final_model.json`: `models.majority_baseline.out_of_fold_metrics`. Mỗi fold gán prevalence của train fold; score thay đổi giữa fold. |
| Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính | DEV OOF, 1.558 mẫu / 94 dương | ROC-AUC 0,4969; AP 0,0645; CI ROC 0,4330–0,5599; CI AP 0,0490–0,0914; CI ΔAP −0,0193 đến +0,0204 | `outputs/metrics/dev_final_models_v2.json`: `repurchase_features_v2.selected_oof_metrics`, `selected_model_bootstrap_ci`; đối chiếu `outputs/metrics/test_eval.json`: `development_reference`. |
| Baseline majority | Test, 5.169 khách / 237 dương | ROC-AUC 0,5000; AP 0,0459 | `outputs/metrics/test_eval.json`: `models.majority_baseline`. Baseline test dùng một prevalence DEV cố định cho mọi khách. |
| Logistic Regression C=10 — mô hình chính theo D-005 | Test, 5.169 khách / 237 dương | ROC-AUC 0,7024 (CI 0,6651–0,7365); AP 0,1234 (CI 0,1005–0,1581); ΔAP +0,0776 (CI +0,0560 đến +0,1109); TN/FP/FN/TP = 4.538/394/158/79 | `outputs/metrics/test_eval.json`: `models.amendment_03_logistic_regression`, `bootstrap_95_ci.amendment_03_logistic_regression.metrics_95_ci`, `bootstrap_95_ci.paired_average_precision_delta_vs_baseline_95_ci.amendment_03_logistic_regression`. |
| Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính | Test, 5.169 khách / 237 dương | ROC-AUC 0,7027 (CI 0,6651–0,7373); AP 0,1233 (CI 0,0994–0,1582); ΔAP +0,0774 (CI +0,0554 đến +0,1111); TN/FP/FN/TP = 4.468/464/154/83 | `outputs/metrics/test_eval.json`: `models.repurchase_features_v2_logistic_regression`, `bootstrap_95_ci.repurchase_features_v2_logistic_regression.metrics_95_ci`, `bootstrap_95_ci.paired_average_precision_delta_vs_baseline_95_ci.repurchase_features_v2_logistic_regression`. |
| Cổng tín hiệu đã đăng ký | Cận dưới CI ROC-AUC > 0,55 và cận dưới paired ΔAP CI > 0; CI aggregate của cả hai classifier thỏa hai cận theo lần chạy thực tế | Cờ `feature_v2_signal_supported=True` chỉ được lưu cho v2; không tạo cờ C=10 | `config/amendment_05_test_open.yaml`: `classification.signal_rule`, model registry; `outputs/metrics/test_eval.json`: `feature_v2_signal_supported` và từng khóa bootstrap ở hai dòng trên. D-021 quy định cách diễn đạt có caveat giao thức. |

DEV OOF ROC-AUC baseline 0,5362 khác test baseline 0,5000 vì baseline DEV dùng prevalence riêng của train ở từng fold, còn test dùng prevalence DEV cố định. Hai con số không cùng cách tạo score.

Cấu hình ghi >T, evaluator dùng [T,end) (gồm ngày T); ảnh hưởng chưa xác định; đây là kết quả số liệu của lần chạy thực tế, không phải khẳng định tuân thủ đầy đủ giao thức, không gọi là 'đạt cổng ghi trước'.

## Tiền hiện hành và lịch sử cổng cũ

| Đại lượng | Số chuẩn và định nghĩa | Nguồn sự thật |
|---|---|---|
| Cổng cũ | 701/6.400 đơn status 3 DEV = 10,95%, theo công thức và cổng 5% của Amendment 02 đã bị thay thế | `docs/money_audit.md` (phần lịch sử), `config/amendment_02_money_and_gift_rules.yaml` (khóa, chỉ đọc). |
| `adj_unexplained` hiện hành | 639/6.400 đơn status 3 DEV = 9,98%, theo phân loại Amendment 03 | `outputs/metrics/day2_money_audit.json`: `adj_unexplained.count`, `adj_unexplained.rate`, `scope.status3_orders`. Đây không phải cùng định nghĩa với 701 của cổng cũ. |

## Dashboard và sản phẩm bàn giao

| Đại lượng | Số chuẩn và phạm vi | Nguồn sự thật |
|---|---|---|
| Tổng doanh thu dashboard mặc định | 4.200.024.995 đ và 9.104 đơn status 3 không tặng, 25 bucket tháng từ 2024-04 đến 2026-04; gồm DEV và cửa sổ test, tháng 2026-04 không trọn tháng | `outputs/tables/dashboard_sales_monthly.csv`: tổng cột `recognized_revenue_vnd`, tổng cột `orders`, min/max `month`. |
| UNKNOWN trên bảng tỉnh/thành | 3.860.511.662 đ, 8.403 đơn, bằng 91,92% tổng doanh thu trong bảng tỉnh/thành (DEV+test). Trong DEV riêng: 5.860/6.400 đơn thiếu `shipping_address.province_name` (91,56%); doanh thu tương ứng 2.384.693.718/2.628.354.091 đ (90,73%). | `outputs/tables/dashboard_sales_province.csv`; đếm DEV pre-T và công thức Amendment 03 ở `docs/unknown_region_diagnostic.md` và `outputs/tables/cohort_bridge_verified.json`. |
| Dashboard | 5 tab; 10 CSV tổng hợp + 6 JSON tổng hợp; tổng số dòng được kiểm tra bởi `scripts/dashboard_smoke.py` | Danh sách nguồn trong `src/app/streamlit_app.py`; bảng tỉnh/thành không còn là đầu vào dashboard. |
| Báo cáo | 15 trang A4 | `pdfinfo report/xoaif_report.pdf`: `Pages`. |
| Slide in | 15 trang ngang | `pdfinfo slides/xoaif_print.pdf`: `Pages`. Không tạo PPTX vì môi trường thiếu `python-pptx`. |
| Kiểm thử | 78 pytest ở lần hậu kiểm cuối | Log cuối của `scripts/run_all.py` và `pytest`; không chạy evaluator, notebook hay fit/refit model. |
| Hạn nộp | 2026-10-27; thời lượng và rubric chính thức chưa có | Chủ dự án cung cấp trong yêu cầu ngày 2026-10-26; được ghi ở `docs/schedule.md`. |
