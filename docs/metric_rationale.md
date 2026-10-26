# Vì sao dùng các metric phân loại này

Mục tiêu supervised là dự đoán nhãn nhị phân “có ít nhất một lần mua hợp lệ trong `(T, T+180 ngày]` hay không”. Vì đầu ra là lớp 0/1, RMSE, MAE và R² là metric hồi quy và không diễn giải đúng chất lượng xếp hạng/phân lớp của bài toán này.

## Bộ metric

- **ROC-AUC** đo khả năng xếp khách có nhãn dương cao hơn khách âm trên nhiều ngưỡng. Nó không xác định ngưỡng quyết định và không tự nói rằng xác suất được hiệu chỉnh tốt.
- **Average Precision / PR-AUC** tóm tắt precision–recall và làm rõ hiệu quả tìm lớp dương hiếm. Với DEV prevalence 7,41%, đường cơ sở không kỹ năng có AP xấp xỉ prevalence; phải nêu baseline cạnh model.
- **Precision và recall** tại ngưỡng đã khóa 0,5 cho biết trong số khách được gắn dương có bao nhiêu đúng, và trong số khách dương có bao nhiêu được tìm thấy. Tăng một metric thường phải đánh đổi metric kia.
- **F1** là trung bình điều hòa precision và recall tại ngưỡng đó; hữu ích như một điểm tóm tắt, nhưng không thay thế việc xem hai thành phần và ma trận nhầm lẫn.
- **Confusion matrix** cho số TP/FP/FN/TN tại ngưỡng cố định; báo cùng cohort và prevalence để tránh diễn giải ngoài quy mô dữ liệu.

## Cách diễn giải

DEV có 260 mẫu dương trên 3.508 (7,41%). Trong tình huống này accuracy có thể cao chỉ bằng cách đoán lớp âm phần lớn thời gian, vì vậy không dùng accuracy làm tiêu chí chọn mô hình. ROC-AUC và AP được xem cùng prevalence; precision/recall/F1 và confusion matrix được xem tại ngưỡng đã đăng ký. Kết quả test được trình bày như ước lượng trên một cohort theo lần chạy thực tế. Cấu hình ghi >T, evaluator dùng [T,end) (gồm ngày T); ảnh hưởng chưa xác định; đây là kết quả số liệu của lần chạy thực tế, không phải khẳng định tuân thủ đầy đủ giao thức, không gọi là 'đạt cổng ghi trước'.

Metric này không chứng minh tác động nhân quả, giá trị kinh doanh của can thiệp, chất lượng hiệu chỉnh xác suất hay khả năng khái quát sang cửa hàng/thời kỳ khác. Cỡ mẫu positive nhỏ nên phải giữ khoảng tin cậy và tránh tuyên bố mạnh.
