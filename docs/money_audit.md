# Kiểm toán tiền theo amendment 03

Phạm vi: status 3 trong `[2024-04-01,2025-10-22)`, giờ `Asia/Ho_Chi_Minh`; 6.400 đơn. Số liệu lấy từ `outputs/metrics/day2_money_audit.json`; bảng tổng hợp không định danh là `outputs/tables/money_diagnosis.csv`. Không có mã đơn/PII; nhãn và hành vi test chưa được nạp.

## Cách diễn giải

Status 3 được chủ cửa hàng xác nhận là doanh thu đã nhận/ghi nhận. Bằng chứng gồm rà soát mẫu 13 đơn và xác nhận bằng lời; `dash_*` vẫn trống, nên không trình bày như đối soát dashboard chi tiết. Trường thanh toán app không làm bộ lọc hay bằng chứng thu tiền. Amendment 03 thay quy tắc sau khi cổng cũ ghi nhận 701/6.400 (10,95%) vượt 5%; lý do là kiến thức nghiệp vụ rằng chênh lệch có thể là phí/ưu đãi, không dựa trên nhãn/hành vi test. Cổng 5% đã bị thay thế.

701/6.400 là kết quả theo cổng Amendment 02; 639/6.400 `adj_unexplained` là phân loại của Amendment 03. Hai số dùng định nghĩa khác nhau và không thể so trực tiếp như một thay đổi cùng chỉ tiêu.

Doanh thu chính là `after_sub_discount - shipping_fee`, ngoại lệ dùng `after` khi `after == total_price-total_discount` và ship dương. `price_adjustment = revenue_recognized - (total_price-total_discount)`. Điều chỉnh được giữ; `adj_unexplained` chỉ đánh dấu mẫu khác các quan hệ chính xác đã ghi trong amendment 03.

## Quan hệ trường tiền

- Khớp `after = total-discount+shipping`: 5.739/6.400 (89,67%).
- Khớp `total_price = Σ retail_price × quantity`: 6.395/6.395 (100,00%); chỉ tính đơn có đủ dòng hàng.
- Đếm theo từng mẫu `after` (các nhóm loại trừ lẫn nhau):
- Thiếu trường tiền: 0 (0,00%).
- Khớp `total - discount + shipping`: 5.739 (89,67%).
- `after = total - discount` (chưa cộng ship; ngoại lệ đã duyệt): 2 (0,03%).
- `after = total + shipping` (chưa trừ discount): 11 (0,17%).
- `after = total`: 0 (0,00%).
- Lệch dư `+shipping` so với công thức chuẩn: 9 (0,14%).
- Lệch dư `-shipping` so với công thức chuẩn: 0 (0,00%).
- Lệch dư `+discount` so với công thức chuẩn: 0 (0,00%).
- Lệch dư `-discount` so với công thức chuẩn: 0 (0,00%).
- Lệch khác, khoảng cách ≤ 10.000 VND: 97 (1,52%).
- Lệch khác, khoảng cách 10.001–50.000 VND: 325 (5,08%).
- Lệch khác, khoảng cách 50.001–100.000 VND: 93 (1,45%).
- Lệch khác, khoảng cách > 100.000 VND: 124 (1,94%).

## Điều chỉnh và ngoại lệ

