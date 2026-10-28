# Xoaif Garden — bảo vệ, hỏi đáp và demo

## Luận điểm chính

Dự án đã tạo một quy trình phân tích bán hàng có kiểm soát dữ liệu cùng dashboard và các kết quả mô tả. Mô hình mua lại chưa ổn định trong development; test một lần cho kết quả cao hơn nhưng không được dùng để điều chỉnh. Luật kết hợp chỉ mô tả đồng xuất hiện. Chưa kết luận nhân quả, lợi nhuận hay hiệu quả chiến dịch.

## Thuyết trình 12–15 phút

1. Mục tiêu: mô tả khách, khả năng xếp hạng mua lại, sản phẩm thường chung giỏ và nguồn phản hồi.
2. Nguồn và quy mô: Pancake POS, snapshot 12.011 đơn; DEV 6.517 đơn, gồm 6.400 status 3. Đơn và khách là hai đơn vị khác nhau.
3. Kiến trúc năm tầng: API, snapshot/manifest, kiểm soát/HMAC, DuckDB/feature/analysis, aggregate/dashboard/report.
4. Nghiệp vụ: mốc cửa hàng 2024-04-01, DEV kết thúc trước 2025-10-22, status 3, doanh thu ghi nhận, xử lý quà.
5. EDA và giá trị: retention, thời gian mua lần hai, Pareto/CLV. Tiền là doanh thu ghi nhận.
6. Phân khúc: K-Means K=2 chủ yếu tách mua một lần/lặp lại; không gán VIP/churn.
7. Mua lại: DEV đa mốc, baseline, metric lớp hiếm; chưa có mô hình thắng ổn định.
8. Test: đã mở một lần; chênh lệch DEV/test chưa giải thích; nêu sai khác >T và [T,end).
9. Combo: FP-Growth mô tả đồng xuất hiện; chưa có giá vốn hoặc thử nghiệm.
10. Dashboard: aggregate local, 5 tab, không cần API.
11. Hạn chế và đầu vào cần quyết định: giá vốn, nhãn C, mục tiêu hành động, retention raw và rubric.
12. Kết luận: quy trình/dashboard làm được; khuyến nghị kinh doanh cần kiểm chứng.

Rút còn 8 phút bằng cách gộp slide 2–4, 5–6, 7–9; demo tối đa 90 giây.

### Chia phần nếu có hai người trình bày

- Người A: slide 1–6 — mục tiêu, dữ liệu, kiến trúc, quy tắc nghiệp vụ và kết quả mô tả.
- Người B: slide 7–15 — mô hình, đánh giá, combo, dashboard, quyết định còn mở và kết luận.
- Demo do một người thao tác; người còn lại trả lời câu hỏi về dữ liệu hoặc phương pháp. Nếu chỉ có một người, dùng thứ tự slide như trên.

## Kịch bản demo offline (4 phút)

Chuẩn bị: mở terminal ở repo, dùng dashboard local. Không mở raw/restricted hoặc file khách từng dòng.

- 0:00–0:40 Tổng quan doanh số: lọc khoảng tháng, đọc doanh thu ghi nhận và số đơn. Nhắc 2026-04 chưa trọn.
- 0:40–1:25 Phân khúc: xem K=2 và sáu nhóm rule-based; đây là mô tả, chưa kiểm chứng tác động.
- 1:25–2:05 Combo: xem thước đo; chỉ 1/24 cặp qua bộ lọc DEV F3. Không nói combo làm tăng doanh thu.
- 2:05–2:45 Chất lượng: xem định nghĩa tiền và dòng quà. Suy luận subset có thể sai.
- 2:45–3:35 Mô hình: đặt DEV gần 0,51 cạnh test khoảng 0,70; test không được dùng chỉnh mô hình và khác biệt chưa giải thích.
- 3:35–4:00 Chốt: dashboard chỉ đọc aggregate; còn thiếu giá vốn và phản hồi có nhãn.

Lệnh mở dashboard:
~~~powershell
.venv\Scripts\streamlit.exe run src/app/streamlit_app.py
~~~

Nếu dashboard lỗi, dùng slides/Xoaif_Final.pptx hoặc slides/xoaif_print.pdf làm phương án trình bày.

## Hỏi đáp giảng viên

**Mục tiêu dự án?** Xây luồng tái lập từ dữ liệu bán hàng đến kho, phân tích và dashboard; trả lời câu hỏi phân khúc/mua lại, giỏ hàng và khả năng phân loại phản hồi.

**Vì sao DuckDB thay Spark?** Quy mô 12 nghìn đơn phù hợp phân tích trên một máy. DuckDB đủ cho ETL/SQL, nhẹ hơn cụm Spark.

