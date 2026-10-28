# Giữ chân và giá trị khách hàng — DEV-only

**Nhãn:** khám phá, chưa xác nhận ngoài mẫu. Nguồn phân tích: `scripts/analyze_customer_value_dev.py`; kế hoạch đã đăng ký trước tại `docs/analysis_plan_wp2.md`. Cửa sổ DEV `[2024-04-01, 2025-10-22)`, đơn status 3 không quà; 6.093 đơn hợp lệ có khóa khách, 5.169 khách. Các CI là bootstrap 2.000 lần theo khách, seed 20261028. Mọi con số tiền là doanh thu ghi nhận, không phải lợi nhuận.

## Retention và kiểm duyệt

Retention yêu cầu có một **ngày mua sau ngày mua đầu** trong `(first_purchase_date, first_purchase_date+H]`. Chỉ đưa cohort tháng có `month_end + H < 2025-10-22` vào mẫu số; tháng chưa đủ thời gian bị loại vì kiểm duyệt phải. Theo kỳ hạn, các tháng bị loại là:

- 30 ngày: 2025-09 và 2025-10.
- 60 ngày: 2025-08 đến 2025-10.
- 90 ngày: 2025-07 đến 2025-10.
- 180 ngày: 2025-04 đến 2025-10.

Tỷ lệ tổng trên các cohort-month đủ trưởng thành:

| Kỳ hạn | Cohort/khách | Mua lại | Tỷ lệ (CI 95%) |
|---:|---:|---:|---:|
| 30 ngày | 4.524 | 255 | 5,64% (4,97–6,34%) |
| 60 ngày | 4.351 | 313 | 7,19% (6,44–8,00%) |
| 90 ngày | 4.154 | 350 | 8,43% (7,61–9,29%) |
| 180 ngày | 3.508 | 365 | 10,40% (9,35–11,40%) |

Mẫu số thay đổi theo kỳ hạn vì tháng gần cuối DEV bị loại khi chưa trưởng thành. Ma trận tháng × kỳ hạn đầy đủ ở `outputs/tables/customer_retention_dev.csv`; danh sách cohort bị loại ở `outputs/tables/customer_retention_exclusions_dev.csv`.

## Thời gian đến đơn thứ hai

Kaplan–Meier trên 3.508 khách thuộc cohort-month đủ 180 ngày ước lượng xác suất có đơn thứ hai là 6,64% tại ngày 30 (CI 5,82–7,50%), 8,24% tại ngày 60 (7,35–9,15%), 9,44% tại ngày 90 (8,49–10,38%) và 11,32% tại ngày 180 (10,35–12,32%). Median toàn cohort chưa đạt vì xác suất mua lần hai chưa chạm 50%.

Có 397 khách có đơn thứ hai trong 180 ngày nếu tính theo giao dịch, trong đó 34 khách có đơn thứ hai cùng ngày với đơn đầu. Retention ở trên yêu cầu ngày mua sau ngày đầu nên ghi nhận 365 khách; Kaplan–Meier tính giao dịch thứ hai cùng ngày là sự kiện tại ngày 0. Hai tỷ lệ dùng định nghĩa sự kiện khác nhau và được tách riêng.

Trong 397 khách có đơn thứ hai trong 180 ngày, thời gian có điều kiện P25/P50/P75 là 4/20/66 ngày; CI median 14–27 ngày. Đây là phân phối trong nhóm đã mua lần hai, không phải thời gian trung vị của toàn bộ khách.

## Tập trung doanh thu và khách mới/quay lại

Trong 5.169 khách với tổng doanh thu ghi nhận 2.547.369.341₫, top 10% (517 khách) chiếm 43,40% (CI 39,999–47,123%); top 20% (1.034 khách) chiếm 56,89% (54,27–59,77%).

