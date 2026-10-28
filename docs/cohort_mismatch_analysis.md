# Chẩn đoán cohort DEV — WP5

**Nhãn bắt buộc:** khám phá, chưa xác nhận ngoài mẫu. Không thay mô hình chính D-005. Không đọc nhãn/hành vi test hoặc đặc trưng test cấp khách; đối chiếu test chỉ dùng các aggregate đã commit trong `outputs/tables/test_segment_profiles.csv`.

## Kết luận về nghi vấn cohort

Mã xác nhận cấu trúc mẫu DEV cũ khác snapshot scoring. `build_label_samples` chỉ gán một mốc T đầu tiên cho mỗi khách; vì vậy các khách thường mới có lịch sử ngắn tại snapshot đó. Phân tích mới tạo 21.638 snapshot khách–T từ 3.508 khách duy nhất qua 12 mốc tháng đủ điều kiện; mỗi snapshot chỉ dùng đơn DEV hợp lệ, không quà, trước T. Temporal CV có 5 fold validation vì các mốc đầu chưa có train label trưởng thành đủ N+L. Một khách có thể lặp lại ở các T/fold; nhãn train phải trưởng thành trước T validation.

| Universe | Snapshot / khách | Recency ngày: trung bình; P25 / trung vị / P75 | Frequency: trung bình; P25 / trung vị / P75 |
|---|---:|---:|---:|
| Mẫu DEV hiện tại, một mẫu/khách | 3.508 / 3.508 | 15,8; 9 / 15 / 23 | 1,056; 1 / 1 / 1 |
| DEV snapshot đa mốc | 21.638 / 3.508 | 118,6; 45 / 103 / 173,8 | 1,135; 1 / 1 / 1 |
| Cohort scoring test, aggregate pre-T | 5.169 / 5.169 | trung bình 269,3; quantile không có trong aggregate | trung bình 1,179; quantile không có trong aggregate |

Khoảng 95% bootstrap theo khách cho trung bình recency là 15,51–16,04 ngày ở mẫu cũ và 116,94–120,38 ngày ở snapshot đa mốc; cho frequency lần lượt 1,047–1,065 và 1,119–1,152. Snapshot đa mốc dùng cụm khách làm đơn vị lấy mẫu, giữ các T của cùng khách cùng nhau. Test chỉ có trung bình từ profile gộp, nên không tính CI/quantile tương thích và không so sánh phân phối đầy đủ.

**Mức bằng chứng:** B cho nhận định rằng mẫu cũ và các snapshot scoring có lịch sử/recency khác nhau về cấu trúc và thống kê mô tả. C cho nhận định rằng khác biệt cohort giải thích chênh lệch AUC DEV–test: chưa có đối chiếu cùng một thiết kế ngoài mẫu, test aggregate không có phân phối đầy đủ, và định nghĩa cửa sổ test có sai khác `>T`/`[T,end)` đã được ghi ở D-010. Không kết luận nguyên nhân chênh 0,51 so với 0,70.

### Bổ sung về prevalence và metric

Prevalence OOF của DEV snapshot đa mốc là **4,17%** (600/14.394); aggregate test ghi **4,59%** (237/5.169); mẫu DEV cũ là **7,41%** (260/3.508). Khoảng cách prevalence 0,42 điểm phần trăm giữa OOF đa mốc và test nhỏ hơn khoảng cách 3,24 điểm giữa OOF đa mốc và mẫu DEV cũ. Đây là **bằng chứng gián tiếp mức B** rằng prevalence của DEV đa mốc gần cohort test hơn. Mẫu số và giao thức khác nhau; điều này không chứng minh hai quần thể tương đương, cũng không xác định nguyên nhân chênh AUC.

Ở cùng snapshot/fold WP5, ROC-AUC v3 (0,555) thấp hơn recency-only (0,595) và frequency-only (0,591). AP v3 (0,064) cao hơn recency-only (0,062) một chút nhưng thấp hơn frequency-only (0,099); các CI bootstrap chồng lấp. Decile điểm thấp nhất của v3 có tỷ lệ mua lại 5,69%, cao hơn decile 4–9 (2,15%–4,03%). Xếp hạng v3 không đơn điệu. Diễn giải phù hợp là **mô hình phức tạp chưa đem lại giá trị nhất quán** trên bộ kiểm tra này.

## Giải thích ROC-AUC baseline 0,536

Chạy lại đúng baseline fold-local trên mẫu DEV cũ cho pooled ROC-AUC **0,53617** (1.558 dự đoán OOF), khớp số đã báo cáo. Trong từng fold, baseline gán cùng một xác suất cho mọi khách nên ROC-AUC của cả 5 fold đều **0,5**. Xác suất nền train thay đổi giữa fold từ 0,0851 đến 0,0891; khi gộp OOF, các giá trị khác nhau tạo thứ hạng giữa fold và ROC pooled vượt 0,5, dù baseline không xếp hạng khách bên trong fold. Vì vậy 0,536 không phải tín hiệu phân biệt khách của baseline; đó là hệ quả của cách gộp score fold-local. Baseline chung của WP5 giữ một xác suất từ train fold đầu tiên cho mọi OOF snapshot và có pooled ROC-AUC 0,5.

