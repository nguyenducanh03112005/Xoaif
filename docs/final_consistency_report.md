# Báo cáo rà soát nhất quán cuối

**Ngày:** 2026-10-26 · **Hạn nộp:** 2026-10-27

## Kết quả

Đã đồng bộ vai trò mô hình, metric/CI của hai Logistic Regression, ngưỡng tín hiệu Amendment 05 và caveat sai khác ngày T trên tài liệu, dashboard, báo cáo và slide. Logistic Regression C=10 — mô hình chính theo D-005; Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính. Kết quả được mô tả là thỏa ngưỡng về mặt số liệu.

**Cấu hình ghi >T, evaluator dùng [T,end) (gồm ngày T); ảnh hưởng chưa xác định; đây là kết quả số liệu của lần chạy thực tế, không phải khẳng định tuân thủ đầy đủ giao thức, không gọi là 'đạt cổng ghi trước'.**

Đã chuẩn hóa cohort và tỷ lệ theo đúng mẫu số; combo báo 24 cặp theo điều kiện ổn định ít nhất 4/6 ô và 21/24 lift > 1 trên 2.174 giỏ. Dashboard có 5 tab, 11 CSV, 6 JSON và 427 dòng tổng hợp. Đã dựng lại [báo cáo PDF 15 trang](../report/xoaif_report.pdf), [slide PDF 14 trang](../slides/xoaif_print.pdf), cập nhật dashboard và ảnh demo. Không có PPTX; không cài package mới.

Hậu kiểm dự án: `scripts/run_all.py` đạt split/lock, GET-only, PII và 74 pytest; dashboard smoke đạt (427 dòng); quét PII riêng đạt; pytest riêng đạt 74; `verify_day3_locks.py` xác nhận đúng một lần mở và input không đổi. 17 hash của cấu hình/amendment/lock/kết quả test khớp baseline; access log có đúng một `label_load` và một `behavior_load`. Test vẫn chỉ mở một lần; không chạy evaluator, notebook hay fit/refit.

## Giới hạn còn lại

Chưa đối soát quan hệ giữa cohort 5.499/5.174/5.169; chưa phân tích nguyên nhân UNKNOWN doanh thu; giả thuyết DEV–test và chẩn đoán anchor chưa kiểm tra; thời lượng/rubric chưa có. D-022 ghi rằng anchor cần rolling-origin, amendment mới và duyệt chủ dự án. Runtime không có PDF text extractor; đã rà nguồn dựng và render. Chi tiết cùng các vòng consistency scan: [nhật ký](consistency_log.md).

## Việc cần làm trước buổi bảo vệ

Hai thành viên chạy dashboard offline trên máy riêng và thử 5 tab; tập demo 4 phút có mạng/không mạng; in thử đen trắng; mỗi người luyện ít nhất 10 câu hỏi thuộc vai trò người kia. Mang laptop có sạc cùng ảnh/video dự phòng. Thời lượng chính thức và rubric cần xác nhận với giảng viên.
