# Tóm tắt Ngày 2

## Kết quả chính

- **Quy tắc tiền:** 6.400 đơn status 3 trong `[2024-04-01,2025-10-22)`. Doanh thu ghi nhận dùng `after_sub_discount-shipping_fee`, với ngoại lệ đã ghi trong amendment 03. Có 22 đơn tặng; 2 đơn doanh thu âm (0,03%), Monetary bằng 0 nhưng vẫn nằm trong F/R. Cổng dừng 1% đạt. Điều chỉnh dương chiếm 10,21%, âm 0,13%; tổng điều chỉnh ròng 52.016.532 đ (1,98% tổng doanh thu ghi nhận).
- **Preprocess và nhãn:** 6.400 đơn status 3; 286 thiếu customer ID nên loại khỏi mức khách; 22 đơn quà bị loại khỏi hành vi; 5 đơn không có dòng hàng bị loại khỏi giỏ. Đặc trưng gồm R/F/Monetary, giá trị đơn TB/lớn nhất, số lượng, product phân biệt, khoảng cách mua, tháng đầu, tỉnh/thành, adjustment dương/âm và khoảng cách từ lần mua cuối đến lễ gần nhất. Tết dùng ngày mùng 1 được công bố chính thức: 10-02-2024 ([Chính phủ](https://xaydungchinhsach.chinhphu.vn/danh-sach-cac-diem-ban-phao-hoa-tai-tp-hcm-dip-tet-nguyen-dan-giap-thin-2024-119240125193656008.htm)) và 29-01-2025 ([Chính phủ](https://xaydungchinhsach.chinhphu.vn/danh-sach-cac-diem-ban-phao-hoa-dip-tet-duong-lich-2025-va-tet-nguyen-dan-at-ty-tai-ha-noi-119241230172030261.htm)). Tập nhãn gồm 3.508 mẫu nhãn qua nhiều mốc T, 260 dương (7,41%); mốc nhãn xa nhất kết thúc 2025-10-05, trước `test_start`. Theo quy tắc ghi trước, ngưỡng tối thiểu 100 mẫu dương và 5% đều đạt.
- **Tần suất mua:** trong cohort scoring có 4.530/5.169 khách có một đơn (87,6%). DEV status 3 có 4.526/5.174 khách có một đơn (87,5%). Hai tỷ lệ dùng cohort và mẫu số khác nhau.
- **Khách giá trị lớn:** proxy là Monetary hoặc giá trị đơn lớn nhất đạt phân vị 99 trong dev. Ngưỡng Monetary 3.439.576 VND; ngưỡng giá trị đơn 3.082.176 VND; 62 khách nằm trong proxy. Đây không phải phân loại pháp lý/doanh nghiệp.
- **Phân khúc:** K=2; silhouette=0,508. Trong cohort scoring có 4.530/5.169 khách một đơn (87,6%); F ít phân tách. Đặt tên cụm theo số liệu:
  - Cụm 0 — Chủ yếu mua một lần: 4.523 khách, tần suất TB 1,00, Monetary TB 370.154 đ, 65,72% Monetary toàn tập, 26 khách thuộc proxy giá trị lớn.
  - Cụm 1 — Khách mua lặp lại: 646 khách, tần suất TB 2,42, Monetary TB 1.351.787 đ, 34,28% Monetary toàn tập, 36 khách thuộc proxy giá trị lớn.
  - Diễn giải K=2: phân đoạn mô tả theo tần suất mua (một lần / lặp lại); điều này không chứng minh các nhóm có ý nghĩa kinh doanh hoặc giúp ra quyết định tốt hơn.
### Phân loại quay lại

Expanding temporal folds có khoảng đệm `N+L=187` ngày và khách rời nhau. Pipeline fit imputer, scaler và encoder chỉ trong train fold. Precision/Recall/F1 và ma trận nhầm lẫn bên dưới dùng ngưỡng xác suất mặc định 0,5.
Chọn mô hình/siêu tham số theo PR-AUC trung bình của 5 fold thời gian; chỉ 1.558/3.508 mẫu có dự đoán OOF vì các cohort đầu không đủ khoảng đệm nhãn 187 ngày. Bảng dưới báo thêm điểm gộp trên OOF; hai cách tổng hợp có thể xếp hạng khác nhau.

| Mô hình | PR-AUC TB 5 fold | Precision OOF | Recall OOF | F1 OOF | ROC-AUC OOF | PR-AUC OOF gộp | TN/FP/FN/TP | Tham số |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| majority_baseline | 0,0599 | 0,00% | 0,00% | 0,00% | 0,5362 | 0,0671 | 1.464/0/94/0 | — |
| logistic_regression | 0,1093 | 5,87% | 46,81% | 10,44% | 0,5096 | 0,0699 | 759/705/50/44 | C=10 |
| decision_tree | 0,0910 | 9,20% | 32,98% | 14,39% | 0,5737 | 0,0798 | 1.158/306/63/31 | max_depth=8 |
| random_forest | 0,0839 | 15,79% | 6,38% | 9,09% | 0,5409 | 0,0735 | 1.432/32/88/6 | max_depth=16; min_samples_leaf=5 |

Logistic Regression được chọn theo trung bình fold (0,1093), nhưng PR-AUC gộp của Decision Tree cao nhất (0,0798 so với Logistic Regression 0,0699 và baseline 0,0671). Với Logistic Regression, ROC-AUC gộp 0,5096 gần mức ngẫu nhiên; Precision 5,87% và 705 FP so với 44 TP. Vì vậy mô hình hiện **chưa đủ tin cậy cho hành động khách hàng hoặc triển khai**; mức cải thiện so với baseline nhỏ và kết quả phụ thuộc cách gộp fold.

Theo D-005, Logistic Regression C=10 — mô hình chính theo D-005 có DEV OOF ROC-AUC 0,5096, AP 0,0699 trên 1.558 mẫu / 94 dương; PR-AUC trung bình 5 fold là 0,1093. Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính.

Decision Tree ở depth 8 có PR-AUC train 0,4323, validation 0,0910, khoảng cách 0,3413, cho thấy overfit. Theo phân khúc của mô hình được chọn: nhóm mua một lần PR-AUC 0,0747 (n=1.490); mua lặp lại 0,0986 (n=58, chỉ 7 dương); proxy giá trị lớn/tần suất thấp 0,1667 (n=10, chỉ 1 dương), nên hai nhóm sau không đủ mẫu để kết luận ổn định.
### Giỏ hàng

Có 6.031 giỏ status 3, không quà, ít nhất 2 product_id; dùng 6.031 giỏ cho luật. Chọn support 0,05 — mức cao nhất đã thử còn ít nhất 5 luật lift > 1, mỗi luật xuất hiện từ 5 giỏ — tạo 68 luật và 23 combo. Đây là đồng xuất hiện; combo đầu có giá niêm yết gộp 0 đ theo dữ liệu:
  - PORTCARD HƯỚNG DẪN CHĂM CÂY + TÚI GIẤY XOAIF GARDEN: xuất hiện 2.398 giỏ, support 39,761%, confidence 0,582, lift 1,324, giá niêm yết gộp 0 đ.
  - CẨM NHUNG + PORTCARD HƯỚNG DẪN CHĂM CÂY: xuất hiện 982 giỏ, support 16,283%, confidence 0,238, lift 1,010, giá niêm yết gộp 55.000 đ.
  - PHỤ KIỆN BẢNG TÊN + PORTCARD HƯỚNG DẪN CHĂM CÂY: xuất hiện 928 giỏ, support 15,387%, confidence 0,225, lift 1,028, giá niêm yết gộp 5.000 đ.
  - PORTCARD HƯỚNG DẪN CHĂM CÂY + TÚI MICA HÌNH THANG: xuất hiện 594 giỏ, support 9,849%, confidence 0,144, lift 1,159, giá niêm yết gộp 18.000 đ.
  - PHỤ KIỆN BẢNG TÊN + TÚI GIẤY XOAIF GARDEN: xuất hiện 586 giỏ, support 9,716%, confidence 0,221, lift 1,010, giá niêm yết gộp 5.000 đ.

## Độ nhạy

- A (total_price-total_discount): chênh tổng doanh thu ghi nhận 2,02% so với A; 642/6.378 đơn lệch trên 1%; Spearman Monetary theo khách 0,9953. Cụm đổi 0,02%, silhouette đổi +0,0017; PR-AUC của mô hình được chọn đổi +0,0003.
- B (loại đơn điều chỉnh hoặc chưa giải thích): bỏ 659 đơn không quà; cụm đổi 20,47%, Silhouette đổi +0,2385; PR-AUC đổi -0,0128.

Độ nhạy là kiểm tra mức phụ thuộc vào cách định nghĩa tiền; không chứng minh định nghĩa nào đúng hơn. `price_adjustment` ở mức đơn không được phân bổ xuống sản phẩm.

## Độ tin cậy và giới hạn

- Quy tắc amendment 03 thay đổi sau khi cổng amendment 02 báo 701/6.400 (10,95%) vượt 5%, dựa trên hiểu biết nghiệp vụ của chủ cửa hàng. Đây là thay đổi sau khi xem kết quả cổng cũ; kết quả cần được diễn giải cùng độ nhạy.
- Tỷ lệ điều chỉnh dương/`adj_unexplained` không cao nhất ở các tháng mở đầu; xem đỉnh và từng tháng tại `docs/money_audit.md`. Điều này gợi ý bất thường tập trung theo giai đoạn, không phải bằng chứng nguyên nhân.
- Nhãn dựa trên status hiện tại, không có lịch sử hoàn/đổi đủ để tái dựng trạng thái tại `T+N+L`. Đây là nhãn dự báo trong dev, không khẳng định nhân quả.
- Nhiều khách chỉ có một đơn, số khách dương hạn chế so với tổng mẫu; các chỉ số validation không đại diện độc lập cho mọi mùa vụ/khách tương lai.
- Chỉ có tỉnh/thành, không có tọa độ/mã vùng đủ chi tiết nên bỏ qua DBSCAN địa lý. Không có giá vốn nên không thể tính lợi nhuận.
- **[LỊCH SỬ — trước lần mở test duy nhất]** Test chưa mở, `test_labels_loaded=false`, `test_behavior_loaded=false`; khi đó chưa bắt đầu Ngày 3.

## Đầu ra

- Tiền: `docs/money_audit.md`, `outputs/tables/money_diagnosis.csv`, `outputs/metrics/day2_money_audit.json`.
- Khách/phân khúc: `outputs/tables/day2_features_primary.csv`, `outputs/tables/segments.csv`, `outputs/tables/segment_profiles.csv`, `outputs/figures/segments_elbow.png`, `outputs/figures/segments_silhouette.png`.
- Phân loại: `outputs/metrics/dev_final_model.json`, `outputs/models/day2_dev_final_model.joblib`, `outputs/figures/decision_tree_depth_curve.png`.
- Giỏ hàng: `outputs/tables/rules.csv`, `outputs/tables/combos.csv`.

## Ngày 2B — Vòng bổ sung có giới hạn

### Combo sau làm sạch

Trước làm sạch có 6.031 giỏ đủ ít nhất hai sản phẩm; bỏ 6.947 dòng giá niêm yết 0 và còn 5.684 giỏ đạt điều kiện. Fallback danh mục: không cần. Chọn support 0,05; 10 luật, 5 combo. Bảng giá chỉ cộng retail price dương đã quan sát; thiếu giá để NA, không phân bổ discount hay tính lợi nhuận.

Combo có nhiều giỏ nhất:
- CẨM NHUNG + PHỤ KIỆN BẢNG TÊN: 444 giỏ, support 7,81%, confidence 0,339, lift 1,365, leverage 0,0209, giá niêm yết gộp 60.000 đ.
- CHẬU TRỤ + CẨM NHUNG: 432 giỏ, support 7,60%, confidence 0,304, lift 1,226, leverage 0,0140, giá niêm yết gộp 125.000 đ.
- CHẬU TRỤ + PHỤ KIỆN BẢNG TÊN: 395 giỏ, support 6,95%, confidence 0,302, lift 1,208, leverage 0,0120, giá niêm yết gộp 75.000 đ.
- CHẬU TRỤ + ĐÔ LA NGỌC BÍCH: 350 giỏ, support 6,16%, confidence 0,414, lift 1,659, leverage 0,0245, giá niêm yết gộp 190.000 đ.
- CHẬU KIM CƯƠNG THẤP + SEN ĐÁ: 339 giỏ, support 5,96%, confidence 0,407, lift 2,950, leverage 0,0394, giá niêm yết gộp 65.000 đ.

Tệp `outputs/tables/companion_products_v2.csv` liệt kê tối đa 20 sản phẩm theo support. Tự động đề xuất bao bì/phụ kiện theo tên hoặc support trên 30%; danh sách còn chờ chủ dự án xác nhận và chưa dùng để lọc giỏ.

Rà soát tên cho thấy cách so khớp substring có thể đề xuất nhầm: “ĐÔ LA NGỌC BÍCH” khớp từ “bịch”, “CHẬU MOCHI” khớp từ “móc”. Đây là gợi ý tự động chưa xác nhận; cần chủ dự án rà danh sách trước khi dùng.

| Sản phẩm | Support | Giá niêm yết | Loại tự đề xuất | Đi kèm? |
|---|---:|---:|---|---|
| CHẬU TRỤ | 24,96% | 70.000 đ | Sản phẩm chính hoặc chưa rõ | không đề xuất |
| CẨM NHUNG | 24,82% | 55.000 đ | Sản phẩm chính hoặc chưa rõ | không đề xuất |
| PHỤ KIỆN BẢNG TÊN | 23,05% | 5.000 đ | Phụ kiện | đề xuất |
| ĐÔ LA NGỌC BÍCH | 14,87% | 120.000 đ | Bao bì/đóng gói | đề xuất |
| SEN ĐÁ | 14,64% | 30.000 đ | Sản phẩm chính hoặc chưa rõ | không đề xuất |
| CHẬU KIM CƯƠNG THẤP | 13,81% | 35.000 đ | Sản phẩm chính hoặc chưa rõ | không đề xuất |
| CHẬU MOCHI | 13,34% | 60.000 đ | Phụ kiện | đề xuất |
| TÚI MICA HÌNH THANG | 13,02% | 18.000 đ | Bao bì/đóng gói | đề xuất |
| KIM TIỀN | 11,95% | 120.000 đ | Sản phẩm chính hoặc chưa rõ | không đề xuất |
| HỒNG MÔN | 10,42% | 180.000 đ | Sản phẩm chính hoặc chưa rõ | không đề xuất |

### Phân khúc

K=2 giữ nguyên từ Ngày 2. K=3/4 chạy 5 seed định trước; ARI giữa các seed và giữa doanh thu chính/B tính trên 5.169 khách chung. Nhóm theo quy tắc mang tiền tố **Theo quy tắc nghiệp vụ**; proxy giá trị lớn dùng p99 Monetary hoặc p99 đơn lớn nhất, đồng thời Frequency không vượt p25. Không nhóm nào mang nhãn “nguy cơ rời bỏ”.

| Nhánh | Cụm/nhóm | Khách | Doanh thu ghi nhận (đ) | Tỷ trọng | Recency TB (ngày) | Frequency TB | Monetary TB (đ) | Proxy giá trị lớn |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| K=2 frozen | Chủ yếu mua một lần | 4.523 | 1.674.204.729 | 65,72% | 276,6 | 1,00 | 370.154 | 26 |
| K=2 frozen | Khách mua lặp lại | 646 | 873.254.612 | 34,28% | 218,5 | 2,42 | 1.351.787 | 11 |
| K=3 seed=42 | K=3 cụm 0: đơn lẻ lâu rồi, R TB 405 ngày | 2.476 | 1 tỷ 24.745.523 | 40,23% | 405,1 | 1,00 | 413.871 | 21 |
| K=3 seed=42 | K=3 cụm 1: mua lặp lại, F TB 2,43 | 637 | 856.796.452 | 33,63% | 219,0 | 2,43 | 1.345.049 | 8 |
| K=3 seed=42 | K=3 cụm 2: đơn lẻ gần đây, R TB 121 ngày | 2.056 | 665.917.366 | 26,14% | 121,4 | 1,00 | 323.890 | 8 |
| K=4 seed=42 | K=4 cụm 0: đơn lẻ lâu rồi, R TB 430 ngày | 1.722 | 401.595.647 | 15,76% | 429,5 | 1,00 | 233.215 | 0 |
| K=4 seed=42 | K=4 cụm 1: mua lặp lại, F TB 2,45 | 629 | 779.164.542 | 30,59% | 218,9 | 2,45 | 1.238.735 | 0 |
| K=4 seed=42 | K=4 cụm 2: giá trị cao, M TB 887.786 đ | 1.035 | 918.858.536 đ | 36,07% | 304,9 | 1,00 | 887.786 đ | 37 |
| K=4 seed=42 | K=4 cụm 3: đơn lẻ gần đây, R TB 112 ngày | 1.783 | 447.840.616 | 17,58% | 111,7 | 1,00 | 251.173 | 0 |
| Theo quy tắc nghiệp vụ | Theo quy tắc nghiệp vụ — Giá trị cao | 1.281 | 1.394.132.251 | 54,73% | 261,3 | 1,57 | 1.088.316 | 0 |
| Theo quy tắc nghiệp vụ | Theo quy tắc nghiệp vụ — Giá trị lớn, tần suất thấp | 37 | 200.582.266 | 7,87% | 280,4 | 1,00 | 5.421.142 | 37 |
| Theo quy tắc nghiệp vụ | Theo quy tắc nghiệp vụ — Mua lặp lại | 186 | 63.505.500 | 2,49% | 226,9 | 2,05 | 341.427 | 0 |
| Theo quy tắc nghiệp vụ | Theo quy tắc nghiệp vụ — Mua một lần gần đây | 1.832 | 439.929.216 | 17,27% | 128,2 | 1,00 | 240.136 | 0 |
| Theo quy tắc nghiệp vụ | Theo quy tắc nghiệp vụ — Mua một lần đã lâu | 1.833 | 449.310.108 | 17,64% | 420,0 | 1,00 | 245.123 | 0 |

| K | ARI TB giữa seed | ARI nhỏ nhất | ARI chính/B TB | Silhouette TB |
|---:|---:|---:|---:|---:|
| K=3 | 0,9997 | 0,9993 | 0,6214 | 0,3901 |
| K=4 | 0,9934 | 0,9839 | 0,5876 | 0,3853 |

### Mua lại với đặc trưng đơn gần nhất

Một lượt thử, 30 cấu hình đã đăng ký, 5 temporal folds và bootstrap paired 2.000 lần. Mô hình cũ Logistic Regression C=10 vẫn được giữ nguyên; không thay bằng Decision Tree dù AP OOF gộp trước đó cao hơn. Lượt mới chọn **logistic_regression** theo PR-AUC trung bình fold 0,0839; AP OOF gộp là 0,0645.

| Mô hình | PR-AUC TB fold | ROC-AUC OOF | PR-AUC OOF gộp | Precision | Recall |
|---|---:|---:|---:|---:|---:|
| majority_baseline | 0,0599 | 0,5362 | 0,0671 | 0,00% | 0,00% |
| logistic_regression | 0,0839 | 0,4969 | 0,0645 | 5,68% | 32,98% |
| decision_tree | 0,0813 | 0,5382 | 0,0804 | 6,37% | 44,68% |
| random_forest | 0,0803 | 0,5340 | 0,0747 | 8,57% | 3,19% |

Mô hình được chọn có CI 95% ROC-AUC [0,4330, 0,5599], CI PR-AUC [0,0490, 0,0914], CI chênh PR-AUC so baseline [-0,0193, 0,0204]. Tiêu chí tín hiệu yêu cầu cận dưới ROC >0,55 **và** cận dưới chênh AP >0. Kết quả: **không đủ bằng chứng để dự đoán mua lại từ dữ liệu hiện có**. Đây là kết luận hợp lệ; không chạy thêm biến thể. Chỉ số theo phân khúc có mẫu nhỏ được gắn cảnh báo.

**Cập nhật sau lần mở test duy nhất:** đoạn trên mô tả kết quả DEV tại thời điểm Day 2B. Amendment 05 ghi cho classifier cận dưới CI ROC-AUC > 0,55 và cận dưới paired ΔAP CI > 0. CI aggregate của cả Logistic Regression C=10 — mô hình chính theo D-005 và Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính thỏa các cận về mặt số liệu trong lần chạy thực tế. Tuy nhiên ROC-AUC DEV OOF C=10 là 0,5096, gần ngẫu nhiên; ROC-AUC test khoảng 0,70 chỉ là tín hiệu yếu chưa được development xác nhận, không đủ để kết luận mô hình hoạt động tốt. Test đã mở; không dùng để tiếp tục tinh chỉnh hay chọn lại mô hình. Cấu hình ghi `>T`, evaluator dùng `[T,end)` gồm ngày T; ảnh hưởng chưa xác định. **Cấu hình ghi >T, evaluator dùng [T,end) (gồm ngày T); ảnh hưởng chưa xác định; đây là kết quả số liệu của lần chạy thực tế, không phải khẳng định tuân thủ đầy đủ giao thức, không gọi là 'đạt cổng ghi trước'.** Xem `docs/test_provenance_note.md`; không rerun test.

| Nhóm theo quy tắc nghiệp vụ | Mẫu OOF | Dương | PR-AUC | ROC-AUC | Cảnh báo |
|---|---:|---:|---:|---:|---|
| Theo quy tắc nghiệp vụ — Giá trị cao | 497 | 71 | 0,12627942692483368 | 0,4266018647093831 | đủ hơn 20 mẫu dương |
| Theo quy tắc nghiệp vụ — Giá trị lớn, tần suất thấp | 10 | 0 | 0,0 | NA | mẫu dương <20 |
| Theo quy tắc nghiệp vụ — Mua lặp lại | 48 | 23 | 0,32107166879401583 | 0,12173913043478261 | đủ hơn 20 mẫu dương |
| Theo quy tắc nghiệp vụ — Mua một lần gần đây | 525 | 0 | 0,0 | NA | mẫu dương <20 |
| Theo quy tắc nghiệp vụ — Mua một lần đã lâu | 478 | 0 | 0,0 | NA | mẫu dương <20 |

### Hủy/hoàn và nhật ký thử nghiệm

Hủy/hoàn: Gate không đạt; dương mỗi fold: F1: 30 / 1330, F2: 13 / 801, F3: 6 / 920, F4: 1 / 726, F5: 18 / 1007. Không fit mô hình theo ngưỡng đã ghi trước. Tổng status 5/6 dương sau khi bỏ status-3 quà: 117; số mô hình đã fit: 0.

- repurchase_v2: 1/1 lượt; 30 candidate evaluations; retry sau kết quả 0.
- cancel_refund_optional: 0/1 lượt; 0 candidate evaluations; retry sau kết quả 0.

**[LỊCH SỬ — trước lần mở test duy nhất]** Test vẫn đóng, không có nhãn/hành vi test trong đầu vào; khi đó Day 3 chưa bắt đầu. Metric DEV chi tiết nằm trong `outputs/metrics/dev_final_models_v2.json`, `day2b_baskets.json`, `day2b_segmentation.json` và `day2b_cancel_model.json`. Trạng thái hiện hành: `docs/test_provenance_note.md`.
