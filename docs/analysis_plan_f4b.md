# Đăng ký trước F4b — cuboid 2 chiều thô hơn sau F4

- **Lý do:** hai thiết kế F4 đã đăng ký bị ẩn 57,14% và 66,67%; giữ nguyên, không sửa kết quả. Thử riêng protocol thô hơn.
- **Phạm vi:** DEV-only, chỉ `load_dev_orders()`, status 3 không quà, không test raw/nhãn/hành vi.
- **Hai cuboid cố định:** (1) quý × phân khúc RFM 2 nhóm `{mua lặp lại, một đơn}`; (2) quý × kênh 2 nhóm `{Facebook, Khác/thiếu}`. Không kết hợp hai chiều khách/kênh/cỡ giỏ trong cùng cube. Không xuất margins/subtotals.
- **Suppression:** primary orders<30 hoặc customers<30, ngưỡng bất biến 30. Trong từng quý của mỗi cube 2 nhóm, nếu một nhóm primary-hidden thì complementary-hide nhóm còn lại; nếu sau đó vẫn chỉ có một ô ẩn thì thiết kế dừng và không dùng cube.
- **Mục tiêu:** tỷ lệ ô ẩn <30% cho từng cube; mọi kết quả báo cáo, kể cả không đạt. Không chọn lại dimensions.
- **Đầu ra:** CSV safe (measures NULL khi ẩn), JSON rates riêng; tests cho primary/complementary và ngưỡng bất biến.