- Đơn không tặng có điều chỉnh xác định: 6.378; bằng 0: 5.719 (89,67%); dương: 651 (10,21%); âm: 8 (0,13%).
- Phân vị price_adjustment: p00 = −450.000 đ; p25 = 0 đ; p50 = 0 đ; p75 = 0 đ; p90 = 2.000 đ; p95 = 40.000 đ; p99 = 180.000 đ; p100 = 1.368.800 đ.
- Tổng điều chỉnh dương: 52.588.532 đ (2,00% doanh thu ghi nhận); tổng điều chỉnh âm có dấu: −572.000 đ (−0,02%); ròng 52.016.532 đ (1,98%).
- Đơn tặng: 22 (0,34%); doanh thu âm: 2 (0,03%), phân nhóm nguyên nhân theo mẫu trường tiền `{"after_below_shipping_fee": 2, "total_minus_discount_is_negative": 2}`; `adj_unexplained`: 639; `total_price=0` và `after>0`: 5.
- Tỷ lệ theo tháng:
- 2024-04: điều chỉnh khác 0 3,25%; chưa giải thích 3,16%; doanh thu âm 0,00%.
- 2024-05: điều chỉnh khác 0 3,06%; chưa giải thích 2,43%; doanh thu âm 0,00%.
- 2024-06: điều chỉnh khác 0 3,05%; chưa giải thích 3,02%; doanh thu âm 0,00%.
- 2024-07: điều chỉnh khác 0 2,69%; chưa giải thích 2,68%; doanh thu âm 0,00%.
- 2024-08: điều chỉnh khác 0 3,02%; chưa giải thích 3,02%; doanh thu âm 0,00%.
- 2024-09: điều chỉnh khác 0 6,20%; chưa giải thích 5,84%; doanh thu âm 0,00%.
- 2024-10: điều chỉnh khác 0 9,85%; chưa giải thích 9,69%; doanh thu âm 0,16%.
- 2024-11: điều chỉnh khác 0 25,40%; chưa giải thích 24,80%; doanh thu âm 0,00%.
- 2024-12: điều chỉnh khác 0 22,85%; chưa giải thích 21,66%; doanh thu âm 0,00%.
- 2025-01: điều chỉnh khác 0 28,08%; chưa giải thích 27,13%; doanh thu âm 0,00%.
- 2025-02: điều chỉnh khác 0 17,34%; chưa giải thích 17,34%; doanh thu âm 0,40%.
- 2025-03: điều chỉnh khác 0 22,46%; chưa giải thích 22,07%; doanh thu âm 0,00%.
- 2025-04: điều chỉnh khác 0 12,44%; chưa giải thích 12,44%; doanh thu âm 0,00%.
- 2025-05: điều chỉnh khác 0 4,41%; chưa giải thích 4,41%; doanh thu âm 0,00%.
- 2025-06: điều chỉnh khác 0 3,40%; chưa giải thích 3,40%; doanh thu âm 0,00%.
- 2025-07: điều chỉnh khác 0 1,61%; chưa giải thích 1,61%; doanh thu âm 0,00%.
- 2025-08: điều chỉnh khác 0 1,38%; chưa giải thích 0,92%; doanh thu âm 0,00%.
- 2025-09: điều chỉnh khác 0 1,15%; chưa giải thích 1,15%; doanh thu âm 0,00%.
- 2025-10: điều chỉnh khác 0 2,39%; chưa giải thích 1,84%; doanh thu âm 0,00%.
- So sánh đầu kỳ và đỉnh: Tỷ lệ điều chỉnh bình quân 5 tháng đầu (2024-04, 2024-05, 2024-06, 2024-07, 2024-08) là 3,01%; đỉnh ở 2025-01 (28,08%). Tỷ lệ điều chỉnh không đạt đỉnh ở giai đoạn mở đầu theo nhóm tháng này.

## So sánh độ nhạy A

A dùng `total_price-total_discount`; so sánh loại quà. Doanh thu ghi nhận chính là 2.628.354.091 đ; A là 2.576.337.559 đ; chênh chính trừ A là 52.016.532 đ (2,0190% theo trị tuyệt đối A). 642/6.378 đơn khác trên 1% (10,07%). Spearman Monetary theo 5.169 khách ghép được là 0,9953; Monetary đặt đóng góp từng đơn âm bằng 0.

## Độ nhạy B và cổng

Độ nhạy B loại hợp đơn có `price_adjustment != 0` hoặc `adj_unexplained`: giữ 5.719 đơn không quà; doanh thu ghi nhận tổng của các đơn còn lại là 2 tỷ 76.771.667 đ. Các phân tích khách hàng sẽ chạy lại trên cùng mốc thời gian/chia khách.

**Cổng tiền:** ĐẠT: 2/6.400 đơn âm (0,03%), không vượt ngưỡng 1%; có thể tiếp tục Ngày 2.

Giới hạn: chỉ có status hiện tại; không dùng `status_history`, nên không thể khôi phục trạng thái tại `T+N+L`. Đây là doanh thu ghi nhận theo quy tắc nghiệp vụ, không phải lợi nhuận hay đối soát kế toán.
