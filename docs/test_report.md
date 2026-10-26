# Đánh giá test một lần

## Phạm vi và kiểm soát

Test được mở đúng một lần. Cấu hình ghi outcome ngày địa phương `>T`; lần chạy thực tế dùng `[T, end)`, gồm ngày T và 179 ngày địa phương sau T. Sai khác được ghi trong [ghi chú provenance](test_provenance_note.md) và D-010. Nhãn dương là có ít nhất một đơn status 3 không phải quà cấp đơn. Ngưỡng dự đoán của các classifier giữ ở 0,5.

Trước lần mở, khu vực dành riêng có hai bản ghi `eligibility_count`. Xác minh hậu mở xác nhận một lần `label_load` và một lần `behavior_load`; access log không chứa giá trị hay định danh khách.

## Mô hình mua lại

Cohort scoring gồm 5.169 khách đã mua trước T; có 237 dương (4,59%). DEV có 3.508 mẫu nhãn và 260 dương (7,41%). Các hàng precision, recall, F1 và confusion matrix dùng ngưỡng 0,5.

**Diễn giải cần ưu tiên:** ROC-AUC DEV OOF của mô hình chính C=10 là 0,5096, gần mức đoán ngẫu nhiên; development chưa cho thấy tín hiệu xếp hạng rõ. ROC-AUC test khoảng 0,70 là tín hiệu yếu trên tập test mà DEV chưa xác nhận, không đủ để kết luận mô hình hoạt động tốt hay sẵn sàng triển khai. Test đã được mở; không dùng kết quả test để tinh chỉnh đặc trưng, ngưỡng, mô hình hoặc luật, và không chạy evaluator lần nữa.

| Mô hình | Vai trò | Precision | Recall | F1 | ROC-AUC | AP | ROC-AUC 95% CI | AP 95% CI | ΔAP vs baseline 95% CI | TN / FP / FN / TP |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline majority | Mốc so sánh | 0,000 | 0,000 | 0,000 | 0,500 | 0,046 | 0,5000–0,5000 | 0,0404–0,0517 | — | 4.932 / 0 / 237 / 0 |
| Logistic Regression C=10 — mô hình chính theo D-005 | Chính | 0,167 | 0,333 | 0,223 | 0,702 | 0,123 | 0,6651–0,7365 | 0,1005–0,1581 | +0,0560 đến +0,1109 | 4.538 / 394 / 158 / 79 |
| Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính | Bổ sung | 0,152 | 0,350 | 0,212 | 0,703 | 0,123 | 0,6651–0,7373 | 0,0994–0,1582 | +0,0554 đến +0,1111 | 4.468 / 464 / 154 / 83 |

ΔAP point estimate lần lượt là +0,0776 với C=10 và +0,0774 với feature-v2. CI bootstrap paired 95% theo khách, 2.000 lượt, seed 20261026. Cận dưới CI ROC-AUC của cả hai lớn hơn 0,55; cận dưới CI ΔAP của cả hai lớn hơn 0. Baseline test chấm một mức prevalence DEV cố định nên ROC-AUC bằng 0,500.

**Cấu hình ghi >T, evaluator dùng [T,end) (gồm ngày T); ảnh hưởng chưa xác định; đây là kết quả số liệu của lần chạy thực tế, không phải khẳng định tuân thủ đầy đủ giao thức, không gọi là 'đạt cổng ghi trước'.** Xem [ghi chú provenance](test_provenance_note.md).

DEV OOF của Logistic Regression C=10 có ROC-AUC 0,5096, AP 0,0699 và PR-AUC trung bình 5 fold 0,1093; feature-v2 có ROC-AUC 0,4969 và AP 0,0645. Cả hai ROC-AUC DEV đều gần mức ngẫu nhiên. Baseline DEV OOF có ROC-AUC 0,5362 vì score baseline dùng prevalence riêng của train ở từng fold; khác test baseline dùng một score cố định nên ROC-AUC 0,500. Test point estimate khoảng 0,70 được xem là tín hiệu yếu chưa được development xác nhận; không kết luận mô hình hoạt động tốt. Chênh lệch chưa được giải thích. Lịch sử đặc trưng dài hơn, prevalence khác nhau và cửa sổ có Tết 2026 là các giả thuyết chưa kiểm chứng. Vì test đã mở, không dùng nó để tiếp tục tinh chỉnh hoặc chọn mô hình.

## Phân khúc

K-Means K=2/3/4 và nhóm quy tắc được gán bằng scaler, mô hình và ngưỡng DEV đã khóa. K=2 chủ yếu tách khách mua một lần với khách mua lặp lại; đây là phân biệt theo tần suất, chưa chứng minh các nhóm có ý nghĩa kinh doanh hoặc giá trị cho quyết định vận hành. Cohort scoring có 5.169 khách. Khoảng cách TV bằng 0 vì DEV tại T và scoring dùng cùng hồ sơ đầu vào đã khóa; Wasserstein chuẩn hóa theo IQR của Frequency không xác định vì IQR DEV bằng 0. Đây là đặc điểm của thiết kế so sánh, không phải bằng chứng hành vi tương lai ổn định. Proxy giá trị lớn không xác minh pháp nhân.

## Luật kết hợp

Đã chấm 24 cặp đóng băng trên 2.174 giỏ test đủ điều kiện sau khi loại dòng quà; 21/24 cặp có lift > 1. Bảng support, confidence hai hướng, lift và chênh lệch DEV–test nằm trong `outputs/tables/test_combos_frozen.csv`. Luật chỉ mô tả đồng xuất hiện; không chọn luật mới.

## Diễn giải và hạn chế

Tập DEV có một mùa Tết trọn vẹn. Chênh lệch DEV–test và khả năng liên quan của cửa sổ test/Tết chưa được kiểm chứng. Suy luận tập con gán quà có thể sai; dữ liệu hiện trạng không lưu lịch sử thay đổi trạng thái. Chưa có giá vốn nên không đánh giá được hiệu quả kinh tế combo.

Không có đủ dữ liệu phản hồi/đánh giá với nhãn phù hợp trong snapshot để xây dựng hoặc kiểm định bài phân loại phản hồi; bài toán này được bỏ qua, không diễn giải là phản hồi tiêu cực hay không có vấn đề.
