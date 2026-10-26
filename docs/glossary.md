# Chú giải thuật ngữ và mốc thời gian

Nguồn định nghĩa là `config/split.yaml` đã khóa, amendment ngày mở cửa hàng ở `config/amendment_01_analysis_start.yaml`, và quy tắc tiền đang có hiệu lực ở `config/amendment_03_money_adjustment.yaml`. Các tên N/W dưới đây giữ nguyên theo cấu hình/code.

| Thuật ngữ | Tên trong code/config | Nghĩa đang dùng |
| --- | --- | --- |
| `N` | `primary_n_days`, `n_candidates_days` | Chân trời nhãn theo ngày lịch; nhãn tìm đơn mua hợp lệ trong `(T,T+N]`. N chính là 180 ngày. |
| `L` | `l_candidates_days` | Đệm hoàn hàng/trạng thái sau chân trời; chính là 7 ngày. |
| `W` | `window_days` | Độ dài cửa sổ các ngày T của kỳ test, không phải lookback đặc trưng; chính là 180 ngày. |
| `T` | Mốc ngày đánh giá | Ngày địa phương `Asia/Ho_Chi_Minh` để tính đặc trưng trước T và bắt đầu theo dõi nhãn. |
| `analysis_start` | Amendment 01 | Ngày cửa hàng bắt đầu hoạt động theo chủ dự án: `2024-04-01`; trước đó là giai đoạn bán thử và bị loại khỏi hành vi. |
| `test_start` | `config/split.yaml` | Ngày đầu tiên trong kỳ test và cận loại trừ của dev: `2025-10-22`. |
| `DATA_CUTOFF` | `config/split.yaml` | Cận phải loại trừ của dữ liệu hoàn chỉnh; snapshot bao phủ đến hết ngày trước đó. |
| `H_obs` | Amendment 03 | Toàn bộ lịch sử hợp lệ `[analysis_start,T)`, không phải `W`. |
| `revenue_recognized` / doanh thu ghi nhận | `src/features/money.py`; amendment 03 | `after_sub_discount-shipping_fee`, trừ trường hợp `after == total_price-total_discount` và ship dương thì dùng `after`. Chỉ status 3. |
| `price_adjustment` | `src/features/money.py`; amendment 03 | `revenue_recognized - (total_price-total_discount)`. Dương là phí/giá cao hơn; âm là ưu đãi thêm; bằng 0 là khớp. Giữ đơn có điều chỉnh. |
| `is_gift` | `src/features/money.py`; amendment 03 | Doanh thu bằng 0, hoặc `total_price=0` và `after=0`; loại khỏi F/R, nhãn, giỏ hàng và chỉ số giá trị, nhưng đếm riêng. |
| `negative_revenue` | `src/features/money.py`; amendment 03 | Doanh thu âm; Monetary của đơn bằng 0, nhưng đơn vẫn nằm trong F/R. Cổng kỹ thuật dừng nếu vượt 1% status-3 dev. |

## Ví dụ theo cấu hình hiện hành

- Dev hiệu dụng là `[2024-04-01,2025-10-22)`.
- Kỳ test T là `[2025-10-22,2026-04-20)`, đúng 180 ngày. Các ngày T chạy đến `2026-04-19`.
- Với `T=2025-10-22`, nhãn chính nhìn `(T,T+180]`; sau `L=7`, nhãn chốt tại `label_asof=2026-04-27`.
- `N=365,W=365` đã được xác định là không khả thi và không làm thay đổi split chính.

## Cửa sổ quan sát đặc trưng `H_obs`

Tất cả giao dịch trong ngày T hoặc sau T bị loại khỏi đặc trưng. `H_obs=[analysis_start,T)` không đồng nhất với `W`, độ dài cửa sổ các ngày T. Quy tắc hiện hành nằm trong amendment 03; `split.yaml` và amendment 01 không bị sửa.

