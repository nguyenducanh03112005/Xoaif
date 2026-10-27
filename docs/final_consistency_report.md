# Báo cáo rà soát nhất quán cuối

**Ngày cập nhật:** 2026-10-27 · **Hạn nộp:** 2026-10-27

## Kết quả

Đã đồng bộ vai trò mô hình, metric/CI của hai Logistic Regression và caveat sai khác ngày T trên tài liệu, dashboard, báo cáo và slide. Logistic Regression C=10 — mô hình chính theo D-005; Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính. ROC-AUC DEV OOF C=10 là 0,5096, gần ngẫu nhiên; ROC-AUC test khoảng 0,70 được mô tả là tín hiệu yếu chưa được development xác nhận, không phải bằng chứng mô hình hoạt động tốt. Test đã mở; không dùng để tinh chỉnh.

**Cấu hình ghi >T, evaluator dùng [T,end) (gồm ngày T); ảnh hưởng chưa xác định; đây là kết quả số liệu của lần chạy thực tế, không phải khẳng định tuân thủ đầy đủ giao thức, không gọi là 'đạt cổng ghi trước'.**

Đã chuẩn hóa cohort và tỷ lệ theo đúng mẫu số; combo báo 24 cặp theo điều kiện ổn định ít nhất 4/6 ô và 21/24 lift > 1 trên 2.174 giỏ. K=2 được gọi là phân đoạn mô tả theo tần suất mua (một lần / lặp lại), chưa xác minh ý nghĩa kinh doanh. Bỏ so sánh tỉnh/thành khỏi dashboard vì 91,92% doanh thu mang nhãn UNKNOWN; ghi rõ bài phân loại phản hồi bị bỏ qua do thiếu nhãn. Dashboard có 5 tab, 10 CSV và 6 JSON aggregate. Hai PDF cùng các đầu vào dashboard được dựng lại sau cập nhật; xem [danh sách artifact và kiểm tra an toàn](submission_artifacts.md). `python-pptx` không có trong `.venv`; không tạo PPTX.

Hậu kiểm lần này xác minh split/lock, GET-only, Day 3 và 17 hash bảo vệ; `run_all.py` hậu mở cùng pytest riêng đều đạt 75 test, PII scan và dashboard smoke (5 tab, 10 CSV, 6 JSON, 405 dòng). Test vẫn chỉ mở một lần; không chạy evaluator, notebook hay fit/refit.

## Giới hạn còn lại

Đã đếm các điều kiện/intersection có trong schema và ghi cầu số học 5.499 − 325 − 5 = 5.169. Delta 325 (lower bound) và 5 (đơn quà) chưa được xác minh bằng COUNT DISTINCT theo từng điều kiện; **phần dư chưa giải thích: 330** delta chưa có attribution trực tiếp. Mục cohort chưa đối soát vẫn còn. Nguyên nhân UNKNOWN doanh thu chưa xác định; giả thuyết DEV–test chưa kiểm chứng; thời lượng/rubric chưa có. D-022 ghi rằng mọi chẩn đoán bổ sung cần rolling-origin, amendment mới và duyệt chủ dự án. Chi tiết cùng các vòng consistency scan: [nhật ký](consistency_log.md).

## Việc cần làm trước buổi bảo vệ

Hai thành viên chạy dashboard offline trên máy riêng và thử 5 tab; tập demo 4 phút có mạng/không mạng; in thử đen trắng; mỗi người luyện ít nhất 10 câu hỏi thuộc vai trò người kia. Mang laptop có sạc cùng ảnh/video dự phòng. Thời lượng chính thức và rubric cần xác nhận với giảng viên.
