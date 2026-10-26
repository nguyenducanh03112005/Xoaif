# Nhật ký rà soát nhất quán cuối

Ngày rà soát: 2026-10-26. Phạm vi gồm tài liệu giao nộp, README/PROGRESS, dashboard, hai PDF đầu ra và script dựng PDF/slide. Nguồn số liệu được đối chiếu chỉ là bảng/JSON aggregate và quyết định đã khóa.

## Phạm vi an toàn

- Không đọc dòng đơn hàng, nhãn, hành vi hoặc dữ liệu `data/restricted`; không nạp bảng customer-HMAC/label-level.
- Không chạy evaluator, notebook, model fit/refit hay chọn lại mô hình; không gọi API.
- Không sửa split, Amendment 01–05, sidecar/lock, lock mở test, `test_eval.json`, access log hay D-001–D-020. Diễn giải mới được ghi ở D-021/D-022.
- Không cài package và không tạo PPTX. PDF là bản in dự phòng đã chọn.

## Các điểm phát hiện và sửa

1. **Metric và vai trò mô hình:** bổ sung CI ROC-AUC, AP và paired ΔAP cho cả C=10 và feature-v2; chuẩn hóa vai trò C=10 là mô hình chính theo D-005 và feature-v2 là khảo sát Amendment 04, không thay mô hình chính. Làm rõ quy tắc tín hiệu áp dụng cho cả hai classifier; cờ `feature_v2_signal_supported` vẫn chỉ thuộc feature-v2.
   Tên chuẩn: **Logistic Regression C=10 — mô hình chính theo D-005**; **Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính**.
2. **Giới hạn ngày T:** thống nhất câu caveat bắt buộc ở tài liệu kết quả, QA, bàn giao, demo, progress, speaker notes, dashboard và nguồn dựng PDF/slide. Tách “thỏa ngưỡng số liệu” khỏi kết luận tuân thủ giao thức; không khẳng định cổng ghi trước đã được đáp ứng.
3. **Cohort và số tổng hợp:** thống nhất các định nghĩa riêng của 5.499, 5.174 và 5.169; sửa tỷ lệ một đơn theo đúng mẫu số; giữ 24 combo theo điều kiện ổn định ít nhất 4/6 ô và báo đúng 21/24 lift > 1 trên 2.174 giỏ.
4. **Lịch sử và tiền:** gắn nhãn các đoạn trạng thái trước khi mở test là lịch sử; phân biệt định nghĩa tiền Amendment 02 với Amendment 03; sửa cách ghi số tiền để PII regex không nhầm thành số điện thoại mà vẫn giữ nguyên giá trị.
5. **Đầu ra và chỉ dẫn:** đồng bộ README/PROGRESS; sửa hiển thị `C=0,1` trong PDF builder; dựng lại PDF 15 trang và slide PDF 14 trang; cập nhật ảnh tab Model. Thêm guard để builder tài liệu tiền mở không ghi đè nội dung sau khi test đã mở.

## Vòng kiểm tra cuối

Đã render lại các trang báo cáo 7–15 và slide 6–14 sau lần dựng cuối. Kiểm tra trực quan xác nhận trang metric, caveat ngày T, kết luận, combo và checklist trình bày không bị tràn/cắt. Số trang xác nhận bằng `pdfinfo`: báo cáo 15 trang A4, slide in 14 trang ngang. `pdftotext` không có trong runtime; vì vậy phần chữ được kiểm qua nguồn dựng và ảnh render, không qua trích xuất văn bản PDF.

Các vòng kiểm tra:

- Scan ban đầu phát hiện 5 thiếu sót: `qa_roles.md` chưa có caveat nguyên văn và hai tên vai trò chuẩn; nhật ký mới chưa ghi đủ hai tên vai trò. Đã sửa cả 5 mục.
- Dashboard smoke sau đó phát hiện checker kỳ vọng 5 JSON trong khi app đọc 6 JSON aggregate. Đã sửa kỳ vọng, cập nhật canonical/progress/slide và dựng lại slide PDF.
- Final consistency scan 1: **0 findings**.
- Final consistency scan 2: **0 findings**.

Phạm vi scan: tên/vai trò mô hình; caveat ở mọi vị trí nêu tín hiệu test; các mốc combo/cohort; số trang và liên kết README; dashboard data-contract; dấu hiệu trạng thái tiền mở bị trình bày như trạng thái hiện hành; cú pháp và nội dung các đầu ra đã dựng.

**Câu caveat chuẩn:** Cấu hình ghi >T, evaluator dùng [T,end) (gồm ngày T); ảnh hưởng chưa xác định; đây là kết quả số liệu của lần chạy thực tế, không phải khẳng định tuân thủ đầy đủ giao thức, không gọi là 'đạt cổng ghi trước'.

## Chưa xác minh / việc chuyển giao

- Các cohort 5.499 / 5.174 / 5.169 chưa được phân rã đối soát; không suy diễn quan hệ giữa chúng.
- Nguyên nhân doanh thu tỉnh UNKNOWN chiếm 91,92% chưa được phân tích.
- Chênh lệch DEV–test và giả thuyết lịch sử đặc trưng dài hơn/mùa vụ/prevalence chưa được kiểm chứng. Không chạy chẩn đoán anchor; D-022 ghi rõ muốn kiểm tra hợp lệ phải có thiết kế rolling-origin, amendment mới và duyệt của chủ dự án.
- Thời lượng thuyết trình và rubric chính thức chưa có trong hồ sơ.
- Không còn artifact combo Day2B sạch để dựng lại bản tóm tắt Day2B; builder hiện từ chối chạy sau khi lock test tồn tại, tránh ghi đè bản lưu trữ bằng artifact không đúng schema.
- Runtime thiếu công cụ trích xuất chữ PDF; đã kiểm source và render trực quan.
- Một literal lịch sử trong YAML Amendment 04 đã khóa và trường metadata/code tương ứng không được sửa theo ranh giới bảo vệ; không dùng trong narrative bàn giao.

Trước hạn 2026-10-27, hai thành viên tự chạy kiểm tra an toàn và mở đủ 5 tab trên máy riêng; tập demo 4 phút có mạng và không mạng; kiểm bản in đen trắng; mỗi người luyện ít nhất 10 câu hỏi chéo. Xem `docs/final_consistency_report.md`, `docs/handover.md` và `docs/qa_roles.md`.