**Dữ liệu đi qua đâu?** Pancake API, snapshot có manifest, kiểm tra/ẩn danh HMAC, DuckDB/Pandas/features, mô hình/luật, aggregate cho dashboard/PDF.

**Snapshot 12.011 có nghĩa mọi đơn được dùng không?** Không. DEV là 6.517 đơn trong [2024-04-01, 2025-10-22); cohort mỗi phân tích còn điều kiện riêng.

**Sample có phải dữ liệu cửa hàng?** Không. CSV được sinh giả lập với seed cố định để minh họa schema.

**Vì sao status 3 là doanh thu ghi nhận?** Chủ cửa hàng xác nhận status 3 là đơn đã nhận/ghi nhận, gồm đơn tại quầy. Đây không phải đối soát ngân hàng.

**Công thức có phải lợi nhuận?** Không. Đây là doanh thu ghi nhận theo quy tắc nghiệp vụ; không có giá vốn/chi phí và không phân bổ điều chỉnh cấp đơn xuống sản phẩm.

**HMAC có ẩn danh tuyệt đối không?** Không. Đây là mã giả danh ổn định, vẫn nhạy cảm vì liên kết lịch sử khách.

**API và dashboard có an toàn?** Client chỉ cho phép GET/allowlist. Dashboard chỉ đọc aggregate local, không gọi API và không mở raw/restricted.

**K=2 nói gì?** Chủ yếu tách mua một lần và mua lặp lại. Silhouette 0,508 là khoảng cách hình học, không chứng minh giá trị kinh doanh.

**Có gọi nhóm là VIP/churn risk không?** Chưa. Chưa có định nghĩa và outcome/chiến dịch xác nhận. Dùng nhãn mô tả RFM.

**Vì sao không chọn AUC test ~0,70?** Mô hình chính có DEV OOF ROC-AUC 0,5096, gần ngẫu nhiên. Test đã mở, chênh lệch chưa giải thích và không được dùng tinh chỉnh.

**Vì sao DEV/test khác?** Cấu trúc cohort và prevalence khác nhau. Mẫu DEV cũ có 7,41% dương, OOF đa mốc 4,17%, test 4,59%. Đây là khác biệt mô tả, chưa xác định nguyên nhân AUC.

**Test mở bao nhiêu lần?** Một lần theo lock/access log. Không chạy evaluator lại và không dùng test để chọn mô hình/ngưỡng.

**Sai khác ngày T?** Cấu hình ghi nhãn ngày sau T, evaluator thực tế dùng [T,end), gồm ngày T. Ảnh hưởng chưa xác định; phải công khai.

**Vì sao không dùng accuracy?** Lớp dương hiếm; accuracy có thể cao khi đoán toàn âm. Đọc AP/ROC-AUC cùng precision, recall, confusion matrix và baseline.

**Mô hình có triển khai score cho khách thật chưa?** Chưa. DEV không xác nhận xếp hạng ổn định, calibration yếu, chưa có ngân sách top-k/chiến dịch.

**Lift>1 có nghĩa combo tốt?** Không. Chỉ là đồng xuất hiện. F3 chỉ 1/24 cặp qua lọc DEV; cần margin, tồn kho và A/B test.

**Vì sao chưa có giá vốn?** Chưa có bảng giá vốn theo thời gian và chưa xác minh trường imported price là giá mua thực. Cần export và xác nhận từ chủ cửa hàng.

**Bài toán C có kết quả gì?** Chưa đủ nguồn phản hồi có nhãn để huấn luyện/đánh giá. Không đồng nghĩa khách không có vấn đề.

**Người chấm chạy được gì trên clone?** Cài dependency, mở dashboard outputs, sinh sample và chạy hậu kiểm. Clone không có raw/DuckDB nên không thể tái tạo toàn pipeline API.

**run_all có fit lại không?** Sau khi test lock tồn tại, runner chỉ hậu kiểm; không gọi evaluator, notebook/model selection/refit.

**Cần quyết định gì tiếp?** Export giá vốn, nguồn/quyền dùng phản hồi, nhãn và người gán, mục tiêu/ngân sách top-k, hạn lưu/xóa raw, rubric/thời lượng. Cách xử lý nằm trong PROJECT_GUIDE mục 7.

## Câu kết 30 giây

“Dự án đã hoàn thiện luồng dữ liệu cục bộ an toàn, dashboard và phân tích mô tả. Retention và các mẫu giỏ giúp hình thành giả thuyết. Mô hình mua lại chưa được development xác nhận, combo chưa có chứng cứ nhân quả hay giá vốn, và bài toán phản hồi thiếu nhãn. Bước tiếp theo là lấy dữ liệu giá vốn/phản hồi có quyền sử dụng và kiểm chứng hành động bằng thử nghiệm phù hợp.”
