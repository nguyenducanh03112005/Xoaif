# Doanh thu ghi nhận: định nghĩa đang có hiệu lực và kiểm toán

## Phạm vi, bằng chứng và thời điểm quyết định

Amendment 03 (`config/amendment_03_money_adjustment.yaml`) thay thế quy tắc tiền của amendment 02. Quy tắc áp dụng cho đơn status `3` trong `[analysis_start,test_start)` theo giờ `Asia/Ho_Chi_Minh` (`[2024-04-01,2025-10-22)`). Status 3 được chủ cửa hàng xác nhận là đơn đã nhận và được ghi nhận doanh thu, kể cả khi nhân viên chưa thao tác xác nhận thanh toán trên app. Đơn tại quầy thu tiền mặt; các trường thanh toán app thời kỳ đầu không đáng tin. Không dùng `cash`, `cod`, `prepaid`, `transfer_money` hoặc `money_to_collect` làm bộ lọc hay bằng chứng thanh toán; `cod` âm không phải lý do loại đơn.

Bằng chứng là rà soát mẫu 13 đơn và xác nhận bằng lời của chủ cửa hàng. `dash_*` trong file mẫu vẫn trống; không có bảng dashboard chi tiết để đối soát. Trong mẫu được rà soát, 12/13 đơn khớp `after_sub_discount = total_price - total_discount + shipping_fee`; 13/13 khớp `total_price = Σ variation_info.retail_price × quantity`. Phép so khớp này xác định cách xử lý trường tiền, không phải đối soát độc lập ngân hàng hay kế toán.

Quyết định amendment 03 được đưa ra sau khi cổng amendment 02 ghi nhận 701/6.400 đơn (10,95%) vượt ngưỡng 5%. Chủ dự án thay đổi theo hiểu biết nghiệp vụ rằng status 3 là doanh thu đã nhận và các chênh lệch gồm phí phát sinh/ưu đãi. Việc đổi quy tắc không dựa trên nhãn hoặc hành vi test. Đây là quyết định nghiệp vụ sau khi xem kết quả cổng cũ; phải đọc cùng độ nhạy được ghi trước, không xem như kiểm định độc lập.

Số 701/6.400 là kết quả chẩn đoán cổng Amendment 02. Số 639/6.400 trong audit Amendment 03 là nhãn phân loại hiện tại `adj_unexplained`, dựa trên các quan hệ trường tiền được ghi trong Amendment 03. Hai con số dùng các định nghĩa khác nhau, không so sánh như một xu hướng giảm/tăng.

## Công thức chính

Đặt `after = total_price_after_sub_discount`, `base = total_price - total_discount`, và `shipping = shipping_fee`:

- Mặc định: `revenue_recognized = after - shipping`.
- Ngoại lệ khớp chính xác: nếu `after == base` và `shipping > 0`, dùng `revenue_recognized = after` để không trừ ship hai lần.
- `price_adjustment = revenue_recognized - base`. Giá trị dương biểu thị phí phát sinh hoặc giá bán cao hơn; âm biểu thị ưu đãi thêm; bằng 0 nghĩa là khớp công thức niêm yết sau giảm.
- `gross_list_value = total_price`, dùng cho phân tích giỏ hàng và giá niêm yết. Tổng dòng hàng được kiểm tra bằng `Σ variation_info.retail_price × quantity` khi có đủ dữ liệu.

Các chênh lệch được giữ lại để phân tích; không loại đơn chỉ vì `price_adjustment != 0`. `adj_unexplained` đánh dấu các trường hợp `after` không khớp đẳng thức dự kiến, ngoại lệ ship chưa cộng, các mẫu `after=total+shipping`, `after=total`, phần dư chính xác `±shipping`/`±discount`. Nhóm còn lại được đánh dấu chưa giải thích và phân khoảng theo độ lớn phần dư. Phân loại mẫu là chẩn đoán, không thay đổi công thức chính.

## Đơn tặng, số âm và hành vi khách hàng

Đánh dấu `is_gift` nếu doanh thu ghi nhận bằng 0, hoặc nếu `total_price=0` và `after=0`. Giữ đơn trong raw và đếm riêng; loại khỏi F/R, nhãn, giỏ hàng, doanh thu ghi nhận, Monetary, AOV và các thống kê giá trị đơn.

Đánh dấu `negative_revenue` nếu doanh thu ghi nhận âm và đơn không phải quà. Đóng góp Monetary của đơn đó bằng 0; vẫn giữ đơn trong Frequency và Recency. Cổng dừng kỹ thuật duy nhất của phần tiền là tỷ lệ `negative_revenue` vượt 1% của toàn bộ status-3 dev. Không dùng cổng bất thường 5% của amendment 02 nữa.

## Độ nhạy đã ghi trước

- **A — công thức thay thế:** `total_price - total_discount`; giữ loại quà và đặt đóng góp Monetary của đơn âm bằng 0. Báo chênh lệch doanh thu tổng, tỷ lệ đơn lệch quá 1%, và Spearman giữa Monetary theo khách. Đây là so sánh báo cáo, không phải cổng dừng.
- **B — bỏ điều chỉnh:** loại hợp các đơn `price_adjustment != 0` hoặc `adj_unexplained`; chạy lại phân khúc và phân loại với cùng mốc thời gian và chia khách. Không phân bổ điều chỉnh ở mức đơn xuống từng sản phẩm.

## Giới hạn

Chỉ có status hiện tại; không dùng `status_history`, nên không thể khôi phục độc lập trạng thái tại `T+N+L`. Định nghĩa này là “doanh thu ghi nhận” theo quyết định nghiệp vụ, không phải lợi nhuận hay đối soát kế toán. Đơn trước 04/2024 thuộc giai đoạn bán thử, giữ trong raw nhưng không tham gia hành vi. `H_obs` là toàn bộ lịch sử hợp lệ `[analysis_start,T)`. **[LỊCH SỬ — tại thời điểm viết]** Test chưa mở và chưa có nhãn/hành vi test được nạp; trạng thái hiện hành tại `docs/test_provenance_note.md`.

Kết quả định lượng mới được sinh trong `outputs/metrics/day2_money_audit.json`, bảng không định danh trong `outputs/tables/money_diagnosis.csv`, và bản tóm tắt tại `docs/money_audit.md`.
