# Mùa vụ, dịp, kênh và điều chỉnh giá — DEV-only

**Nhãn:** khám phá, chưa xác nhận ngoài mẫu. Kế hoạch đăng ký trước: `docs/analysis_plan_wp4.md`; SHA-256 `588ec1e6161e1ee0edccdb19888a12f2f41fa1074798e924f82182fddb8222a0`. Nguồn tính: `scripts/analyze_seasonality_dev.py`. DEV `[2024-04-01, 2025-10-22)`, đơn status 3 bỏ quà cấp đơn; 6.378 đơn. Không đọc test raw/nhãn. Bootstrap seed 20261028, 2.000 lượt.

## Chuỗi tháng và tuần

Chuỗi có 569 ngày, 19 bucket tháng và 82 bucket tuần. Tháng 2025-10 và tuần đầu/cuối là kỳ không trọn vẹn theo ranh giới DEV. Bảng tháng/tuần có đơn, doanh thu ghi nhận, trend moving average (3 tháng/13 tuần), seasonal mean theo tháng lịch/ISO week và phần dư. Seasonal mean chỉ được tính khi có ít nhất hai quan sát lặp của cùng kỳ; các kỳ chỉ quan sát một lần có seasonal component bằng 0 và cờ `seasonality_supported_repeated_period=False`.

Đây là phép phân rã mô tả, không phải dự báo. Chuỗi tháng có 19 điểm; chỉ một Tết trọn vẹn. Chuỗi tuần chỉ bao phủ khoảng một năm rưỡi; các thành phần mùa vụ không đủ cơ sở để lập lịch tồn kho cứng. Nên theo dõi số đơn và doanh thu hàng tuần, rồi kết hợp với tồn kho và lịch chiến dịch thực tế.

## Dịp lễ và sale proxy

Calendar có 12 event rows nằm trong DEV; các cửa sổ ±7 ngày chồng nhau được gộp thành 9 event blocks. Mỗi block có hai so sánh (đơn/ngày và doanh thu/ngày), 18 dòng tổng hợp. Control là ngày cùng thứ trong tuần cách mốc 28–56 ngày và nằm ngoài event blocks. Mỗi event/control sample dưới 30 ngày nên kết quả chỉ mô tả, dù bảng có CI block bootstrap.

Ví dụ: cửa sổ Tết 2025 có 4,60 đơn/ngày so với 18,17 ở các ngày control (tỷ số 0,253); doanh thu ghi nhận 3,83 triệu/ngày so với 8,44 triệu (0,454). Hai mốc 30/4–1/5 năm 2025 gộp có 7,00 đơn/ngày so với 15,72 (0,445). Đây có thể phản ánh lịch nghỉ, ngày mở cửa, nguồn hàng, mức ghi nhận dữ liệu hoặc yếu tố khác; không gọi là tác động của dịp lễ.

Hai ngày sale là proxy lịch, không phải chiến dịch đã xác nhận của shop. Cửa sổ 11/11/2024 ghi nhận tỷ số đơn 1,115; 12/12/2024 là 0,691. Không suy ra hiệu quả khuyến mãi. Tệp calendar không có mốc 8/3, 20/10, 20/11 hoặc 25/12 trong DEV; phân tích này không tự bổ sung các ngày đó. Cần cập nhật lịch tham chiếu có nguồn nếu muốn phân tích các dịp này ở lượt sau.

## Kênh

Trường kênh có mặt ở 3.996/6.378 đơn DEV status 3 không quà (62,64%). Trong 3.641 khách có đơn đầu đủ 180 ngày, kênh đơn đầu là Facebook n=2.254, thiếu n=1.257, Instagram + nguồn hiếm n=130. Nhóm Instagram đã gộp nguồn hiếm; các nhãn theo quy tắc hiện có trong `docs/channel_monthly_coverage.md`.

