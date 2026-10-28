# Sản phẩm, giỏ hàng và combo — DEV-only

**Nhãn:** khám phá, chưa xác nhận ngoài mẫu. Kế hoạch đăng ký trước: `docs/analysis_plan_wp3.md`; SHA-256 đã ghi cùng kết quả là `ec35ed48b995101ccf622d224ed44a6994858d9a5479175f80de648fe9a21483`. Nguồn tính: `scripts/analyze_product_journey_dev.py`. DEV `[2024-04-01, 2025-10-22)`, status 3, bỏ quà cấp đơn và dòng quà theo amendment đã khóa. CI bootstrap 2.000 lượt, seed 20261028, theo khách; đối chiếu test chỉ đọc `outputs/tables/test_combos_frozen.csv` đã commit. Không đọc test raw hay nhãn.

## Nhật ký chạy A2

1. Lần thử đầu bị dừng vì vòng lặp bootstrap quá chậm, trước khi tạo đầu ra; không có metric một phần.
2. Lần chạy kế tạo bảng nhưng bị loại khỏi diễn giải: bước chuẩn hóa tháng đã bỏ quá nhiều strata, CI cho strata trống bị ghi thành 0 và bảng chưa nối với aggregate test đã commit. Bản chạy này có metadata tạm 6.349 giỏ, 3.635 khách đủ theo dõi và 77 sản phẩm đủ ngưỡng; các bảng đầu ra đã được ghi đè sau sửa lỗi. Không dùng các CI/so sánh của lần chạy này.
3. Bản cuối dùng bootstrap vector hóa phân tầng theo tháng, không yêu cầu tối thiểu 30 khách trong từng strata tháng nhưng vẫn yêu cầu ít nhất 30 khách ở mỗi nhóm toàn cohort; strata không có cả hai nhóm được loại khỏi phép chuẩn hóa và độ phủ tháng được xuất rõ. 24 tổ hợp test được ghép từ đúng bảng aggregate đã commit. Các đầu ra cuối nằm ở các bảng dẫn dưới đây.

## Giỏ đầu và mua lại trong 180 ngày

Có 6.349 giỏ DEV không quà có ít nhất một sản phẩm; 6.006 giỏ có ít nhất hai sản phẩm dùng cho luật combo. Cohort giỏ đầu có 3.635 khách được theo dõi đủ 180 ngày theo ngày mua đầu chính xác; 378 khách có giỏ kế tiếp ở một ngày địa phương khác trong 180 ngày. Bảng `outputs/tables/first_basket_product_repeat_dev.csv` xét 77 sản phẩm có mặt ở ít nhất 30 giỏ đầu; số khách của nhóm có/không sản phẩm và CI được ghi theo từng sản phẩm.

Tỷ lệ mua lại thô của khách có PORTCARD HƯỚNG DẪN CHĂM CÂY ở giỏ đầu là 11,17%, so với 8,77% nếu không có sản phẩm này. Sau chuẩn hóa theo tháng mua đầu trên cùng các tháng có cả hai nhóm, chênh lệch là +1,07 điểm phần trăm (CI 95% −1,29 đến +3,35), độ phủ 13/13 tháng trưởng thành (100%). Với TÚI GIẤY XOAIF GARDEN, tỷ lệ thô là 11,94% so với 9,14%; chênh lệch chuẩn hóa +1,26 điểm (−1,15 đến +3,78), cũng 13/13 tháng. Các CI đều chứa 0.

Trong 77 so sánh mô tả, 5 CI bootstrap của chênh lệch chuẩn hóa nằm trên 0, 8 nằm dưới 0, còn 64 chứa 0. Chưa hiệu chỉnh nhiều phép so sánh; đây là danh sách khám phá, không phải kiểm định xác nhận. Một vài sản phẩm có độ phủ tháng chuẩn hóa thấp hơn 13 tháng; bảng xuất `standardized_month_weight_coverage` và `standardized_month_count`. Các ước lượng đó áp trên phần tháng có cả hai nhóm và không đại diện đầy đủ cùng một tập tháng giữa mọi sản phẩm.

## Sản phẩm ở lần mua kế tiếp

Chuỗi chỉ coi giao dịch ở ngày địa phương sau ngày đầu là lần kế tiếp; các giao dịch cùng ngày không tạo thứ tự. Có 2.746 cặp sản phẩm có hướng quan sát được, 23 cặp có ít nhất 30 khách; bảng hiển thị 20 cặp có số khách nhiều nhất. Cặp thường gặp nhất là PORTCARD → PORTCARD, 190 khách, khoảng cách median 23,5 ngày (CI 14,5–31). TÚI GIẤY XOAIF GARDEN → PORTCARD có 133 khách, median 26 ngày (19–33); PORTCARD → TÚI GIẤY có 132 khách, median 20 ngày (13–27). Khoảng cách được tính trên khách có cặp đó; đồng xuất hiện giữa nhiều sản phẩm trong cùng giỏ không xác định thứ tự.