Ở các tháng có ít nhất 30 khách quay lại, tỷ trọng doanh thu nhóm quay lại dao động 6,77–22,80%; CI từng tháng và nhóm dưới 30 được ẩn nằm ở `outputs/tables/customer_revenue_new_returning_monthly_dev.csv`. Đây là phân rã mô tả theo khách có đơn đầu trong DEV hay đã mua trước tháng đó; không phải tác động chiến dịch.

## Nhóm RFM có hành động

Snapshot RFM tại 2025-10-22; recent là recency ≤90 ngày, mua lặp lại là frequency ≥2, giá trị cao là doanh thu ghi nhận tích lũy ≥p90 DEV (830.000₫). Quy tắc tạo sáu nhóm không chồng lấn; nhóm, quy mô, đóng góp doanh thu và CI bootstrap ở `outputs/tables/rfm_action_segments_dev.csv`.

| Nhóm | Khách | Tỷ trọng doanh thu ghi nhận |
|---|---:|---:|
| Giá trị cao, mua lặp lại gần đây | 62 | 6,66% |
| Mua lặp lại gần đây | 120 | 2,35% |
| Mua lặp lại đã lâu | 457 | 21,63% |
| Giá trị cao, một đơn | 284 | 20,64% |
| Một đơn gần đây | 767 | 8,43% |
| Một đơn đã lâu | 3.479 | 40,29% |

Hành động là giả thuyết để thử, chưa chứng minh hiệu quả. Mỗi hành động liên hệ khách có điều kiện tiên quyết: cần có thông tin liên hệ hợp lệ và khách đồng ý nhận liên hệ; cửa hàng cần kiểm tra quy định bảo vệ dữ liệu cá nhân áp dụng. Đây là lưu ý cần kiểm tra, không phải tư vấn pháp lý. Không gán ưu đãi hay chi phí khi chưa có dữ liệu.

## CLV mô tả 180 ngày

Chỉ tính cohort-month trưởng thành đủ 180 ngày; 3.508 khách. Doanh thu ghi nhận 180 ngày đầu từ đơn đầu chia cho khách là 512.934₫/khách (CI 472.395–560.411₫). Phân rã đồng nhất: AOV 444.619₫ × 1,154 đơn/khách = 512.934₫. Đây là giá trị lịch sử mô tả, không phải dự báo CLV tương lai hay lợi nhuận.

Theo nhóm RFM cuối DEV, `Một đơn gần đây` có dưới 30 khách đủ theo dõi CLV nên số đã ẩn. Các nhóm còn lại và CI ở `outputs/tables/clv_180d_dev.csv`.

## K-Means và ngoại lai

Silhouette có sẵn: K=2 là 0,508; K=3/4/5 lần lượt 0,390/0,385/0,392. Bootstrap 100 lần cho ARI median 0,995/0,985/0,953/0,957 theo K=2/3/4/5. So sánh Ward trên cùng mẫu cố định 2.000 khách cho ARI K-Means–Ward 0,988/0,766/0,798/0,792. K=2 tách hình học ổn định hơn; độ ổn định hình học không xác nhận ý nghĩa kinh doanh hay tính hành động. Không thay kết quả K-Means đã khóa.

Proxy p99 hiện có bắt 62/5.169 khách (1,20%; p99 Monetary 3.439.576₫ hoặc max order 3.082.176₫). Tukey upper fence trên log1p(Monetary) và log1p(max order) bắt 169 khách (3,27%); giao với proxy là 62 khách, Jaccard 0,367. Đây là cờ ngoại lai mô tả, không phải loại khách/rủi ro.

## Giới hạn

Chỉ một cửa hàng và một DEV window; các cohort có mức trưởng thành khác nhau, giá trị giao dịch không có giá vốn, và không có chi phí liên hệ/ưu đãi hay lịch sử chiến dịch. Không suy ra nhân quả, lợi nhuận hoặc hiệu quả. Mọi nhóm n<30 chỉ mô tả; số tiền/tỷ lệ nhóm nhỏ đã bị ẩn.

