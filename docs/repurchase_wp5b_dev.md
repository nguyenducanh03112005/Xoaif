# WP5b — chiến lược mua lại dễ diễn giải (DEV-only)

**Nhãn:** khám phá, chưa xác nhận ngoài mẫu. Không dùng để thay mô hình chính D-005. Không đọc test raw, nhãn hay hành vi; không chạy `evaluate_test_once.py`. Test không tham gia chọn mô hình.

## Đăng ký trước và cách chạy

Giao thức ở [`analysis_plan_wp5b.md`](analysis_plan_wp5b.md), SHA-256 `ed9af7f35e03a41f2462462361f8476ba2b25dee89c6cd59340512419fcdd931`; hash trong metric khớp file đăng ký trước. Cùng mẫu WP5 gồm 21.638 snapshot khách–T từ 3.508 khách, 5 fold theo thời gian; OOF có 14.394 snapshot, 600 nhãn mua lại (4,17%). Bootstrap theo khách 2.000 lượt, seed 20261028.

Đã đăng ký năm chiến lược: (S1) `frequency >= 2`; (S2) luật tần suất với ngưỡng recency chọn trong train từ 30/60/90/180 ngày; (S3) cây độ sâu tối đa 3, lá tối thiểu 50; (S4) LR không `class_weight` với hiệu chỉnh sigmoid từ inner temporal OOF; (S5) LR v3 đã dùng ở WP5 làm tham chiếu. S2 và S4 không có inner fold thời gian hợp lệ trong bất kỳ outer fold nào, nên không tạo dự đoán. Tất cả 10 lần thất bại (hai chiến lược × năm fold), lý do theo từng fold, được lưu ở `outputs/metrics/repurchase_wp5b_dev.json`. Không thay bằng random split hay ngưỡng định trước sau khi thấy kết quả.

## Metric theo fold và pooled OOF

| Chiến lược | AP trung bình 5 fold | AP pooled (95% CI theo khách) | ROC-AUC pooled (95% CI) | Brier pooled |
|---|---:|---:|---:|---:|
| S1 luật frequency≥2 | 0,0668 | 0,0659 (0,0520–0,0837) | 0,605 (0,573–0,640) | 0,1238* |
| S3 cây nông | 0,0665 | 0,0745 (0,0586–0,0924) | 0,623 (0,587–0,658) | 0,0445 |
| S5 Logistic v3 | 0,0694 | 0,0641 (0,0507–0,0836) | 0,555 (0,515–0,595) | 0,1172 |

AP fold-by-fold, prevalence, số dương, ROC-AUC và Brier nằm ở `outputs/tables/repurchase_wp5b_fold_metrics.csv`; pooled metric nằm ở JSON. Khoảng tin cậy là bootstrap theo khách, không theo từng snapshot độc lập. Các khoảng AP chồng lấp; không có cơ sở gọi S3 là mô hình thắng ổn định. `*` Brier S1 dùng điểm nhị phân, không phải xác suất hiệu chỉnh; không so sánh trực tiếp với Brier mô hình xác suất.

## Chỉ số hướng hành động và calibration

| Chiến lược | Precision@5% (95% CI) | @10% (95% CI) | @20% (95% CI) | Lift top 10% so prevalence |
|---|---:|---:|---:|---:|
| S1 luật frequency≥2 | 10,28% (9,10–16,14%) | 12,15% (9,13–15,44%) | 8,37% (6,84–10,40%) | 2,92 |
| S3 cây nông | 12,50% (8,84–16,23%) | 10,28% (7,75–12,66%) | 8,37% (6,81–10,10%) | 2,47 |
| S5 Logistic v3 | 11,25% (7,87–15,04%) | 8,26% (6,22–10,45%) | 6,63% (5,34–7,97%) | 1,98 |

Đây là tỷ lệ mua lại quan sát trong validation DEV, không phải uplift, hiệu quả chiến dịch hay dự báo phản hồi. `outputs/tables/repurchase_wp5b_deciles.csv` và `repurchase_wp5b_top_k.csv` có cả metric theo từng fold và pooled; khoảng tin cậy đầy đủ của precision/decile nằm trong JSON.

