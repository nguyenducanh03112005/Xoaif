# Ghi chú provenance kết quả test

Ngày cập nhật: 2026-10-26. Căn cứ: cấu hình và artifact đã khóa, metric aggregate đã lưu, D-010 và D-021. Không nạp lại đơn, nhãn hay hành vi test.

## Quy tắc ghi trước và cửa sổ thực thi

- Amendment 05 ghi outcome dương nếu có đơn status 3 không phải quà trong ngày địa phương **lớn hơn T** và trước `test_end_exclusive`.
- Lần chạy duy nhất dùng điều kiện `day >= start` và `day < end`, tức cửa sổ thực thi **[T, end)**. Cửa sổ lịch gồm ngày T và 179 ngày sau T.
- Sai khác được phát hiện bằng cách đối chiếu rule trong YAML với điều kiện ngày của evaluator, rồi ghi ở D-010. Không sửa config, evaluator hoặc kết quả.
- Quy tắc tín hiệu classification ghi cận dưới ROC-AUC 95% CI > 0,55 và cận dưới paired ΔAP 95% CI > 0. Amendment 05 liệt kê cả Logistic Regression C=10 và feature-v2 C=0,1. Metric aggregate có CI cho cả hai; trường boolean `feature_v2_signal_supported=True` chỉ là cờ lưu cho v2, không tạo cờ mới cho C=10.

## Kết quả hai mô hình đóng băng

Mô hình chính là **Logistic Regression C=10 — mô hình chính theo D-005**. **Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính**. Cả hai được chấm bằng artifact đóng băng; không fit lại trên test.

| Mô hình | ROC-AUC (95% CI) | AP (95% CI) | ΔAP so baseline (95% CI) | TN / FP / FN / TP |
|---|---:|---:|---:|---:|
| Logistic Regression C=10 — mô hình chính theo D-005 | 0,7024 (0,6651–0,7365) | 0,1234 (0,1005–0,1581) | +0,0776 (+0,0560 đến +0,1109) | 4.538 / 394 / 158 / 79 |
| Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính | 0,7027 (0,6651–0,7373) | 0,1233 (0,0994–0,1582) | +0,0774 (+0,0554 đến +0,1111) | 4.468 / 464 / 154 / 83 |

Hai CI số liệu trên đều thỏa các cận đã ghi trước theo metric aggregate của lần chạy thực tế. Tập test gồm 5.169 khách, 237 dương (4,59%); DEV có 3.508 mẫu nhãn, 260 dương (7,41%). Bootstrap theo khách: 2.000 lượt, seed 20261026.

**Cấu hình ghi >T, evaluator dùng [T,end) (gồm ngày T); ảnh hưởng chưa xác định; đây là kết quả số liệu của lần chạy thực tế, không phải khẳng định tuân thủ đầy đủ giao thức, không gọi là 'đạt cổng ghi trước'.**

## Chênh lệch DEV–test và giới hạn

DEV OOF của Logistic Regression C=10 có ROC-AUC 0,5096 và AP 0,0699 trên 1.558 dự đoán OOF; feature-v2 có ROC-AUC 0,4969 và AP 0,0645 trên cùng số mẫu. Chênh lệch với test chưa được giải thích. Lịch sử đặc trưng dài hơn, tỷ lệ nhãn DEV/test khác nhau và cửa sổ có Tết 2026 là giả thuyết chưa kiểm chứng; không phân tách tác động.

Test chỉ mở một lần. Tách metric riêng cho ngày T cần nạp lại dữ liệu test, trái khóa và quyết định bảo vệ; do đó ảnh hưởng của ngày T chưa xác định. Các metric là mô tả của lần chạy thực tế, không chứng minh khả năng tổng quát qua cửa sổ khác.