Khác biệt với A1: A1 tính giao dịch thứ hai kể cả trong cùng ngày và dùng cohort tháng trưởng thành; A2 yêu cầu giỏ có sản phẩm, ngày thứ hai khác ngày đầu và theo dõi đủ 180 ngày từ ngày mua đầu. Vì vậy các mẫu số/số sự kiện không thay thế trực tiếp cho nhau.

## 24 combo đã khóa

Không thay đổi danh sách 24 combo. Bảng `outputs/tables/frozen_combo_supplement_dev.csv` có support, confidence hai chiều, lift và ba thước đo bổ sung: Kulczynski, all-confidence, imbalance ratio; đồng thời ghi ổn định theo 19 tháng DEV và các cột test lấy từ aggregate đã commit. DEV có 17/24 cặp lift>1; bảng test đóng băng có 21/24 lift>1, trong đó 16 cặp cùng vượt 1 ở cả hai cohort. Đây là so sánh mô tả giữa hai cửa sổ trong cùng snapshot, không phải xác nhận độc lập.

Tất cả 24 combo xuất hiện trong 16–19 trên 19 tháng DEV; hệ số biến thiên support theo tháng nằm trong 0,232–1,068 (median 0,516). DEV chỉ có một Tết trọn vẹn nên không gán nhãn mùa vụ ổn định.

Xếp hạng bundle là thứ hạng để thảo luận, trung bình percentile rank của support, lift, CV support thấp và median doanh thu ghi nhận của hóa đơn chứa cặp. Hạng 1 PORTCARD + CHẬU MOCHI có support DEV 8,49% (510/6.006), lift 0,982; tháng có cặp 19/19, median hóa đơn 235.000₫, tổng giá niêm yết 61.000₫. Aggregate test đã commit có support 3,17% (69/2.174), lift 1,376. Hạng 6 ĐÔ LA NGỌC BÍCH + CHẬU TRỤ có lift DEV 1,741 và lift test 2,562; support lần lượt 5,81% và 10,17%. Các ví dụ cho thấy thứ hạng tổng hợp và lift đơn lẻ không đồng nghĩa với hiệu quả bán hàng.

Giá niêm yết gộp chỉ có khi cả hai sản phẩm có giá dương trong bảng đóng băng; ô thiếu để trống. Median doanh thu là giá trị hóa đơn của giỏ có cặp, không phân bổ doanh thu/chiết khấu xuống sản phẩm, không phải giá bán bundle hay lợi nhuận.

## Vai trò sản phẩm — mô tả

`outputs/tables/product_roles_dev.csv` cho 77 sản phẩm có ít nhất 30 khách giỏ đầu: tỷ lệ giỏ đầu, số khách có sản phẩm ở đơn kế tiếp và median giá trị hóa đơn của các đơn có sản phẩm. PORTCARD có mặt ở giỏ đầu của 2.472/3.635 khách (68,01%); xuất hiện trong giỏ thứ hai của 241 khách; median hóa đơn chứa sản phẩm 255.000₫ trên 4.134 đơn. TÚI GIẤY có mặt ở giỏ đầu của 1.633 khách (44,92%), xuất hiện ở giỏ thứ hai của 167 khách; median hóa đơn 230.000₫ trên 2.653 đơn. Các con số mô tả độ phủ sản phẩm trong hóa đơn, không nói phần doanh thu do sản phẩm tạo ra.

## Hàm ý thử nghiệm và giới hạn

- Có thể dùng các cặp ổn định và có giá niêm yết đủ làm ứng viên bố trí trưng bày/bundle để thử; bắt đầu bằng nhóm đối chứng và đo tỷ lệ thêm sản phẩm vào giỏ cùng giá trị hóa đơn. Xếp hạng không chứng minh khách sẽ mua thêm.
- Có thể thử nội dung chăm sóc vào khoảng 20–30 ngày sau lần mua đầu cho các chuỗi có đủ mẫu; thời điểm này là mô tả khoảng cách, không phải thời điểm tối ưu đã xác nhận. Liên hệ khách là giả thuyết hành động; điều kiện tiên quyết là có thông tin liên hệ hợp lệ và khách đồng ý nhận liên hệ. Cửa hàng cần kiểm tra quy định bảo vệ dữ liệu cá nhân áp dụng; đây không phải tư vấn pháp lý.
- Dữ liệu quan sát không kiểm soát tồn kho, giá/khuyến mãi, mục đích mua, mùa, nội dung tư vấn hay quan hệ giữa sản phẩm và khách. Không suy ra nhân quả, lợi nhuận hay hiệu quả. CI không điều chỉnh multiplicity của 77 sản phẩm.
