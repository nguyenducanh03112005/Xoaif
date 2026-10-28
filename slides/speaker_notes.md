# Speaker notes — Xoaif Garden

Kịch bản theo deck cuối, có thể rút theo thời lượng giảng viên. Nguồn số liệu nằm ở từng slide; không mở dữ liệu từng khách/đơn khi trình bày.

## Slide 01 — Kho dữ liệu và khai phá dữ liệu bán hàng

Mở đầu bằng mục tiêu: biến dữ liệu bán hàng thành quy trình phân tích có thể kiểm tra và trình bày trung thực cả kết quả lẫn giới hạn.

Nguồn: docs/PROJECT_GUIDE.md; README.md

## Slide 02 — Ba câu hỏi, một quy trình dữ liệu

Nói rõ phạm vi ba bài toán. Bài toán C chưa đủ nhãn. Hai bài còn lại có kết quả nhưng cần nêu độ tin cậy và điều kiện diễn giải.

Nguồn: docs/PROJECT_PLAN.md; docs/PROJECT_GUIDE.md

## Slide 03 — Từ API đến dashboard qua năm tầng

Đi theo luồng từ trái sang phải. Client chỉ GET. Snapshot có manifest. HMAC thay định danh trước kho. Dashboard chỉ đọc bảng tổng hợp đã phát hành.

Nguồn: docs/architecture_matrix.md; docs/data_governance.md; docs/PROJECT_GUIDE.md

## Slide 04 — Snapshot lớn hơn phạm vi phân tích

Snapshot chứa nhiều khoảng thời gian; từng phân tích dùng cohort riêng. 12.011 là số đơn snapshot, 6.517 là số đơn DEV, 6.400 là status 3 DEV, 5.169 là khách đủ điều kiện scoring.

Nguồn: docs/canonical_numbers.md; docs/cohort_reconciliation.md

## Slide 05 — Dữ liệu được tách theo mức nhạy cảm

HMAC là pseudonymization, không phải ẩn danh tuyệt đối. Raw/restricted cần quyền truy cập và retention policy. Shared chỉ chứa aggregate.

Nguồn: docs/data_governance.md; docs/PROJECT_GUIDE.md

## Slide 06 — Retention tăng theo kỳ hạn, nhưng vẫn thấp

Nêu điều kiện trưởng thành cohort. Retention 180 ngày dùng định nghĩa ngày mua sau. CLV là doanh thu ghi nhận 180 ngày đầu, không phải CLV dự báo hay lợi nhuận.

Nguồn: docs/customer_value_dev.md; outputs/tables/customer_retention_dev.csv

## Slide 07 — K=2 mô tả tần suất, chưa xác nhận hành động

K=2 gần với luật mua một lần/lặp lại. Silhouette là độ tách hình học. Sáu nhóm RFM rule-based tạo giả thuyết mô tả; chưa chứng minh hiệu quả tiếp cận.

Nguồn: docs/customer_value_dev.md; docs/day2_summary.md; docs/PROJECT_GUIDE.md

## Slide 08 — DEV chưa xác nhận tín hiệu mua lại

Đọc biểu đồ cùng thiết kế đánh giá. Điểm test cao hơn nhưng DEV OOF không tái hiện. Không kết luận mô hình tốt hoặc sẵn sàng triển khai.

Nguồn: docs/test_report.md; docs/cohort_mismatch_analysis.md

## Slide 09 — Đánh giá theo thời gian, khóa test một lần

Trình bày định nghĩa feature-as-of T, temporal folds, baseline và bootstrap. Nhắc test đã mở một lần. Nêu chính xác khác biệt ngày biên và không gọi kết quả là đạt trọn protocol.

Nguồn: docs/data_protocol.md; docs/test_provenance_note.md; outputs/metrics/test_opened.lock.json

## Slide 10 — Bộ lọc DEV giữ lại một giả thuyết combo

24 cặp đã khóa; 21/24 lift trên 1 ở test là tiêu chí yếu. Bộ lọc DEV F3 dùng lift>1, Kulczynski>=0,5 và imbalance ratio<=0,5; 1 cặp qua. Chỉ nên xem là giả thuyết A/B.

Nguồn: docs/combo_recommendation_f3.md; docs/test_report.md

## Slide 11 — Bài toán phản hồi đang chờ dữ liệu có nhãn

Không diễn giải thiếu nhãn thành không có phàn nàn. Không gửi văn bản ra dịch vụ ngoài nếu chưa duyệt nhà cung cấp và cách lưu dữ liệu.

Nguồn: docs/data_gap_report.md; docs/data_governance.md; docs/PROJECT_GUIDE.md

## Slide 12 — Dashboard chạy offline từ aggregate

Chỉ demo các tab thật sự có trong app. Bộ lọc đổi aggregate local; không hiển thị ID khách/đơn. Khoảng tổng quan có tháng cuối chưa trọn.

Nguồn: src/app/streamlit_app.py; docs/DEFENSE_GUIDE.md

## Slide 13 — Bốn quyết định mở khóa bước tiếp theo

Dùng bảng này để chuyển từ kết quả sang các quyết định cần chủ dự án/giảng viên chốt. Phần xử lý cụ thể nằm trong PROJECT_GUIDE mục 7.

Nguồn: docs/PROJECT_GUIDE.md

## Slide 14 — Ba cách sử dụng repo sau khi clone

Nêu điều kiện: dashboard cần outputs aggregate; sample là giả lập; runner hậu kiểm có thể chạy pytest nhưng không mở test hay fit. Ingestion chỉ chạy trên máy được cấp quyền API.

Nguồn: docs/PROJECT_GUIDE.md; scripts/run_all.py

## Slide 15 — Kết luận và câu hỏi

Kết luận bằng những gì đã làm được, phần chưa có căn cứ và dữ liệu cần bổ sung. Mời giảng viên đặt câu hỏi.

Nguồn: docs/PROJECT_GUIDE.md; docs/DEFENSE_GUIDE.md
