# F4b — cuboid quý 2 chiều sau khi F4 không đạt

**Nhãn:** khám phá, chưa xác nhận ngoài mẫu. Đăng ký riêng `docs/analysis_plan_f4b.md`, SHA-256 `1459e9428c668c7adf3ac7a8ddc98584e531419e145a884f8d71f353591b846b`. Nguồn DEV-only 6.093 đơn status 3 không quà; ngưỡng 30.

| Cuboid | Ô | Primary | Complementary | Tổng ẩn | Tỷ lệ ẩn | Mục tiêu |
|---|---:|---:|---:|---:|---:|---|
| Quý×RFM gộp (mua lặp lại/một đơn) | 14 | 0 | 0 | 0 | 0% | Đạt <30% |
| Quý×kênh gộp (Facebook/khác-thiếu) | 14 | 0 | 0 | 0 | 0% | Đạt <30% |

Kết quả F4 gốc vẫn giữ nguyên: hai cube 3 chiều có suppression 57,14% và 66,67%, không đưa vào dashboard. F4b là thiết kế mới đăng ký trước sau khi F4 thất bại; không sửa hồi tố giao thức cũ.

Hai bảng F4b không xuất grand total/subtotal; measures của primary/complementary suppressed đều NULL. Kiểm thử synthetic xác nhận primary threshold và complementary suppression che nhánh thứ hai khi một quarter có đúng một ô primary-hidden. Bảng: `outputs/tables/quarter_rfm_f4b.csv`, `outputs/tables/quarter_channel_f4b.csv`; metric riêng từng cube: `outputs/metrics/dashboard_cuboids_f4b.json`.

Các bảng là aggregate sạch để dashboard có thể đọc offline; chưa nối vào giao diện dashboard trong F4.
