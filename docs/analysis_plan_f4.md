# Đăng ký trước F4 — cuboid OLAP gọn và suppression bổ sung

- **Phạm vi:** khám phá DEV-only từ `load_dev_orders()` (status 3, không quà, DEV date gate); không dùng test raw, không thay A4 cuboid đã lưu.
- **Cuboid dashboard:** (1) quý × kênh gộp `{Facebook, Khác/thiếu}` × RFM `{mua lặp lại, một đơn gần đây, một đơn đã lâu}`; (2) quý × cỡ giỏ `{1–2, 3+}` × RFM cùng ba nhóm. Hạn chế chiều đã định trước để giảm ô nhỏ.
- **Suppression:** primary hide nếu orders<30 hoặc customers<30; ngưỡng 30 không đổi. Complementary suppression: trong mỗi quý, với mọi cặp chiều được công bố (kênh/cỡ giỏ ↔ RFM), nếu một subgroup có ít nhất một ô ẩn thì ẩn ít nhất hai ô; lặp đến điểm cố định. Không xuất margin tổng/subtotal; metadata nêu rõ không thể drill qua ô ẩn. Chạy bộ lọc suppression trước mọi ghi file.
- **Mục tiêu:** tỷ lệ ô bị ẩn <30% mỗi cube; nếu không đạt, báo không phù hợp dashboard, không nới ngưỡng/quy tắc hậu nghiệm.
- **Metric:** rows, suppressed_primary, suppressed_complementary, suppressed_total, suppression_rate mỗi cuboid; cube xuất count/revenue đều NULL khi ẩn. Tổng doanh thu không xuất riêng.
- **Số phép so sánh:** đúng hai cuboid, hai chiều thời gian/kinh doanh như trên; không thêm drill-down/subgroup.
- **Đầu ra:** hai CSV safe và JSON metric. Test đơn vị cho ngưỡng primary, complementary suppression, không có cell nhỏ hiển thị, và tính chất che ít nhất hai nhánh khi có thể suy ra residual.
