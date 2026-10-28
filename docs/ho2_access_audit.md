# Kiểm toán đường truy cập dữ liệu trước khi mở HO2

**Trạng thái: HO2 vẫn đóng.** Kiểm toán chỉ đọc mã, metadata, và giá trị tối đa của cột thời gian trong aggregate đã commit; không đọc raw để kiểm tra nhãn/hành vi HO2. Không chạy `scripts/evaluate_test_once.py`.

## Cổng nạp và đầu ra

| Nơi | Cổng/nguồn theo mã | Đầu ra hoặc phạm vi |
|---|---|---|
| `src/features/day2_data.py::load_dev_orders` | `inserted_at` được kiểm tra trước; sau đó local date phải nằm DEV `[2024-04-01,2025-10-22)`. | In-memory DEV orders/features; đầu vào cho các script WP5/A1–F5 và phân tích DEV liệt kê dưới. |
| `src/features/day2b_data.py::make_repurchase_features` | Gọi `load_dev_orders`; chỉ chọn đơn status 3 không quà với ngày `<T`. `load_cancel_refund_orders` có loader riêng: timestamp gate trước, date `<test_start`. | DEV latest-order features hoặc aggregate hủy/hoàn; không dùng nhãn test để fit. |
| `scripts/build_dev_warehouse.py` | Quét snapshot; timestamp `inserted_at` trước, rồi chỉ đưa local date DEV vào kho. | `data/restricted/xoaif_dev.duckdb`; HMAC keys, không địa chỉ/văn bản tự do/tiền. |
| `scripts/build_dss_cuboids_dev.py` | Raw gate `inserted_at` trước và DEV date bounds; DuckDB read-only truy vấn có giới hạn DEV; đối chiếu với DEV loader. | Cuboid tổng hợp DEV. |
| `scripts/audit_money.py` | Raw timestamp gate trước; khoảng ngày phát triển được khóa. | Audit tiền tổng hợp DEV. |
| `scripts/build_pretest_evidence.py` | DuckDB truy vấn đến trước T; raw scan chỉ dựng bằng chứng tiền kiểm có ranh giới ngày. | Bằng chứng tiền kiểm; không phải nhãn HO2. |
| `scripts/build_day1_artifacts.py`, `scripts/build_eda_dev_artifacts.py`, `scripts/profile_development_cohorts.py` | DuckDB read-only; truy vấn EDA/chỉ tiêu có điều kiện DEV. Riêng profile kiểm tra MAX(local_date) metadata. | EDA và profile DEV. |
| `scripts/count_ho2_eligibility_preregistered.py` | Timestamp trước, sau đó chỉ lấy lịch sử local date `<T2`; phép đếm cohort/feature-side, không dựng outcome. | Số khách và nhóm pre-T2. |
| `scripts/evaluate_holdout2_once.py`, `src/features/holdout2_access.py` | Được viết trong Gate B revision 2 nhưng không chạy chế độ mở. Import mặc định không nạp dữ liệu; raw loader gọi `require_open_lock()` trước manifest/page; lock phải revision 2 và khớp config/protocol/evaluator hash. Raw rows chỉ được xét sau timestamp gate trong phạm vi `[analysis_start,2026-10-17]`. | Sau ủy quyền riêng mới tạo single-open lock/log và aggregate; hiện không có lock/outcome output. |
| `scripts/count_test_eligibility.py`, `scripts/preregister_test_open.py`, `scripts/verify_split_lock.py` | Kiểm tra manifest/metadata/điều kiện cohort; không tạo bộ nhãn HO2. | Metadata và khóa giao thức. |
| `scripts/evaluate_test_once.py` | Mã lịch sử duy nhất từng mở cửa sổ test cũ `[2025-10-22,2026-04-20)`. Không chạy trong lượt này. | Aggregate test cũ đã khóa; không liên quan HO2. |
| `scripts/snapshot_orders.py`, `scripts/refresh_batch.py`, `scripts/profile_snapshot.py`, `scripts/profile_day1_status.py`, `scripts/profile_analysis_start.py`, `scripts/survey_gift_line_fields.py` | Công cụ snapshot/profile có thể đọc raw. Không chạy trong lượt kiểm toán này; phải giữ/áp dụng timestamp gate và giới hạn scope trước khi tái sử dụng. | Snapshot hoặc báo cáo metadata/profiling; không được dùng để mở HO2 ngoài evaluator được khóa sau này. |
| `scripts/probe_endpoints.py` | DuckDB read-only, nhưng truy vấn theo hồ sơ probe; không chạy trong lượt này. | Probe metadata/đếm, không cần cho Gate B. |
| DEV analysis scripts | `analyze_repeat_definition_f1.py`, `analyze_prevalence_drift_f2.py`, `analyze_repurchase_v3_dev.py`, `evaluate_repurchase_wp5b_dev.py`, `evaluate_repurchase_wp5c_dev.py`, `analyze_gateb_r2_dev.py`, `calibrate_gateb_r4_dev.py`, `freeze_gateb_strategies_dev.py`, `analyze_customer_value_dev.py`, `analyze_product_journey_dev.py`, `analyze_revenue_scenarios_f5.py`, `analyze_seasonality_dev.py`, `evaluate_holiday_time_dev.py`, `evaluate_dev_segmentation_objective_i.py`, `build_dashboard_cuboids_f4.py`, `build_dashboard_cuboids_f4b.py`, `prepare_day2.py` đều dùng `load_dev_orders`, kho DEV có date gate, hoặc aggregate DEV đã tạo. | Chỉ đầu ra DEV; không mở test/HO2. |
| `src/features/basket.py`, `basket_v2.py`, `day3_baskets.py`; `src/models/classify.py`, `classify_v2.py`, `segment_v2.py` | Đọc các bảng feature/aggregate đã tạo cho DEV; không tự mở raw. | Mô hình/giỏ hàng đã khóa hoặc DEV. |
| Dashboard `src/app/streamlit_app.py`, `src/app/dashboard.py`; `scripts/dashboard_smoke.py` | Chỉ đọc CSV/JSON aggregate đã được review trong `outputs/`; không đọc DuckDB/raw. | Dashboard offline; smoke không gọi API. |
| `scripts/build_report_pdf.py`, `scripts/build_slides_pdf.py`, `scripts/build_dq_report.py` | Đọc aggregate/artifact hiện có; PDF report dùng bảng dashboard có cả DEV và test cũ. Không nạp raw. | PDF/slide/quality report; không có HO2. |
| `src/ingest/decision_amendment.py` | Đọc restricted manifest/metadata để áp quy tắc, không tự quét đơn. | Manifest kiểm toán; không có HO2 outcome. |
| Các script output khác (`scripts/build_dq_report.py`, `scripts/build_report_pdf.py`, `scripts/build_slides_pdf.py`, `scripts/evaluate_dev_segmentation_objective_i.py`) | Đọc bảng DEV/test aggregate đã commit hoặc feature table đã chuẩn bị; không mở raw order. | Báo cáo DQ, report/slide và đánh giá DEV. |
| Notebook `01_day1_development_eda.ipynb` | Đọc DuckDB read-only; truy vấn ngày DEV có điều kiện. | EDA DEV và hình schema. |
| Notebook `01b_eda_dev.ipynb` | Chỉ đọc file `outputs/`; tham chiếu `outputs/metrics/eda_dev_summary.json` hiện không có trong repo. | EDA hiển thị; không raw. |
| Notebooks `02_preprocess.ipynb`, `03_supervised.ipynb`, `04_unsupervised.ipynb`, `05_combo.ipynb` | Đọc bảng `outputs/` đã chuẩn bị; notebook tiền xử lý có guard chặn trạng thái test-open. | EDA/model/basket từ artifact; không truy cập raw trực tiếp. |