| Kênh đơn đầu | Khách | AOV hóa đơn đầu (CI 95%) | Mua lại 180 ngày (CI 95%) |
|---|---:|---:|---:|
| Facebook | 2.254 | 475.919₫ (438.707–522.095₫) | 11,67% (10,29–13,04%) |
| Thiếu kênh | 1.257 | 361.998₫ (324.305–407.457₫) | 8,51% (7,00–10,10%) |
| Instagram + nguồn hiếm | 130 | 344.875₫ (286.625–419.281₫) | 6,92% (3,08–11,54%) |

Các CI bootstrap theo khách; nhóm nhỏ hơn 30 bị ẩn. Kênh thiếu nhiều, và tên nguồn có thể không phải kênh tiếp thị đầy đủ; chênh lệch không chứng minh kênh tạo ra mua lại hay hóa đơn cao hơn.

## Mức giảm giá và điều chỉnh giá

Phân tích dùng lần mua đầu của cùng 3.641 khách trưởng thành. Median dương của `total_discount/total_price` là 9,09%; đây chỉ là ngưỡng chia nhóm trong DEV. Nhóm tỷ lệ giảm dương thấp có 750 khách, AOV 517.920₫ (CI 477.033–564.722₫), mua lại 9,87% (7,73–12,00%). Nhóm tỷ lệ giảm dương cao có 713 khách, AOV 712.363₫ (588.514–859.266₫), mua lại 11,50% (9,26–13,89%). Nhóm không có giảm giá ghi nhận n=2.177, AOV 310.534₫ (300.270–320.665₫), mua lại 10,24% (8,96–11,53%).

Chênh lệch AOV không nói ưu đãi làm tăng giỏ: nhóm mức giảm cao được định nghĩa từ chính số tiền chiết khấu và có thể phản ánh giỏ gốc lớn hơn. `price_adjustment` âm có n=5 và bị suppression; chỉ số điều chỉnh cũng không đồng nghĩa với giảm giá, có thể gồm phí hoặc sai khác ghi nhận. Không suy luận lợi nhuận do không có giá vốn.

## Lịch hành động gợi ý

| Thời gian | Việc nên chuẩn bị | Căn cứ và giới hạn |
|---|---|---|
| Tháng 1–2 | Xác nhận lịch mở cửa, lịch giao hàng và kế hoạch Tết; kiểm tra tồn kho trước khi tăng đặt hàng. | Có mốc năm mới/Tết trong lịch; DEV chỉ có một Tết trọn vẹn, số ngày event nhỏ. |
| Tháng 4–5 | Rà soát trước giờ mở cửa, hàng cần bổ sung và nội dung hướng dẫn trước cụm ngày lễ cuối tháng 4/đầu tháng 5. | Có event blocks trong calendar; đơn quanh các cửa sổ quan sát thấp hơn control nhưng n ngày nhỏ và không có dữ liệu giờ mở cửa. |
| Tháng 9 | Kiểm tra lịch giao/nhận hàng trước Quốc khánh; theo dõi số đơn tuần thực tế. | Hai event windows Quốc khánh cho tỷ số quan sát khác nhau, không thành quy luật ổn định. |
| Tháng 11–12 | Chỉ lập chương trình nếu shop xác nhận có campaign; soạn sẵn nội dung và kiểm tra tồn kho, không mặc định chạy giảm giá. | 11/11 và 12/12 là sale proxy; không có lịch chiến dịch của cửa hàng. |
| Mọi tháng | Theo dõi dashboard tuần/tháng và cập nhật lịch chiến dịch thực tế cùng dữ liệu tồn kho. | Các chuỗi DEV ngắn, thiếu hai mùa Tết và thiếu dữ liệu tồn kho/chiến dịch. |

Đây là khung chuẩn bị, không phải dự báo nhu cầu. Bất kỳ chăm sóc khách nào cũng cần thông tin liên hệ hợp lệ và sự đồng ý; cửa hàng cần kiểm tra quy định bảo vệ dữ liệu cá nhân áp dụng. Đây không phải tư vấn pháp lý.
