# Kiểm toán chất lượng tỉnh/thành UNKNOWN

## Phạm vi và định nghĩa

- Phạm vi số liệu: DEV, đơn status 3 có `local_date` trong `[2024-04-01, 2025-10-22)`, tổng cộng 6.400 đơn.
- Feature mapping đọc `shipping_address.province_name` rồi áp dụng `canonical_province`. Giá trị không phải chuỗi hoặc chuỗi rỗng sau khi trim được ánh xạ thành UNKNOWN; chuỗi còn lại được chuẩn hóa dấu, khoảng trắng và chữ hoa. Vì vậy UNKNOWN là trạng thái thiếu sau chuẩn hóa, không nhất thiết đồng nghĩa JSON không có khóa.
- Đã quét 601 trang JSON của snapshot `20261024T052943Z` trong bộ nhớ và chỉ giữ aggregate độ hiện diện trường cho 6.400 đơn DEV status 3. Không in/lưu địa chỉ, giá trị trường, định danh hay văn bản tự do. Không gọi API.

## Kiểm tra các trường địa chỉ trong raw snapshot

| Trường | Đơn có giá trị trong DEV status 3 | Ý nghĩa / giới hạn |
|---|---:|---|
| `shipping_address.province_name` | 540 | Trường tên tỉnh đang được feature mapping dùng; 5.860 đơn còn lại không có tên sau chuẩn hóa. |
| `shipping_address.province_id` | 540 | Có cùng độ phủ với `province_name`; không bổ sung mã cho đơn thiếu tên. |
| `shipping_address.new_province_id` | 81 | Chỉ 23/5.860 đơn thiếu `province_name` có mã này. Không có trong repo mapping lịch sử/được kiểm chứng từ mã này sang tỉnh; không tự đoán mapping. |
| `shipping_address.district_id` / `district_name` | 427 / 427 | Không thể suy ra tên tỉnh nếu thiếu bảng ánh xạ district→province đã xác minh. |
| `customer.shop_customer_addresses[].province_id` | 606 | Hồ sơ địa chỉ khách, không nhất thiết là địa chỉ giao của đơn; 68 đơn thiếu `shipping_address.province_name` có mã hồ sơ. Không dùng thay địa chỉ giao. |
| `shipping_address.address`, `full_address`, `new_full_address`, `marketplace_address` | 2.162 / 2.169 / 61 / 0 | Các trường địa chỉ tự do có thể chứa PII; không parse, không dùng để suy đoán tỉnh và không xuất ra repo. |

Kết quả: chưa có căn cứ an toàn để khôi phục tỉnh cho phần lớn đơn UNKNOWN. Chỉ 23 đơn có `new_province_id` nhưng thiếu tên; cần bảng mã chính thức của Pancake có phiên bản/thời điểm hiệu lực để đánh giá nhóm nhỏ này. Không dùng địa chỉ khách hoặc text tự do làm phương án thay thế. Không dựng lại bảng xếp hạng tỉnh/thành và không khôi phục tab so sánh tỉnh trong dashboard.

## Kết quả aggregate DEV

| Chỉ tiêu | Số lượng | Tỷ lệ |
|---|---:|---:|
| Đơn status 3 trong cửa sổ DEV | 6.400 | 100,00% |
| UNKNOWN province sau chuẩn hóa | 5.860 | 91,56% |
| Province hiện diện sau chuẩn hóa | 540 | 8,44% |
| Doanh thu ghi nhận DEV | 2.628.354.091 VND | 100,00% |
| Doanh thu của nhóm UNKNOWN | 2.384.693.718 VND | 90,73% |

Các aggregate DEV province và doanh thu được ghi trong `docs/unknown_region_diagnostic.md`; định nghĩa doanh thu theo Amendment 03 được kiểm toán tại `docs/money_audit.md`. Số 91,92% từng xuất hiện trong dashboard có mẫu số DEV+test, không cùng phạm vi với tỷ lệ DEV 91,56% ở đây.

## Diễn giải và giới hạn

Phát hiện xác nhận UNKNOWN tương ứng thiếu giá trị tỉnh/thành sau mapping hiện hành; province ID chính có độ phủ đúng bằng tên, còn mã mới chỉ tăng thêm 23 ứng viên chưa ánh xạ. Không xác định được lý do nghiệp vụ, độ chính xác của địa chỉ, hoặc nguồn/kênh nào gây thiếu; không suy luận nguyên nhân từ tỷ lệ này. Không trích xuất hay công bố tên tỉnh, địa chỉ, giá trị nguồn/kênh hoặc nhóm nhỏ. Phân tích này không thay đổi feature, cohort, split hay mô hình.
