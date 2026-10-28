# WP5c — S6 bảng tỷ lệ theo frequency–recency (DEV-only)

**Nhãn:** khám phá, chưa xác nhận ngoài mẫu. Kế hoạch đăng ký trước `docs/analysis_plan_wp5c.md`, SHA-256 `8dd4774425659f170de08669d42b2d358cdd6c2ed4cd5a33ed68ebeb6767fbf8`. Không dùng test raw/nhãn/hành vi; không đổi D-005.

S6 dùng ô frequency `{1,2,≥3}` × recency `{≤30,31–90,91–180,>180}`. Trong mỗi outer fold, tỷ lệ ô và gộp ô chỉ tính từ train; ngưỡng gộp n_train≥100. Nếu stratum frequency tổng dưới 100, gộp với stratum kề có n lớn hơn (hòa chọn thấp hơn); sau đó gộp band recency nhỏ nhất với band kề đông hơn (hòa chọn band cũ hơn). Không có fallback prevalence toàn train trong 5 folds. Bảng train-rate và validation cell n/positive/observed rate ở `outputs/tables/repurchase_wp5c_train_rates.csv` và `repurchase_wp5c_calibration_cells.csv`; không có validation cell n<30 cần suppression.

## Kết quả xếp hạng

OOF có 14.394 snapshot, 3.508 khách, 600 dương (4,17%) trên 5 fold.

| Metric | S6 pooled OOF (95% bootstrap theo khách) |
|---|---:|
| ROC-AUC | 0,640 (0,610–0,673) |
| AP | 0,0727 (0,0588–0,0900) |
| Brier | 0,0416 (0,0369–0,0466) |
| Precision@5% | 12,64% (9,43–16,05%) |
| Precision@10% | 10,21% (7,90–12,74%) |
| Precision@20% | 7,57% (6,28–9,20%) |
| Lift top-decile | 2,45 (2,01–2,90) |

Metric theo fold và pooled tách ở `outputs/tables/repurchase_wp5c_fold_metrics.csv`; AP trung bình 5 fold 0,0668, ROC-AUC trung bình 0,604. Fold đầu chỉ có một rate group do ít dữ liệu train nên score constant: ROC-AUC 0,5 và AP bằng prevalence. Không diễn giải pooled AP như performance tương lai; snapshot lặp khách được bootstrap theo khách.

Decile pooled không hoàn toàn đơn điệu: decile 3 (5,69%) cao hơn decile 2 (4,93%); các decile trên cùng cho tín hiệu phân tầng nhưng có nhiễu. Top 10% OOF có tỷ lệ mua lại 10,21% so với nền 4,17%; đây là tỷ lệ quan sát, không uplift hay kết quả chiến dịch.

## Calibration và cách dùng

Pooled mean predicted rate là 7,74%, còn observed prevalence 4,17%; fold predicted averages đều cao hơn validation prevalence. Đây là dịch chuyển tỷ lệ nền đã quan sát ở F2; S6 rate được học trên train và không tự hiệu chỉnh với từng validation window. Brier 0,0416 không xóa bỏ calibration-in-the-large gap. Bảng cell ghi train rate, n_train và n/positive validation; n<30 được che nếu phát sinh.

WP5b ghi S2 là “luật kết hợp” trong protocol ban đầu; thuật ngữ đúng để diễn giải là **luật ngưỡng recency–frequency**, không phải luật kết hợp Apriori. S2 và S4 đều thất bại vì không có inner temporal folds hợp lệ, không phải metric kém và không được thay bằng phân tích khác. WP5b monotonicity criterion không phù hợp tốt với score rời rạc, nhưng cũng không nới hồi tố. S6 là một chiến lược mới đăng ký riêng, không phải cứu S2/S4 hay thay D-005.

S6 có thể cung cấp tỷ lệ nền theo ô cho mô hình hòa vốn trong bước kinh doanh sau, nhưng chỉ làm đầu vào nếu có giả định chi phí/biên lợi nhuận do người dùng nhập. Không suy luận tác động nhân quả hay lợi nhuận. Mức bằng chứng C cho lựa chọn vận hành, vì chỉ DEV-only và các fold có dịch chuyển prevalence.

Nguồn script `scripts/evaluate_repurchase_wp5c_dev.py`; số liệu được ghi ở `outputs/metrics/repurchase_wp5c_dev.json`, các bảng train/validation rates, fold metrics, decile và top-k. Không ghi khóa khách vào output.
