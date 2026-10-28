# Đăng ký trước A3 — mùa vụ, kênh và điều chỉnh giá DEV

- **Trạng thái:** đăng ký trước ngày 2026-10-28, trước khi chạy phân tích A3 mới. Khám phá, chưa xác nhận ngoài mẫu.
- **Cohort:** DEV `[2024-04-01, 2025-10-22)`, đơn status 3, loại quà cấp đơn. Dùng `load_dev_orders()` và DEV date gate. Không dùng test raw/labels/behaviors.
- **Lịch:** chỉ các dòng trong `data/reference/vietnam_holiday_sale_calendar_2024-04_to_2026-10.csv` có ngày nằm trong DEV. Không tự thêm mốc 8/3, 20/10, 20/11 hay 25/12 nếu không có trong tệp; proxy sale không xác nhận chiến dịch của cửa hàng. Các cửa sổ ±7 ngày chồng nhau được gộp thành một event block để không đếm ngày hai lần.
- **Seed/CI:** 20261028; 2.000 bootstrap. Chỉ số theo khách dùng cluster bootstrap khách. Với so sánh event-window theo ngày, dùng moving-block bootstrap 7 ngày để giữ tương quan chuỗi; đây là mở rộng mô tả, không tạo suy luận nhân quả. Cấp nhóm dưới 30 chỉ mô tả và bị suppression theo quy tắc hiện hành.

## Phân tích khóa trước

1. **Chuỗi tháng và tuần:** tạo chuỗi liên tục số đơn và doanh thu ghi nhận. Monthly trend là centered moving average 3 kỳ; seasonal component là trung bình phần lệch khỏi trend theo tháng lịch; residual = observed − trend − seasonal. Weekly dùng centered moving average 13 tuần và seasonal component theo ISO week chỉ khi có quan sát lặp qua năm. Xuất observed/trend/seasonal/residual cho cả count và recognized revenue. Không dự báo. Số chu kỳ ngắn khiến mùa vụ không ổn định, nhất là tuần.
2. **Dịp lễ/Tết/sale proxy:** mọi event block trong calendar DEV, cửa sổ ngày −7…+7 (gộp khi chồng). So trung bình số đơn/ngày và doanh thu/ngày với các ngày control cùng thứ trong tuần, cách event 28–56 ngày trước/sau, bỏ control rơi vào bất kỳ event window nào. Dùng block bootstrap 7 ngày cho chênh lệch và tỷ số; báo n ngày event/control. Đây là chênh lệch quan sát, không gọi uplift nhân quả. Nếu control count nhỏ hơn 30 ngày hoặc event window nằm sát ranh giới DEV thì chỉ mô tả/đánh dấu không đủ dữ liệu.
3. **Kênh:** nhãn kênh đúng theo `docs/channel_monthly_coverage.md`; nhóm kênh có dưới 30 đơn gộp/ẩn. Báo coverage (đơn có kênh / toàn bộ đơn DEV), số đơn, AOV recognized revenue, và mua lại 180 ngày theo kênh của đơn mua đầu trên khách đủ theo dõi. Bootstrap theo khách cho AOV/retention; không suy ra kênh gây ra chênh lệch.
4. **Điều chỉnh giá:** trên đơn mua đầu của khách đủ theo dõi, nhóm tỷ lệ `total_discount/total_price` thành không giảm giá, giảm dương thấp (≤ median dương DEV) và giảm dương cao (> median dương DEV); nếu giá gốc không dương thì nhóm riêng/ẩn. Báo tỷ lệ mua lại 180 ngày và recognized revenue/AOV của đơn đầu theo nhóm, CI bootstrap theo khách. Bổ sung mô tả `price_adjustment` âm/bằng 0/dương như diagnostic riêng; không gọi giá trị điều chỉnh là giảm giá thật nếu định nghĩa tiền chưa xác minh.

## Số phép so sánh và giới hạn

- Chuỗi: 2 tần suất × 2 biến (orders, recognized revenue), toàn bộ kỳ quan sát; không kiểm định.
- Dịp: toàn bộ event blocks tạo theo quy tắc lịch, mỗi block × 2 kết quả; không chọn theo kết quả đẹp.
- Kênh: mọi nhãn đã quy ước × AOV và retention; điều chỉnh giá: 3 nhóm chính × retention/AOV cùng các nhóm price-adjustment diagnostic. Ghi số nhóm thực tế và nhóm bị suppression trong đầu ra.
- Không có dữ liệu chiến dịch của cửa hàng, giá vốn hay tồn kho. Calendar sale là proxy giả định; DEV có một Tết trọn vẹn. Không kết luận lợi nhuận, tác động nhân quả, hiệu quả khuyến mãi hay dự báo chắc chắn. Nhóm n<30 chỉ mô tả.
