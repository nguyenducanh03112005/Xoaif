# Rà soát ranh giới test và nguy cơ leakage

## Phạm vi kiểm toán

Đây là rà soát tĩnh trên quy tắc split, pipeline feature, nhãn DEV, freeze metadata và evaluator đã khóa; không mở hoặc nạp đơn hàng, nhãn hay hành vi test; không chạy evaluator, không fit mô hình và không chạy notebook.

## Đường thời gian và thứ tự xử lý

- Feature cho mốc T dùng đơn có `local_date < T`; bộ tạo feature `make_customer_features` bỏ mọi dòng có ngày `>= as_of`.
- Nhãn DEV dựa trên các mốc T lịch sử thỏa khoảng cách N+L trước ranh giới test, và được lưu riêng trong `outputs/tables/day2_label_samples_primary.csv`.
- Preprocessing và lựa chọn pipeline/model được fit trong DEV. Freeze metadata ghi hash model trước test; evaluator dùng artifact đã freeze để chấm cohort đã chốt và không có bước fit trong đường chạy.
- `scripts/evaluate_test_once.py` là evaluator một lần, không được chạy lại. Lock/access log đã được kiểm tra ở giai đoạn bàn giao trước đó; audit này không đọc dữ liệu test.
- Bảng EDA mới dùng kho DEV `[2024-04-01, 2025-10-22)` và nhãn lịch sử DEV; không lấy feature file scoring 5.169 khách để mô tả DEV.

## Kết luận

Trong phần mã và metadata đã rà soát, không thấy đường đưa nhãn/hành vi tương lai vào feature trước T hoặc fit lại mô hình trong evaluator. Kiểm thử tổng hợp mới xác nhận đơn đúng ngày T và sau T không đóng góp frequency/monetary/last purchase vào feature. Đây là bằng chứng về logic, không phải chứng minh tuyệt đối cho mọi đầu vào dữ liệu.

Số 5.169 khớp cohort scoring đã freeze không tự nó chứng minh leakage; cohort cũng được lập theo quy tắc đủ điều kiện từ dữ liệu trước T. Giải thích chênh lệch prevalence DEV/test do mùa vụ là giả thuyết chưa kiểm chứng. Dữ liệu test đã mở đúng một lần theo log; mọi sai khác về việc bao gồm ngày T (`>T` ghi trước so với `[T,end)` thực tế) được ghi ở `docs/test_provenance_note.md`, tác động chưa xác định. Không khẳng định đã đạt cổng ghi trước.

## Tái kiểm tra an toàn đã yêu cầu

- Test mới chỉ dùng ba đơn tổng hợp với ngày trước T, đúng T và sau T; không đọc fixture dự án hay dữ liệu test.
- Static check notebook chỉ kiểm tra JSON/source/hash; không thực thi bất kỳ notebook nào.
- `scripts/run_all.py` và pytest chạy nhánh hậu mở đã được yêu cầu trong phạm vi; xác nhận lock, GET-only, PII scan và suite tổng thể sau khi bổ sung test tổng hợp.

## Giả thuyết chưa kiểm chứng: chẩn đoán anchor DEV

Giả thuyết “lịch sử đặc trưng dài hơn làm thay đổi metric khi T muộn hơn” chưa được kiểm tra. Không mở Amendment 06 và không chạy chẩn đoán trong phạm vi hiện tại (D-022). Dùng mô hình đóng băng đã fit trên toàn DEV để chấm các anchor lịch sử có thể gây leakage theo thời gian vì mô hình đã thấy dữ liệu sau các anchor đó. Một kiểm tra hợp lệ sau này cần thiết kế rolling-origin, mỗi anchor chỉ fit trên dữ liệu trước anchor, đăng ký trước trong Amendment 06 mới và được chủ dự án duyệt. Kết quả chỉ mang tính thăm dò, phải báo cả khi không ủng hộ giả thuyết và không đổi kết luận test.

Không tính metric mới theo fold hoặc anchor. Nếu một báo cáo DEV OOF đã lưu được dùng để mô tả độ dao động, phải giữ nguyên cohort/fold và trích trực tiếp giá trị aggregate hiện có.
