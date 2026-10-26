# Đầu vào dự kiến cho dashboard Ngày 3

Danh sách dưới đây dùng đầu ra đã rà PII. Mã khách trong bảng khách là HMAC giả danh; không có order_id, tên khách, điện thoại hoặc địa chỉ. Hình hiện là bản phát triển; chưa có chỉ số test.

- `outputs/tables/segments.csv` — một dòng/khách: `customer_key` (giả danh), `cluster_id`, `cluster_name`, `rule_segment`, `business_like_proxy`, Recency, Frequency, Monetary, giá trị đơn TB/lớn nhất, số lượng, số sản phẩm phân biệt, khoảng cách mua trung bình, tháng đơn đầu, khoảng cách holiday, tỉnh/thành đã chuẩn hóa, tỷ lệ adjustment dương/âm, tỷ trọng doanh thu cụm. Nguồn: feature snapshot trước `test_start`.
- `outputs/tables/segment_profiles.csv` — mỗi cụm: quy mô, Recency/Frequency/Monetary và giá trị đơn trung bình/trung vị, số proxy giá trị lớn, Monetary gộp và tỷ trọng. Dùng cho thẻ/phân tích cụm.
- `outputs/tables/rules.csv` — `antecedent_products`, `consequent_products`, combo, support, confidence, lift, số giỏ xuất hiện, giá niêm yết gộp nếu đủ giá. Không có khóa khách/đơn.
- `outputs/tables/combos.csv` — combo duy nhất cùng tên sản phẩm, số lần, độ đo luật, giá niêm yết gộp và ghi chú chất lượng.
- `outputs/tables/money_diagnosis.csv` — pattern tiền, phân vị/tổng price adjustment và tỷ lệ theo tháng; chỉ số tổng hợp không có mã giao dịch.
- `outputs/metrics/day2_money_audit.json`, `day2_label_audit.json`, `day2_segmentation.json`, `dev_final_model.json`, `day2_baskets.json` — metadata/phạm vi, counts, độ đo dev, ngưỡng và trạng thái không mở test; dashboard chỉ đọc trường tổng hợp cần thiết.
- `outputs/figures/segments_elbow.png`, `segments_silhouette.png`, `decision_tree_depth_curve.png` — hình đánh giá K và độ sâu cây trên dev.

**[LỊCH SỬ — trước lần mở test duy nhất]** Khi ghi danh sách này chưa có đầu vào test và dashboard Ngày 3 chưa bắt đầu. Test đã được mở một lần sau đó; xem `docs/test_provenance_note.md`. Không đọc `outputs/tables/day2_label_samples_*.csv` vào dashboard chung vì có nhãn phát triển theo khách; không đọc `outputs/models/day2_dev_final_model.joblib` trong dashboard.


## Đầu vào Day 2B đã rà PII

- `outputs/tables/segments_v2.csv` — mỗi dòng là một customer HMAC giả danh; gồm K=2/3/4, tên cụm, nhóm theo quy tắc, proxy p99 và R/F/Monetary. Không có order key hay nhãn.
- `outputs/tables/segment_profiles_v2.csv` — quy mô, doanh thu ghi nhận/tỷ trọng, Recency, Frequency, Monetary và số proxy giá trị lớn theo từng scheme.
- `outputs/tables/companion_products_v2.csv` — tên sản phẩm, support, retail price, loại gợi ý; xác nhận của chủ dự án đang pending.
- `outputs/tables/rules_v2.csv`, `combos_v2.csv` — sản phẩm, support, confidence, lift, leverage, occurrences, giá niêm yết gộp nếu đủ giá và cờ companion; không có order/customer key.
- `outputs/metrics/day2b_baskets.json`, `day2b_segmentation.json`, `day2b_cancel_model.json`, `dev_final_models_v2.json` — chỉ tổng hợp dev, trạng thái cổng, CI và hash; dashboard chỉ chọn trường aggregate.
- Hình `outputs/figures/segments_v2_stability.png`; nếu gate hủy/hoàn đạt, `outputs/figures/cancel_tree_depth_curve_v2.png`.

**[LỊCH SỬ — trước lần mở test duy nhất]** Khi ghi đoạn này Day 3 chưa bắt đầu và chưa có đầu vào test. Không đưa `outputs/tables/day2_label_samples_*.csv`, mô hình joblib hay dự đoán theo khách vào dashboard. Trạng thái test và diễn giải hiện hành: `docs/test_provenance_note.md`.
