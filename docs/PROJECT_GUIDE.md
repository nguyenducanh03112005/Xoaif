# Xoaif Garden — hướng dẫn dự án

> Tài liệu này mô tả repo hiện tại: sản phẩm, luồng dữ liệu, cài đặt/chạy, kết quả, giới hạn và quyết định còn chờ. Không cần đọc nhật ký công việc để nắm trạng thái.

## 1. Mục tiêu và sản phẩm hiện có

Dự án phân tích bán hàng Pancake POS cho một cửa hàng cây cảnh. Repo có quy trình lấy snapshot có kiểm soát, kiểm tra dữ liệu, kho DuckDB cục bộ, xử lý/khai phá dữ liệu, dashboard offline, báo cáo và tài liệu bảo vệ.

Hiện có:
- Kho fact/dimension và mẫu CSV tổng hợp minh họa schema.
- EDA, doanh thu ghi nhận, retention, thời gian đến lần mua thứ hai, Pareto/CLV mô tả, RFM, mùa vụ.
- Phân tích mua lại trên DEV và một đánh giá test đã mở đúng một lần.
- FP-Growth/association rules cho giỏ hàng.
- Dashboard Streamlit, báo cáo PDF, slide PDF, PPTX 15 trang có speaker notes và cẩm nang bảo vệ/demo.
- Kiểm soát API GET-only, allowlist, HMAC, manifest/checksum, quy tắc khóa và quét PII.

## 2. Cấu trúc repo hiện tại

| Đường dẫn | Vai trò |
|---|---|
| src/ingest | Client Pancake GET-only, HMAC, kiểm soát truy cập và snapshot. |
| src/warehouse | Nạp/tạo kho DuckDB. |
| src/features | Chuẩn hóa ngày/tiền, dòng quà, cohort, feature và giỏ hàng. |
| src/models | Phân khúc RFM, classifier và luật kết hợp. |
| src/app | Dashboard Streamlit chỉ đọc aggregate local. |
| scripts | Snapshot, ETL, phân tích, dựng artifact và kiểm tra. |
| config | Allowlist, split/protocol và hash lock. Không sửa file khóa thủ công. |
| data/sample | CSV giả lập, không phải dữ liệu cửa hàng. |
| data/raw | Raw API cục bộ, có thể chứa PII, bị ignore. |
| data/restricted | DuckDB và dữ liệu pseudonymous, bị ignore. |
| outputs/tables, outputs/metrics | Aggregate, metric và đầu vào dashboard. |
| report, slides | PDF báo cáo và tài liệu thuyết trình. |
| docs | Hướng dẫn dự án, bảo vệ, quy tắc và bằng chứng kỹ thuật. |

Không chia sẻ data/raw, data/restricted, xoaif.env, khóa HMAC, model .joblib hoặc bảng từng khách/đơn.

## 3. Công nghệ

Python 3.11+, requests, python-dotenv, DuckDB, Pandas, NumPy, scikit-learn, mlxtend, Matplotlib/Seaborn, ReportLab, Streamlit, Plotly, PyYAML, Jupyter/nbconvert và pytest. Dependency nằm trong pyproject.toml, requirements.txt.

## 4. Dữ liệu đi qua đâu

Nguồn chính là Pancake POS Open API. Client chỉ gọi GET theo endpoint allowlist. Snapshot đang phân tích: 20261024T052943Z, 12.011 đơn trên 601 trang. API cho trạng thái hiện tại, không có lịch sử trạng thái đầy đủ để dựng mọi trạng thái quá khứ.

DEV dùng giờ Asia/Ho_Chi_Minh, từ 2024-04-01 đến trước 2025-10-22: 6.517 đơn, gồm 6.400 đơn status 3. Các đơn bán thử năm 2022 nằm ngoài phạm vi phân tích. Chủ cửa hàng xác nhận status 3 là đơn doanh thu được ghi nhận; đây không phải đối soát ngân hàng.