## Aggregate đã commit

Script `scripts/audit_committed_aggregate_dates.py` kiểm kê tất cả **89** CSV/JSON đã track trong `outputs/tables/` và `outputs/metrics/`: 22 file có cột/key thời gian, 67 file không có trường thời gian. CSV chỉ nạp cột có tên mang dấu thời gian; JSON chỉ báo key thời gian và max. Không phát hiện event-period sau T2. Mốc lớn nhất ngoại lệ là `calendar_end_inclusive=2026-10-31` trong `holiday_time_supplement_dev.json`, đây là lịch tham chiếu ngày lễ, không phải ngày đơn; các anchor số liệu dừng `2025-04-01`.

Các mốc lớn nhất còn lại: dashboard monthly `2026-04` (tháng chưa trọn, nguồn là aggregate cũ đã mở một lần; kết thúc tại 2026-04-20 loại trừ), `test_eval.json` `end_exclusive=2026-04-20`, các cube/revenue/gift monthly DEV `2025-10`, retention cohort `2025-08`, prevalence/revenue-driver cohort `2025-03`, quarter DEV `2025-Q4` (chỉ chứa phần tháng 10 trước 22/10), seasonality monthly `2025-10-01`, weekly `2025-10-20`, holiday event tối đa `2025-09-09`. Các bảng test segment/combo đã commit là aggregate của cửa sổ test cũ trước T2. Không thấy aggregate nào chứa event HO2 sau T2.

## Kho DuckDB và giới hạn

Truy vấn read-only chỉ lấy `MIN(local_date), MAX(local_date)` từ `data/restricted/xoaif_dev.duckdb`: **2024-04-01 đến 2025-10-21**. Vì vậy bản kho hiện tại không chứa order date sau T2. Hàng raw được cách ly trong code bằng timestamp-first gate và local-date bound; evaluator revision 2 đã có khóa mở một lần riêng và hiện chưa được gọi.

Hạn chế đã biết:

1. Trạng thái đơn trước T2 là trạng thái tại snapshot, có thể đã thay đổi sau T2; giữ nguyên quy ước hiện tại.
2. Đơn có local date đúng **2026-04-20** không thuộc feature history (`date<T2`) và không thuộc outcome (outcome bắt đầu `date>T2`).
3. Tổng **12.011** dòng snapshot là số đã biết trước khóa; kiểm toán này không quét nội dung raw để tái đếm.
4. Cách ly được chứng minh bằng cổng mã, hash/metadata và đầu ra aggregate; không phải chứng cứ pháp y về thao tác ngoài repo hoặc truy cập thủ công.
5. Tháng 2026-04 trong dashboard aggregate là tháng partial của test cũ, không thể diễn giải như đủ tháng; lịch ngày lễ 2026 là reference metadata chứ không phải quan sát bán hàng.

Kiểm toán này không cấp quyền mở HO2 và không bắt đầu Phase C.