Calibration pooled trên OOF: S3 có intercept −2,887 (95% CI bootstrap −3,137 đến −2,336), slope 0,087 (0,014–0,308), Brier 0,0445; S5 có intercept −3,143 (−3,324 đến −2,965), slope −0,005 (−0,053–0,065), Brier 0,1172. Slope S5 CI bao gồm 0; điểm số v3 không có liên hệ đơn điệu rõ với log-odds quan sát trong pooled OOF. Đây là mô tả, không phải kiểm định xác nhận. S1 điểm 0/1 không có slope/intercept hữu ích nên để trống. Reliability bins ở `outputs/tables/repurchase_wp5b_calibration.csv`.

Decile pooled không đơn điệu với bất kỳ chiến lược hoàn chỉnh nào: S1 có 2 vi phạm kề, S3 và S5 có 4 vi phạm kề. Điểm bằng nhau có thể tách qua decile theo khóa khách; điều này làm bảng decile thô nhiễu hơn cho luật rời rạc. Quy tắc đăng ký trước yêu cầu chiến lược hoàn chỉnh và đơn điệu, vì vậy **không có ứng viên được chọn**. Quyết định này không được nới sau khi xem kết quả.

Cây nông được fit theo outer fold và bảng IF–THEN được lưu ở `outputs/tables/repurchase_wp5b_tree_rules.csv`. Do lớp mua lại hiếm và giới hạn lá 50, các lá đều dự đoán lớp 0 tại ngưỡng mặc định; xác suất lá được dùng để xếp hạng. Cây hiện chưa cung cấp rule phân loại dương phù hợp để kích hoạt chăm sóc.

## Kết luận và giới hạn

- Trong phép chạy này, S3 AP pooled cao hơn S1 và S5, nhưng khoảng AP chồng lấp, mean fold AP của S5 cao nhất trong ba chiến lược hoàn chỉnh, và cả ba không đạt điều kiện decile đơn điệu. Không chọn ứng viên.
- Giả thuyết `class_weight="balanced"` gây calibration kém **chưa kiểm chứng được**: S4 không thể fit/hiệu chỉnh theo giao thức inner temporal CV vì không có fold inner hợp lệ trong cả 5 outer fold. Không kết luận class weighting là nguyên nhân, và không tạo phương pháp thay thế hậu nghiệm.
- S2 cũng không thể chọn ngưỡng theo CV; các ngưỡng 30/60/90/180 không có kết quả so sánh hợp lệ và không được thử trực tiếp trên outer validation.
- Các kết quả xác nhận nhận xét WP5 rằng Logistic v3 không có lợi thế ổn định trước chiến lược đơn giản trong temporal CV DEV. Mức bằng chứng C cho lựa chọn vận hành; chưa có xác nhận ngoài mẫu. Chênh lệch AUC DEV–test vẫn chưa quy nguyên nhân.
- D-005 vẫn là mô hình chính theo quyết định hiện hành; không thay đổi pipeline triển khai.

## Nhật ký thực thi

Giao thức không đổi sau đăng ký. Nhật ký mọi lượt: (1) trước fit, script đọc nhầm tên khóa metadata và dừng; (2) mô hình fit xong nhưng bước ghép decile dừng vì cột `as_of` lặp; (3) lượt tiếp theo bổ sung bootstrap calibration, tạo artifact tạm nhưng pooled decile bị lặp; (4) sau sửa bảng pooled, OpenBLAS báo lỗi cấp phát trước khi fit; (5) chạy một luồng xuất bảng decile đúng nhưng rà soát phát hiện cách tính slope điểm S3 chưa thống nhất với bootstrap ở các leaf xác suất 0; (6) căn chỉnh cách clipping xác suất 0 và chạy lại cùng seed/tham số/folds, sinh artifact cuối. Các artifact tạm đã bị ghi đè bởi lượt hoàn chỉnh cuối; không dùng các lượt trước để chọn mô hình hay ngưỡng. Trạng thái cuối được xác định bởi artifact có protocol hash nêu trên.

## Nguồn

Script `scripts/evaluate_repurchase_wp5b_dev.py`; dữ liệu vào `load_dev_orders()` và hàm snapshot/fold đã có `src/features/repurchase_v3.py`; outputs chỉ gồm aggregate/meteric, không ghi khóa khách. Mọi kỹ thuật mới được ánh xạ trong `docs/course_alignment.md`.
