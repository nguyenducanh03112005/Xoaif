# F4 — cuboid theo quý và suppression bổ sung (DEV-only)

**Nhãn:** khám phá, chưa xác nhận ngoài mẫu. Protocol SHA-256 `d865e0f5772f78e07c509affe207f52c53611b1d6ac2792eb40784e9e2c3d380`. Nguồn DEV `load_dev_orders()`, 6.093 đơn status 3 không quà; không đọc test.

Hai thiết kế đã đăng ký: quý×kênh gộp×RFM 3 nhóm và quý×cỡ giỏ×RFM 3 nhóm. Suppression primary nếu orders hoặc customers<30. Quy tắc complementary ẩn thêm ô để mọi roll-up theo cặp chiều không còn đúng một ô ẩn; không xuất margin. Test đơn vị xác nhận hai điều kiện.

## Kết quả suppression

| Cuboid | Ô | Primary ẩn | Complementary ẩn | Tổng ẩn | Tỷ lệ ẩn | Đạt mục tiêu <30% |
|---|---:|---:|---:|---:|---:|---|
| Quý×kênh×RFM | 42 | 13 | 11 | 24 | 57,14% | Không |
| Quý×cỡ giỏ×RFM | 42 | 15 | 13 | 28 | 66,67% | Không |

**Không đưa hai cuboid này vào dashboard.** Kết quả không đạt mục tiêu dù đã gộp kênh và dùng quý; không hạ ngưỡng suppression 30 hay đổi quy tắc. Các file được giữ làm bằng chứng thất bại thiết kế và không phải đầu vào sản phẩm. Cần protocol mới nếu thử chiều thô hơn.

Các bảng CSV giữ ô suppressed với mọi measures là NULL; JSON ghi số ô và tỷ lệ theo từng cube. Không có margins/subtotals được xuất. Phần suppression bổ sung che các ô còn lại khi cần bảo vệ residual. Đây là biện pháp giảm suy luận từ margins có trong bảng, không thay thế kiểm soát truy vấn tùy ý nếu triển khai interactive.