Luồng:
1. scripts/snapshot_orders.py phân trang qua API và lưu raw cùng manifest SHA-256 trong data/raw.
2. Loader kiểm tra schema/allowlist, khóa snapshot, chuẩn hóa ngày và thay định danh bằng HMAC-SHA-256.
3. Dữ liệu cần cho phân tích được nạp vào data/restricted/xoaif_dev.duckdb. Kho có fact đơn, fact dòng hàng và dimension khách/ngày/trạng thái/sản phẩm; đây không phải bản sao đầy đủ raw.
4. Từ kho tạo cohort, RFM, giỏ, nhãn và feature DEV. Mỗi feature tại T chỉ dùng thông tin đã biết trước T. Cấu hình mua lại dùng N=180 ngày và L=7 ngày.
5. Chỉ aggregate đã rà soát được đưa vào outputs và dashboard. Dashboard không gọi API hay đọc raw/restricted.

Raw ở data/raw chỉ lưu cục bộ. Restricted ở data/restricted chứa dữ liệu HMAC liên kết lịch sử khách, nên vẫn là dữ liệu nhạy cảm. Shared outputs chỉ gồm aggregate đã qua rà soát và suppression. Mẫu data/sample được sinh giả lập cố định, chỉ minh họa cấu trúc.

Doanh thu ghi nhận dùng total_price_after_sub_discount trừ shipping_fee, với ngoại lệ không trừ ship hai lần khi tổng sau giảm bằng total_price trừ total_discount. Đây là quy tắc nghiệp vụ, không phải lợi nhuận. Đơn quà cấp đơn bị loại khỏi hành vi/doanh thu. Dòng quà ưu tiên cờ bonus, giảm 100%, rồi subset-sum chính xác; 903 dòng suy luận subset có thể sai và cần rà thủ công trước quyết định kinh doanh. Doanh thu/giảm giá ở cấp đơn nên không phân bổ xuống sản phẩm.

## 5. Kết quả chính và cách diễn giải

### EDA và giá trị khách
Retention 180 ngày theo định nghĩa có giao dịch vào ngày sau là 10,40% trên 3.508 khách đủ thời gian theo dõi (95% CI 9,35–11,40%). Doanh thu ghi nhận 180 ngày đầu là 512.934₫/khách (95% CI 472.395–560.411₫); đây là mô tả lịch sử, không phải dự báo hay lợi nhuận.

### Phân khúc
K-Means K=2 trên RFM có silhouette 0,508 và chủ yếu tách khách mua một lần với khách mua lặp lại. Trong DEV, 4.526/5.174 khách (87,5%) chỉ mua một lần. Đây là mô tả hình học/tần suất, chưa chứng minh nhóm có ý nghĩa kinh doanh. Sáu nhóm RFM theo quy tắc được dùng như giả thuyết mô tả, không phải danh sách hành động đã kiểm chứng.

### Mua lại
DEV đa mốc tạo 21.638 snapshot khách–T từ 3.508 khách; OOF có 14.394 snapshot, 600 nhãn dương (4,17%). Baseline đơn giản và mô hình đầy đủ không cho thấy mô hình phức tạp vượt ổn định. WP5b: AP pooled frequency rule 0,0659; cây nông 0,0745; LR v3 0,0641. CI chồng lấp và chiến lược không đạt tiêu chí decile đơn điệu, nên chưa chọn mô hình triển khai.

Test mở một lần có 5.169 khách, 237 dương (4,59%). LR C=10 có ROC-AUC 0,7024, AP 0,123. DEV OOF của mô hình chính có ROC-AUC 0,5096, gần ngẫu nhiên. Vì DEV chưa xác nhận tín hiệu, điểm test chỉ là tín hiệu yếu, không dùng để chỉnh mô hình. Cấu hình ghi >T nhưng evaluator chạy [T,end), gồm ngày T; ảnh hưởng chưa xác định. Test cũ không được chạy lại.