## So sánh cố định trên DEV

Giao thức `docs/analysis_plan_wp5.md` được giữ nguyên sau khi đăng ký. Bốn chiến lược chạy trên cùng 5 validation fold: baseline hằng số chung; Logistic Regression chỉ recency; chỉ frequency; Logistic Regression v3. Có 14.394 dự đoán OOF, 3.508 khách duy nhất và 600 nhãn dương (4,17%) trong phần OOF. Khoảng 95% dùng bootstrap theo khách 2.000 lần, seed 20261028.

| Chiến lược | ROC-AUC pooled OOF (95% CI) | AP pooled OOF (95% CI) | Brier |
|---|---:|---:|---:|
| Baseline hằng số chung | 0,500 (0,500–0,500) | 0,0417 (0,0361–0,0479) | 0,0421 |
| Chỉ recency | 0,595 (0,559–0,633) | 0,0624 (0,0522–0,0765) | 0,1255 |
| Chỉ frequency | 0,591 (0,551–0,631) | 0,0989 (0,0681–0,1439) | 0,2445 |
| Logistic Regression v3 | 0,555 (0,515–0,595) | 0,0641 (0,0507–0,0836) | 0,1172 |

Các giá trị theo từng fold nằm ở `outputs/tables/repurchase_v3_dev_fold_metrics.csv`; pooled metric và CI ở `outputs/metrics/repurchase_v3_dev.json`. Không chọn cấu hình chiến thắng hay thay D-005. Kết quả cho thấy v3 không vượt rõ các baseline đơn giản trong phép chạy này; khoảng AP rộng và các snapshot có lặp khách làm độ bất định đáng kể.

## Chỉ số hướng hành động của Logistic Regression v3

- Decile đầu: 8,27% mua lại quan sát, lift 1,98 lần prevalence OOF; bootstrap 95% tỷ lệ 6,22%–10,45%. Decile đầu không chiếm hết lợi thế: đường lift không đơn điệu ở các decile thấp.
- Precision@5%: 11,25% (95% CI 7,87%–15,04%); @10%: 8,26% (6,22%–10,45%); @20%: 6,63% (5,34%–7,97%). Đây là tỷ lệ quan sát trong OOF DEV, không phải uplift và không phải kết quả dự kiến khi gửi ưu đãi.
- Decile 1/2/3 tích lũy bắt lần lượt 19,8% / 31,8% / 41,3% số dương OOF. Bảng đầy đủ và CI cho tỷ lệ từng decile nằm ở `outputs/tables/repurchase_v3_dev_deciles.csv`.
- Calibration kém: nhóm điểm cao nhất có xác suất dự đoán trung bình 63,7% nhưng tỷ lệ mua lại quan sát 8,26%; Brier 0,117 so với 0,042 của baseline chung. Không dùng điểm xác suất v3 như xác suất mua lại đã hiệu chỉnh.
- Một giả thuyết cần kiểm tra ở WP5b là `class_weight="balanced"` làm lệch xác suất dự đoán khỏi prevalence thực và góp phần vào calibration kém. Đây chưa phải kết luận. Brier của các score chưa hiệu chỉnh được ghi riêng; chênh lệch Brier không được diễn giải riêng như chênh lệch khả năng xếp hạng.

## Phạm vi, truy vết và các lượt chạy

Nguồn DEV: `load_dev_orders()` chỉ dùng status 3 trong DEV, loại quà theo quy tắc hiện hành; hàm chỉ đọc `inserted_at` để loại record ngoài DEV trước khi truy cập trường khác. Nguồn đối chiếu test duy nhất là aggregate pre-T nói trên; script chỉ đọc cột cohort, scheme, số khách, mean recency và mean frequency. Không tạo nhãn hay đặc trưng test.

Script `scripts/analyze_repurchase_v3_dev.py`; snapshot `20261024T052943Z`. Các snapshot/feature cấp khách chỉ ở RAM, không ghi file. Output đã qua kiểm tra chỉ gồm số đếm, metric, CI và bảng tổng hợp. Metadata trong `outputs/metrics/repurchase_v3_dev.json` ghi hash kế hoạch và nhật ký các lượt đầu dừng vì hiệu năng/serialize trước khi artifact được ghi; lượt cuối giữ nguyên giao thức đăng ký.

Không tuyên bố nhân quả, lợi nhuận hoặc khả năng tổng quát hóa. Mọi kết quả WP5 ở đây là DEV-only, khám phá, chưa xác nhận ngoài mẫu.
