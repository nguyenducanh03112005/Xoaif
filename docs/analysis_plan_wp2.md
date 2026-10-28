# Đăng ký trước A1 — giữ chân và giá trị khách hàng DEV

- **Trạng thái:** đăng ký trước; 2026-10-28. Không sửa kế hoạch sau khi đã xem kết quả mới.
- **Phạm vi:** DEV `[2024-04-01, 2025-10-22)`, chỉ đơn status 3, loại quà theo quy tắc đã khóa. Khám phá, chưa xác nhận ngoài mẫu. Không dùng test records/labels/behavior.
- **Nguồn:** `load_dev_orders()` với date gate hiện có; customer feature snapshot pre-T; không ghi mã khách/đơn vào đầu ra.
- **Seed/CI:** seed `20261028`; percentile bootstrap 2.000 lần theo khách cho retention rates, Pareto shares, doanh thu và CLV. Một khách là đơn vị resampling.

## Câu hỏi và định nghĩa khóa

1. **Retention theo tháng mua đầu:** cohort là tháng của lần mua hợp lệ đầu tiên trong DEV. Retention H là tỷ lệ khách có ít nhất một lần mua hợp lệ khác trong `(first_purchase_date, first_purchase_date+H]`. Với mỗi H∈{30,60,90,180}, chỉ tính trọn các cohort-month có `month_end + H < dev_end` (`dev_end=2025-10-22`). Các tháng còn lại ghi riêng là bị loại vì kiểm duyệt phải; không suy ra tỷ lệ cho cohort chưa trưởng thành. Tạo ma trận tháng × H, chỉ điền ô có đủ theo dõi.
2. **Thời gian đến đơn thứ hai:** cùng định nghĩa lần mua hợp lệ; dùng cohort-month trưởng thành đủ 180 ngày. Theo dõi đến ngày 180; khách chưa mua lần hai được kiểm duyệt phải tại ngày 180. Báo đường sống sót Kaplan–Meier và tỷ lệ tích lũy tại 30/60/90/180; median thời gian đến đơn thứ hai nếu đường sống sót chạm 0,5; P25/P50/P75 thời gian trong nhóm đã mua lần hai được dán rõ là thống kê có điều kiện. Kaplan–Meier là mở rộng ngoài phần mục lục đã đối chiếu; giải thích ngắn trong báo cáo.
3. **Pareto doanh thu:** doanh thu ghi nhận DEV theo khách; xếp hạng giảm dần; báo tỷ trọng của top 10% và top 20% khách, mẫu số là toàn bộ doanh thu hợp lệ DEV. Bootstrap theo khách, mỗi draw tính lại thứ hạng.
4. **Khách mới/quay lại theo tháng:** “mới” là tháng có đơn hợp lệ DEV đầu tiên; “quay lại” là khách có đơn hợp lệ trước tháng đó trong DEV. Báo số đơn, doanh thu ghi nhận và tỷ trọng theo tháng. Không gán doanh thu vào nhân quả của chiến dịch.
5. **CLV mô tả 180 ngày:** trên cohort-month trưởng thành 180 ngày, doanh thu ghi nhận trong 180 ngày đầu từ lần mua đầu chia cho số khách trong cohort. Phân rã đồng nhất thành AOV × đơn bình quân/khách. Báo tổng thể và theo nhóm RFM cuối DEV; diễn giải là mô tả lịch sử, không phải giá trị tương lai/lợi nhuận.
6. **RFM hành động:** snapshot tại `T=2025-10-22`, dùng R=ngày từ lần mua hợp lệ cuối, F=số đơn hợp lệ, M=tổng doanh thu ghi nhận DEV. Ngưỡng cố định: recent R≤90 ngày; repeat F≥2; high-M M≥p90 Monetary DEV. Tạo sáu nhóm không chồng lấn theo thứ tự ưu tiên: (1) high-M, repeat, recent; (2) repeat, recent còn lại; (3) repeat, lapsed (R>90); (4) F=1, high-M; (5) F=1, R≤90; (6) F=1, R>90. Nhóm có n<30 chỉ mô tả; aggregate công bố sẽ gộp/ẩn dưới ngưỡng theo suppression hiện hành. Hành động chỉ là đề xuất; điều kiện tiên quyết là có thông tin liên hệ hợp lệ và khách đã đồng ý nhận liên hệ, cần cửa hàng kiểm tra quy định áp dụng.
7. **Phân cụm và outlier:** giữ nguyên kết quả K-Means đã khóa; chỉ đánh giá bổ sung trên feature snapshot DEV tại T. Cố định K={2,3,4,5}, ma trận `[R, log1p(F), log1p(max(M,0))]`, z-standardization; dùng silhouette đã có cho xu hướng. Độ ổn định K-Means: 100 bootstrap customer resamples, seed gốc 20261028 cộng chỉ số draw; fit scaler và K-Means trên resample rồi dự đoán toàn snapshot; báo phân phối ARI so với nhãn fit full DEV. So sánh full-snapshot K-Means với Ward hierarchical bằng ARI cùng K; không chọn lại K. Outlier bổ sung: Tukey upper fence trên `log1p(M)` và `log1p(max_order_value)`, rồi so quy mô/giao nhau với proxy p99 hiện hành; không gán nhãn khách cụ thể.

## Số phép so sánh và nguyên tắc báo cáo

- Không kiểm định giả thuyết hoặc chọn kết quả đẹp. Công bố mọi horizon, mọi cohort-month đủ trưởng thành, top 10/20, sáu nhóm RFM, K=2/3/4/5, toàn bộ 100 bootstrap ARI mỗi K dưới dạng tóm tắt phân phối, và từng outlier rule đã nêu.
- Mọi số có cohort, đơn vị, n, nguồn script và CI nếu là ước lượng chính. Mẫu n<30 chỉ mô tả; đầu ra aggregate không lộ ô nhỏ.
- Không có giá vốn/chi phí/liên hệ/chiến dịch cũ: không kết luận lợi nhuận, uplift nhân quả hay hiệu quả chiến dịch. Câu hành động phải gắn điều kiện tiên quyết về liên hệ và sự đồng ý.
- K-Means, ngưỡng business rules, quy tắc tiền, khóa split và mô hình chính không đổi. Không mở HO2.