### Giỏ hàng
FP-Growth mô tả sản phẩm đồng xuất hiện. Trong 24 cặp đã khóa, 21 có lift>1 ở test, nhưng đó là bằng chứng yếu. Bộ lọc DEV F3 dùng lift>1, Kulczynski≥0,5 và imbalance ratio≤0,5; chỉ 1/24 cặp qua. Combo chỉ là giả thuyết A/B. Chưa có giá vốn nên không tính margin/hoà vốn.

### Phản hồi
Chưa có nguồn phản hồi đủ số lượng và nhãn để huấn luyện/đánh giá phân loại. Không có kết quả không có nghĩa là khách không gặp vấn đề.

## 6. Cài đặt và chạy

PowerShell từ thư mục gốc:

~~~powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[analysis,dashboard,dev]"
~~~

Dashboard offline:

~~~powershell
.venv\Scripts\streamlit.exe run src/app/streamlit_app.py
~~~

Tạo lại dữ liệu mẫu tổng hợp:

~~~powershell
.venv\Scripts\python.exe scripts/make_sample_data.py
~~~

Hậu kiểm an toàn trên repo hiện tại:

~~~powershell
.venv\Scripts\python.exe scripts/run_all.py
~~~

Do holdout đã mở, runner chỉ xác minh split/locks, GET-only, pytest, PII và dashboard aggregate. Runner không chạy evaluator, notebook, model selection hoặc refit. Clone không có raw/DuckDB chỉ xác minh phần artifact đã ship.

Full ingestion chỉ trên máy được cấp quyền API, có xoaif.env cục bộ và sau khi đọc docs/api_notes.md cùng docs/refresh_procedure.md. Không chạy live refresh chỉ để xem dashboard. Snapshot mới không thay đổi kết quả test khóa hiện tại; phân tích mới cần protocol/amendment.

## 7. Việc còn mở và đầu vào cần chủ dự án

| Việc | Cần chủ dự án cung cấp/chốt | Xử lý sau khi có đầu vào |
|---|---|---|
| Giá vốn | Export giá vốn có thời gian hiệu lực; xác nhận trường giá nhập có đúng giá mua không. | Lưu bảng restricted theo HMAC product key, audit giá 0/giá vốn cao hơn giá bán, rồi tính margin và hòa vốn. |
| Bài toán C | Nguồn review/ghi chú được phép, quyền dùng, nội dung đã ẩn danh và người gán nhãn. | Đếm coverage; nếu đủ thì thống nhất taxonomy, gán nhãn tay, đo đồng thuận và đánh giá tập giữ riêng. |
| Phân khúc | Chọn mục tiêu kinh doanh, ngân sách và người phê duyệt. | Đánh giá nhóm theo outcome DEV/CI, sau đó mới đề xuất thử nghiệm. |
| Combo | Giá vốn, tồn kho, mức giảm, ngân sách, KPI và cỡ mẫu A/B. | Chọn ít giả thuyết, tính hòa vốn từ margin thực, đăng ký thử nghiệm trước khi chạy. |
| Mô hình mua lại mới | Câu hỏi kinh doanh, ngân sách top-k và cách dùng score. | Amendment mới với rolling-origin DEV và baseline. Không dùng test cũ để chọn. |
| Quyền riêng tư | Người truy cập, hạn lưu raw/restricted, ngày xóa sau bảo vệ. | Ghi quyết định và biên bản xóa/giữ. |
| Nộp học phần | Rubric, thời lượng, số người trình bày, format chính thức. | Rút gọn deck/demo theo yêu cầu. |

## 8. Tài liệu chính

- Cẩm nang bảo vệ: DEFENSE_GUIDE.md.
- Hệ thống số liệu chuẩn: canonical_numbers.md.
- Protocol thời gian và split: data_protocol.md.
- Định nghĩa dữ liệu và governance: data_dictionary.md, data_governance.md.
- Kết quả mua lại, cohort, retention và combo: cohort_mismatch_analysis.md, customer_value_dev.md, combo_recommendation_f3.md, test_report.md.
- Danh mục artifact kỹ thuật: submission_artifacts.md và INDEX.md.
