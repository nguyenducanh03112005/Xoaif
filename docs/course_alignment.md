# Ánh xạ dự án với giáo trình môn học

Các ánh xạ dưới đây ghi theo chủ đề/chương của giáo trình *Kho dữ liệu và kỹ thuật khai phá dữ liệu* (2018), không trích nguyên văn. Phạm vi hiện tại chỉ gồm WP5 và nền tảng chung; các WP khác sẽ bổ sung sau khi được duyệt.

| Khái niệm môn học | Nơi áp dụng trong dự án | File |
|---|---|---|
| Chương 1: quy trình KDD, phân loại có giám sát | Đánh giá mua lại và phân biệt thiết kế mẫu với khả năng dự đoán | `src/features/day2_data.py`, `src/models/classify.py`, `src/models/repurchase_v3.py` |
| Chương 1: kiểu dữ liệu và mẫu dữ liệu | Snapshot khách–mốc T, đặc trưng chỉ từ dữ liệu trước T, nhãn tương lai trong DEV | `docs/analysis_plan_wp5.md`, `src/features/repurchase_v3.py` |
| Chương 3: kho dữ liệu đa chiều và hỗ trợ quyết định | Cohort theo thời gian, kiểm tra phân phối recency/frequency và trình bày metric theo fold | `docs/cohort_definitions.md`, `docs/cohort_mismatch_analysis.md` |
| Chương 4: tiền xử lý dữ liệu | Fit imputation/scale/encoding trong từng train fold để tránh rò rỉ | `src/models/classify.py`, `src/models/repurchase_v3.py` (dự kiến) |
| Chương 4: đánh giá mô hình phân loại | Temporal CV, ROC-AUC, AP, precision@k, lift/gain và calibration trên DEV | `docs/analysis_plan_wp5.md`, `outputs/metrics/repurchase_v3_dev.json` |
| Mở rộng thống kê ngoài phần mục lục đã đối chiếu: bootstrap theo cụm khách | Khoảng bất định tôn trọng việc một khách có nhiều snapshot | `docs/analysis_plan_wp5.md`, `scripts/analyze_repurchase_v3_dev.py` |
