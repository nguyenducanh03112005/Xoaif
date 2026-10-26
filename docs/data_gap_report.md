# Báo cáo: khoảng trống và đơn trước ngày cửa hàng mở

## Phạm vi

Nguồn là snapshot `20261024T052943Z` (12.011 đơn, 601 trang). Bộ rà soát kiểm tra hash trang, trước hết chỉ xem `inserted_at`; nếu ngày địa phương từ `2025-10-22` trở đi thì bỏ qua mọi trường khác. Không đọc nhãn test. Toàn bộ số liệu ở đây là đếm bản ghi/độ hiện diện, không suy ra “doanh thu ghi nhận”.

## Đơn theo tháng — mọi trạng thái

Tệp [day1_monthly_orders_all_status.csv](../outputs/tables/day1_monthly_orders_all_status.csv) có số đơn theo từng tháng từ tháng đầu tiên của snapshot đến hết dev (`2025-10`), gồm mọi trạng thái. Trong khoảng **2022-10 đến 2024-03**, mỗi tháng có **0 đơn** ở mọi trạng thái; bảng này không chỉ đếm status 3.

Theo quyết định chủ dự án, Xoaif Garden chưa kinh doanh trong giai đoạn này. Do đó, các tháng trống là phù hợp với lịch mở cửa hàng đã cung cấp; không gán nguyên nhân “lỗi dữ liệu”. Chủ dự án đã đối chiếu số lượng theo trạng thái với dashboard Pancake và báo không có vấn đề; agent không truy cập dashboard độc lập.

## Giai đoạn bán thử đầu tiên trước 2024-04-01

Theo quyết định mới của chủ dự án, các bản ghi này thuộc giai đoạn bán thử đầu tiên. Trước ngày chính thức bắt đầu kinh doanh theo giờ Việt Nam có **476 đơn**, trong khoảng **2022-06-04–2022-09-21**. Chúng vẫn còn nguyên trong raw và không bị coi là lỗi dữ liệu; được gắn phạm vi loại trừ khỏi mọi phân tích hành vi, RFM, nhãn, giỏ hàng và số liệu doanh thu ghi nhận.

| Status hiện tại | Số đơn | Ngày đầu–cuối | Dòng hàng | Có customer_id | Thiếu customer_id |
|---:|---:|---|---:|---:|---:|
| 3 | 462 | 2022-06-04–2022-09-21 | 860 | 415 | 47 |
| 5 | 8 | 2022-06-22–2022-09-11 | 16 | 8 | 0 |
| 6 | 6 | 2022-06-15–2022-08-02 | 11 | 6 | 0 |
| **Tổng** | **476** | **2022-06-04–2022-09-21** | **887** | **429** | **47** |

Trong các trường tiền ứng viên hiện có, số đơn trước ngày mở có giá trị 0 như sau (đếm theo đơn; một đơn có thể xuất hiện ở nhiều trường):

- Status 3: `cash` 396, `cod` 239, `fee_marketplace` 462, `money_to_collect` 3, `partner_fee` 285, `prepaid` 203, `shipping_fee` 229, `total_discount` 192, `total_price` 2, `total_price_after_sub_discount` 3, `transfer_money` 379.
- Status 5: `cash` 8, `fee_marketplace` 8, `partner_fee` 1, `prepaid` 7, `total_discount` 6, `transfer_money` 8.
- Status 6: `cash` 6, `cod` 1, `fee_marketplace` 6, `partner_fee` 4, `prepaid` 5, `shipping_fee` 1, `total_discount` 4, `transfer_money` 6.

Không phát hiện tên dòng hàng chứa các từ khóa `test`, `sample`, `demo`, `thử`, `mẫu`, `init`, `khởi tạo` (0/476 đơn). Đây chỉ là phép rà từ khóa; không đủ để xác định mục đích của từng đơn. Quyết định loại toàn bộ giai đoạn bán thử trước 2024-04-01 khỏi hành vi dựa trên xác nhận ngày bắt đầu kinh doanh của chủ dự án, không dựa vào kết quả tên/giá trị bằng 0.

## Tập phát triển hiệu dụng

Sau khi loại các đơn trước ngày mở, tập phát triển có 6.517 đơn từ `2024-04-01` đến `2025-10-21`: status 3 = 6.400, status 5 = 13, status 6 = 104. Trong status 3, có 286 đơn thiếu `customer_id`, 5 đơn không có dòng hàng, và 726 dòng hàng thiếu `product_id`.

Nguồn raw không bị xóa hoặc sửa. Kho DuckDB dev mới chỉ chứa ngày địa phương `[2024-04-01,2025-10-22)`; các trường tiền không được ghi vào kho đó.

## Phân loại phản hồi không thực hiện

Snapshot và allowlist hiện hành không cung cấp tập phản hồi/đánh giá có văn bản và nhãn đáng tin cậy để huấn luyện, kiểm định một bộ phân loại phản hồi. Các trường ghi chú/văn bản tự do cũng không được đưa vào kho phân tích. Vì vậy bài phân loại phản hồi bị bỏ qua; không suy diễn cảm xúc, chất lượng dịch vụ hoặc tỷ lệ vấn đề từ việc thiếu dữ liệu này.
