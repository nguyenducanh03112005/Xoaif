# Kế hoạch cuối cùng: Phân tích và khai phá dữ liệu bán hàng Xoaif Garden

**Phiên bản:** 2.0 · **Ngày tổng hợp:** 24/10/2026  
**Cơ sở:** mục tiêu ban đầu của người dùng và giảng viên; kế hoạch v1.6; các điểm P1/P2 đã thống nhất sau kiểm duyệt.  
**Trạng thái:** đang triển khai Giai đoạn 0–2; các quyết định phân tích và đánh giá chờ CP1. Tài liệu này chưa chứa kết quả phân tích kinh doanh.

## 1. Mục tiêu và phạm vi

Xây dựng quy trình phân tích dữ liệu bán hàng từ Pancake POS, có thể chạy lại trên máy cá nhân, trình bày kiến trúc năm tầng và trả lời ba câu hỏi kinh doanh. Mọi kết luận phải dựa trên dữ liệu thực tế; nếu dữ liệu không đủ, báo rõ giới hạn hoặc bỏ nhánh phân tích thay vì tạo kết quả yếu.

### 1.1 Ba bài toán

| Bài toán | Câu hỏi và cách phát biểu có thể kiểm chứng | Đầu vào | Đầu ra và đánh giá |
| --- | --- | --- | --- |
| A. Phân khúc và dự đoán khách quay lại | Hành vi mua của khách hiện có khác nhau thế nào? Với lịch sử trước mốc T, mô hình có dự đoán được khách có một đơn mua lại hợp lệ trong N ngày tiếp theo không? | Đơn hàng, dòng hàng và thuộc tính chỉ được phép dùng nếu đã biết tại T | Bắt buộc: phân khúc RFM mô tả bằng K-Means, tên cụm đặt sau khi xem kết quả. Nếu đủ dữ liệu: mô hình quay lại, so với baseline; Precision, Recall, F1, PR-AUC/ROC-AUC và khoảng bất định. Không gọi cụm là “VIP”, “trung thành” hay “nguy cơ rời bỏ” nếu chưa có định nghĩa và bằng chứng phù hợp. |
| B. Sản phẩm thường được mua cùng | Những sản phẩm hoặc nhóm sản phẩm nào đồng xuất hiện trong giỏ hàng hợp lệ? | Giỏ hàng theo quy tắc đơn và dòng hàng đã duyệt | Bắt buộc: luật kết hợp cùng support, confidence, lift và số lần xuất hiện. Nếu đủ dữ liệu: tối đa 10 combo giả thuyết. Luật kết hợp không chứng minh combo làm tăng doanh thu; mức giá/lợi nhuận chỉ đề xuất khi có giá vốn, tồn kho và giả định giảm giá được xác nhận. |
| C. Vấn đề sản phẩm và dịch vụ | Nội dung phản hồi đề cập vấn đề nào, mức độ thường gặp ra sao, và nhóm nào có hành động khắc phục khả thi? | Đánh giá, ghi chú đơn, lý do huỷ/hoàn hoặc hội thoại nếu API cung cấp và được phép sử dụng | Nếu đủ dữ liệu: phân loại văn bản tiếng Việt, đánh giá Precision/Recall/F1 từng nhóm trên tập gán nhãn tay, tổng hợp vấn đề và hành động. Nếu ít văn bản hoặc nhãn không đáng tin, chỉ mô tả nguồn dữ liệu hoặc bỏ nhánh. |

### 1.2 Mức ưu tiên đầu ra

- **Bắt buộc theo mục tiêu ban đầu:** khảo sát dữ liệu/API; ETL và snapshot có thể tái lập; từ điển dữ liệu và kiểm tra chất lượng; kho DuckDB; EDA; phân khúc RFM mô tả; luật kết hợp; báo cáo PDF; sơ đồ kiến trúc năm tầng; dashboard Streamlit bản demo; PPTX và Q&A; đối chiếu với cấu trúc đề mẫu. Dashboard chỉ hiện các kết quả thực có, không tạo tab/kết quả giả.
- **Chỉ nếu đủ dữ liệu:** mô hình quay lại và phân tích văn bản. Không có đủ dữ liệu thì báo rõ trong PDF/PPTX/Q&A và vẫn hoàn thành các đầu ra học thuật bằng phần mô tả có căn cứ.
- **Tuỳ chọn:** Olist để minh hoạ/kiểm chứng quy trình; DBSCAN chỉ khi có toạ độ địa lý thật; video demo dự phòng.

## 2. Đối chiếu mục tiêu ban đầu với kế hoạch cuối

| Mục tiêu ban đầu | Quyết định trong kế hoạch cuối | Lý do/giới hạn |
| --- | --- | --- |
| Kiến trúc năm tầng, nêu công cụ, vai trò, chức năng và tác dụng | Giữ nguyên và trình bày trong mục 3 | Đây là yêu cầu giảng viên trực tiếp, phải xuất hiện trong báo cáo và slide. |
| A có phân khúc khách với tên như VIP/trung thành/nguy cơ rời bỏ | Giữ K-Means/RFM; tên cụm mô tả số liệu. “Quay lại” được dự đoán riêng nếu dữ liệu theo thời gian đủ tốt. | Không ép tên cụm theo mong muốn kinh doanh; không suy ra nguy cơ rời bỏ chỉ từ cụm RFM. |
| B tạo 5–10 combo, có lift và mức giảm; so sánh doanh thu giả định | Giữ luật và combo như giả thuyết. Không trình bày tăng doanh thu dự báo nếu chưa có thử nghiệm; giá và biên lợi nhuận cần dữ liệu chi phí/tồn kho. | Đồng xuất hiện không chứng minh quan hệ nhân quả hay mức giá tối ưu. |
| C phân loại phản hồi và đưa ra việc cần làm | Giữ nhánh có điều kiện; thêm tập nhãn chuẩn do người gán, đánh giá theo từng lớp và duyệt ví dụ trước khi trích dẫn. | Độ hợp lệ JSON hoặc độ tự tin của LLM không thay cho đánh giá chất lượng nhãn. |
| Olist là nguồn dự phòng để “đủ dữ liệu cho mô hình” | Chỉ dùng Olist tách riêng để minh hoạ hoặc kiểm chứng phương pháp; không gộp vào dữ liệu Xoaif và không dùng để kết luận về Xoaif. | Olist khác ngành hàng/thị trường/ngôn ngữ và không làm dữ liệu cửa hàng Xoaif đại diện hơn. |
| Dùng test theo thời gian để tránh nhìn trước tương lai | Giữ và siết: snapshot đóng băng trước khi chọn cửa sổ; W tính theo ngày; EDA phát triển dừng trước test_start; nhãn test chỉ nạp một lần sau khi khoá mô hình/ngưỡng. | Khắc phục ba điểm P1 của v1.6. |
| Tái lập và bảo vệ dữ liệu khách | Giữ allowlist, HMAC, vùng restricted/shared, run manifest và chính sách giữ/xoá. Gom quy tắc split vào một tài liệu chuẩn duy nhất. | Giảm lặp quy định và nguy cơ các bước áp dụng khác nhau. |

## 3. Kiến trúc tổng quan năm tầng

~~~mermaid
flowchart TB
  A["1. Nguồn dữ liệu<br/>Pancake POS · Olist tách riêng"]
  B["2. Thu thập và lưu trữ<br/>Python requests · raw snapshot · DuckDB"]
  C["3. Xử lý<br/>Pandas · EDA · làm sạch · đặc trưng · pipeline"]
  D["4. Khai phá<br/>K-Means · mô hình quay lại · Apriori/FP-Growth · văn bản"]
  E["5. Đầu ra<br/>Streamlit · PDF · PPTX · Q&A"]
  A --> B --> C --> D --> E
~~~

| Tầng | Công cụ | Vai trò | Chức năng cụ thể | Tác dụng |
| --- | --- | --- | --- | --- |
| 1. Nguồn | Pancake POS API | Nguồn chính, dữ liệu thật của cửa hàng | Đơn, dòng hàng, khách, sản phẩm, trạng thái và phản hồi nếu endpoint/thẩm quyền thực tế hỗ trợ | Phản ánh hoạt động Xoaif; chỉ dùng các thực thể đã xác minh được. |
| 1. Nguồn phụ | Olist/Kaggle | Dữ liệu phương pháp, không phải dữ liệu Xoaif | Chạy minh hoạ riêng cho giỏ hàng, nhãn thời gian hoặc review khi CP1 duyệt | Cho thấy phương pháp có thể vận hành; không bù mẫu và không gộp kết luận với Xoaif. |
| 2. Thu thập/lưu trữ | Python, requests, dotenv | ETL có kiểm soát | Phân trang, retry/backoff, timeout, che URL/key, full load và upsert | Tự động hoá, truy vết và chạy lại. |
| 2. Thu thập/lưu trữ | raw snapshot, DuckDB | Lưu bản nguồn và kho phân tích | Lưu raw cục bộ; tạo fact/dimension; phân tách restricted và shared | Bảo toàn nguồn để kiểm tra, đồng thời giới hạn dữ liệu nhạy cảm. |
| 3. Xử lý | Pandas, Matplotlib/Seaborn | EDA và kiểm tra dữ liệu | Thiếu, phân phối, ngoại lai, biến phân loại, xu hướng và chất lượng | Phát hiện giới hạn trước khi chọn mô hình. |
| 3. Xử lý | Scikit-learn Pipeline | Tiền xử lý và chia tập | Impute/mã hoá/chuẩn hoá trong pipeline; fit trên train; chia theo thời gian | Giảm rò rỉ trong tiền xử lý và đánh giá. |
| 3. Xử lý | Feature engineering | Tạo biến phân tích | RFM, giá trị đơn, khoảng cách mua, giỏ hàng và nhãn theo mốc T | Tạo đầu vào sát câu hỏi kinh doanh, có kiểm soát thời điểm biết dữ liệu. |
| 4. Khai phá | K-Means, Logistic Regression, Decision Tree, Random Forest | Phân khúc và dự đoán quay lại | Tạo cụm RFM; so sánh mô hình dự đoán khi đủ lịch sử | Hỗ trợ mô tả nhóm và ưu tiên thử nghiệm chăm sóc, không tự khẳng định tác động. |
| 4. Khai phá | Apriori/FP-Growth, mlxtend | Luật kết hợp | Tính support, confidence, lift, leverage | Tìm quan hệ đồng xuất hiện để hình thành giả thuyết combo. |
| 4. Khai phá | LLM hoặc mô hình cục bộ | Phân loại văn bản | Gán nhóm vấn đề/sắc thái; kiểm tra đầu ra; đánh giá với nhãn tay | Chuyển phản hồi thành bảng vấn đề có giới hạn và có thể kiểm chứng. |
| 5. Đầu ra | Streamlit | Giao diện demo | Tab tổng quan, phân khúc/dự đoán, combo, vấn đề; chỉ đọc dữ liệu shared | Trình bày trực quan, không mở kho từng khách. |
| 5. Đầu ra | PDF, PPTX, Q&A | Sản phẩm học thuật | Báo cáo theo đề mẫu, slide in được, câu hỏi đáp có trỏ số liệu | Trình bày phương pháp, kết quả, giới hạn và đáp ứng rubric. |

## 4. Nguyên tắc dữ liệu, quyền riêng tư và tái lập

### 4.1 Phân vùng lưu trữ

- **data/raw/**: bản API gốc có thể chứa PII; chỉ lưu cục bộ, không commit/không chia sẻ; quyền truy cập, thời hạn và cách xoá ghi trong chính sách dữ liệu.
- **data/restricted/**: kho DuckDB đầy đủ, pseudonymous customer IDs, lịch sử trạng thái, bảng đặc trưng/nhãn, dữ liệu văn bản sạch, nhãn tay và danh sách hành động. Không commit và không đưa lên dashboard/báo cáo.
- **data/shared/** và **outputs/**: chỉ bảng tổng hợp cần cho báo cáo/dashboard. Không có mã khách/đơn, văn bản từng bản ghi hay trường cho phép tái nhận dạng.
- Chỉ xuất restricted sang shared qua một module kiểm soát. Ngưỡng ẩn nhóm nhỏ và quy tắc chống suy ngược qua tổ hợp bộ lọc phải được cấu hình trước khi phát hành dashboard.

### 4.2 Bảo vệ dữ liệu

- Allowlist trường được nạp; trường mới từ API bị loại mặc định.
- HMAC-SHA-256 với khoá riêng cho mã khách; mã giả danh vẫn là dữ liệu nhạy cảm, không gọi là ẩn danh hoàn toàn.
- Che API key/URL trong log và lỗi; dùng quyền API thấp nhất có thể.
- Mẫu API phải được làm sạch trước khi ghi vào docs; thay mã khách/đơn/vận đơn bằng mã giả ngẫu nhiên; văn bản tự do thay bằng văn bản giả.
- Văn bản gửi nhà cung cấp LLM ngoài chỉ sau khi mô tả nhà cung cấp, loại dữ liệu, lưu giữ/huấn luyện và vị trí xử lý được người dùng duyệt. Nếu không, dùng mô hình cục bộ hoặc bỏ bước.
- Sau khi xoá raw có PII, vẫn giữ snapshot đã xử lý cần thiết để tái lập theo chính sách lưu trữ đã duyệt.

### 4.3 Nguồn sự thật duy nhất cho quy tắc thời gian/test

Tạo docs/data_protocol.md làm nguồn chuẩn duy nhất cho: định nghĩa DATA_CUTOFF, timezone, N/L/W, DEV_CUTOFF, eligibility, label, feature-as-of, ranh giới train/validation/test, cách ghi access_log và điều kiện mở test. Các notebook và tài liệu khác tham chiếu file này, không chép lại công thức.

- Chuẩn hoá timestamp về **Asia/Ho_Chi_Minh** để trình bày và so sánh; giữ UTC gốc nếu API trả UTC. Ghi rõ quy tắc chuyển múi giờ.
- Tính toán split theo ngày lịch địa phương. DATA_CUTOFF là ranh giới đầu ngày sau ngày cuối cùng có trong snapshot; manifest lưu thêm timestamp trích xuất thực tế. Các khoảng ngày dùng dạng nửa mở [đầu, cuối), tránh nhập nhằng ngày biên.
- DATA_CUTOFF của snapshot cuối được đóng băng trước khi chọn tập ứng viên và trước CP1. Không cập nhật snapshot giữa lần chạy. Dữ liệu mới tạo một run/snapshot mới; test cũ đã mở hoặc đã đánh giá không được tái sử dụng như test độc lập.
- W luôn tính bằng **ngày lịch** và là độ dài của cửa sổ nửa mở [test_start, test_end). Nếu lịch T rời rạc, chuyển số mốc thành khoảng ngày theo lịch đã khai báo trước, không trừ trực tiếp số mốc khỏi ngày.
- Trước khi nhìn thống kê hành vi, khoá tập N_candidates, L_candidates, W và DEV_CUTOFF bằng cấu hình/hash. DEV_CUTOFF = DATA_CUTOFF − (W + max(N_candidates) + max(L_candidates)); vùng phát triển chỉ dùng ngày trước DEV_CUTOFF.
- Trước CP1, chỉ tạo nhãn phát triển khi T + N + L < DEV_CUTOFF; không dùng nhãn hoặc hành vi từ vùng dành riêng để chọn N/L hay đánh giá khả thi.
- Khoảng test sau khi CP1 chọn N/L: test_end = DATA_CUTOFF − (N + L); test_start = test_end − W. Các mốc T test nằm trong [test_start, test_end), nên mọi nhãn có label_asof không muộn hơn DATA_CUTOFF.
- EDA và các quyết định phát triển chỉ đọc ngày **trước** test_start. Dữ liệu tại T của test chỉ được tạo cho lần đánh giá cuối; không dùng để chọn N, đặc trưng, mô hình, ngưỡng hay mục tiêu kinh doanh.
- Ở vùng dành riêng chỉ cho phép đếm số mốc và số dòng đủ điều kiện theo customer_eligibility_rule, không nạp nhãn, tỷ lệ mua lại hoặc hành vi mua của test. Mọi lần truy cập được ghi log.
- Nếu API không cung cấp lịch sử trạng thái cần thiết, không dùng trạng thái hiện tại để dựng quá khứ. Chuyển sang RFM mô tả và tích luỹ lịch sử tiến cứu; chỉ mở lại nhánh có giám sát khi có dữ liệu đủ tin cậy.

### 4.4 Nhãn, đủ điều kiện và khoảng ổn định

- customer_eligibility_rule thống nhất ở khảo sát, ước lượng số mẫu, tạo nhãn và đánh giá: khách có ít nhất một đơn mua hợp lệ trước T, xét bằng thông tin có thể biết tại T. Không dùng trạng thái sau T để quyết định điều kiện đủ.
- Đơn mua lại hợp lệ được cấu hình riêng, đề xuất ban đầu: đã thu tiền; không huỷ, không xoá, không hoàn toàn bộ; đơn chỉ ở trạng thái đã nhận hàng chưa chắc đã thu tiền. Quy tắc hoàn một phần phải được duyệt.
- Nhãn dương nếu có đơn hợp lệ tạo trong (T, T+N] và trạng thái xét tại label_asof = T+N+L. Nhãn không được sửa theo trạng thái sau label_asof.
- Feature tại T chỉ dùng thông tin đã sẵn có tại T. Nếu có cả event time và observed_at thì cả hai phải không muộn hơn T.
- N_candidates và L_candidates được khoá trước khi khảo sát vùng phát triển. L chọn từ SLA/đối soát đã xác minh và phân tích các quan sát có đủ thời gian theo dõi; bản ghi chưa ổn định là censored, không tính như đã ổn định.
- Nếu độ trễ quan sát vượt max(L_candidates), hoặc không xác định được độ trễ đủ tin cậy, dừng nhánh đánh giá độc lập hiện tại. Không nới L rồi kéo vùng phát triển sang vùng đã xem; dùng snapshot tương lai hoặc đánh giá tiến cứu.

## 5. Kế hoạch triển khai và checkpoint

### Giai đoạn 0. Khởi động và giới hạn phạm vi

| Việc làm | Đầu ra/điều kiện hoàn tất |
| --- | --- |
| Xác nhận rubric, hạn nộp, thời lượng trình bày, ngôn ngữ, thành viên/phân công và cách người dùng cung cấp dữ liệu | docs/schedule.md có mốc và người phụ trách. Tạm giả định báo cáo tiếng Việt cho tới khi giảng viên yêu cầu khác. |
| Tạo môi trường Python, requirements có phiên bản, .gitignore, file env mẫu, chính sách dữ liệu và cấu trúc dự án | Chạy được môi trường sạch; không có secret/data trong git. |
| Ưu tiên test tự động cho các rủi ro có hậu quả cao: che key, allowlist, split temporal, label-as-of, ngăn xuất dữ liệu cấp khách | Bộ test nhỏ nhưng trực tiếp kiểm tra bảo mật và tính độc lập của test; tránh viết test hành chính trùng lặp. |

### Giai đoạn 1. API và cổng khả thi sớm

| Việc làm | Đầu ra/điều kiện hoàn tất |
| --- | --- |
| Đọc tài liệu và gọi thử endpoint được cấp quyền: đơn, chi tiết đơn, sản phẩm, khách, tồn kho/đánh giá nếu có; xác minh phân trang, giới hạn, cập nhật, trạng thái, loại khoá và timezone | docs/api_notes.md chỉ ghi điều đã xác minh bằng tài liệu và thử nghiệm. |
| Xác minh có lịch sử trạng thái và thời điểm thu/hoàn/huỷ thật hay chỉ trạng thái hiện tại/observed_at | docs/point_in_time.md có bảng khả năng dựng lại cho mọi trường có thể đổi. Đây là cổng go/no-go cho bài toán A có giám sát. |
| Lấy mẫu phản hồi, làm sạch PII trước khi lưu; lập từ điển dữ liệu, khối lượng toàn kỳ chỉ cho kiểm kê | Không ghi bản mẫu gốc có PII vào docs. Tách kiểm kê quy mô khỏi quyết định mô hình. |
| Xác nhận có thể tạo snapshot hoàn chỉnh với dữ liệu đủ cho báo cáo và các câu hỏi | Nếu thiếu API/history, đề xuất RFM mô tả; không hứa trước có mô hình quay lại hoặc văn bản. |

### Giai đoạn 2. Snapshot và kho dữ liệu

| Việc làm | Đầu ra/điều kiện hoàn tất |
| --- | --- |
| Tải đầy đủ dữ liệu được duyệt; lưu raw snapshot có manifest và checksum; đặt DATA_CUTOFF rồi đóng băng snapshot | Có thể nạp lại đúng snapshot mà không gọi mạng. |
| Đồng bộ upsert theo ID ổn định; giữ cờ xoá mềm và order_status_log append-only từ thời điểm bắt đầu thu thập | Chạy lặp không nhân đôi; thay đổi trạng thái và xoá mềm được ghi nhận. Không tuyên bố có lịch sử trước lần thu thập đầu nếu không có. |
| Tạo star schema DuckDB: fact_orders, fact_order_items, dim_customer giả danh, dim_product, dim_date, dim_location, dim_order_status; chỉ tạo bảng nếu nguồn có dữ liệu tương ứng | Khoá, kiểu dữ liệu, phép đối soát và chất lượng có báo cáo. |
| Chuẩn hoá định nghĩa chỉ số tiền: giá trị đơn, tiền đã thu, giá trị huỷ, tiền hoàn thực tế, hàng trả/đổi; nêu thành phần gồm/không gồm và trục thời gian | Không gọi là doanh thu ròng nếu chưa đủ dữ liệu điều chỉnh. Người dùng duyệt định nghĩa ở CP1. |

### Giai đoạn 3. Khoá thiết kế và CP1

Trước mọi thống kê hành vi: chốt N_candidates, L_candidates, W theo ngày và DEV_CUTOFF; lưu cấu hình/hash. Tạo vùng phát triển đủ để dựng các lát cắt thời gian; nếu cửa sổ dự trữ làm vùng phát triển quá nhỏ thì bỏ sớm nhánh có giám sát thay vì giảm test sau khi đã nhìn dữ liệu.

**CP1 — duyệt khả thi và thiết kế (sau khi snapshot đã đóng băng):**

- Báo số liệu A/B/C theo đúng vùng dữ liệu; nêu rõ mốc thời gian, khả năng dựng trạng thái, tỷ lệ thiếu và giới hạn.
- Với mô hình quay lại, báo số mốc phát triển, số lớp theo mốc, số khách duy nhất, khả năng tạo ít nhất vài lát validation theo thời gian và số mẫu dự kiến ở test. Khoảng bất định dùng bootstrap theo khách.
- Chỉ đếm eligibility_count trong vùng test; lớp dương test là ước lượng từ tỷ lệ vùng phát triển, không phải nhãn đã xem.
- Người dùng duyệt quy tắc đơn hợp lệ, mục tiêu khách hiện có/khách mới, N/L, test window, tiêu chí kinh doanh cho ngưỡng, chỉ số tiền, kích hoạt Olist hay bỏ nhánh có giám sát/C.
- Sau khi CP1 khoá split, mọi thay đổi cấu hình hoặc DATA_CUTOFF cần tạo run mới và được duyệt lại trước khi mở test. Không tự tính lại cửa sổ đã duyệt.

**Nhánh Olist:** chỉ chạy khi CP1 quyết định. Nạp bảng với tiền tố riêng; ghi rõ nguồn trong mọi đầu ra; dùng để minh hoạ cách làm, không thay kết luận cho Xoaif và không gộp số liệu.

### Giai đoạn 4. EDA và tiền xử lý

- EDA gồm kiểu/thiếu, phân phối, ngoại lai, doanh số theo chiều có thể tính, giỏ nhiều sản phẩm, xu hướng thời gian và nhóm mẫu nhỏ. Mỗi hình có tiêu đề, nhãn trục, nguồn và nhận xét.
- EDA phục vụ quyết định mô hình chỉ đọc vùng phát triển. EDA toàn kỳ chạy sau đánh giá cuối, gắn nhãn mô tả và không dùng chọn lại mô hình.
- Dọn dữ liệu với lý do; xử lý thiếu/ngoại lai; dựng RFM và giỏ hàng; lưu chi tiết trong restricted.
- Mọi phép biến đổi học từ dữ liệu (impute, encode, scale, feature selection) nằm trong pipeline và chỉ fit trên train của từng lát.
- Đối soát tổng đơn/dòng hàng, trạng thái, tiền và bản ghi bị xoá; vấn đề không giải quyết được phải được ghi vào data quality report.

### Giai đoạn 5. Bài toán A

**Phân khúc mô tả — bắt buộc:** K-Means trên RFM; khảo sát K hợp lý bằng chỉ số, độ ổn định qua seed/bootstrap và khả năng diễn giải. Tên cụm dựa trên bảng mô tả cụm sau khi chạy. Cụm không chứng minh rời bỏ.

**Dự đoán khách quay lại — chỉ khi cổng dữ liệu đạt:**

1. Tạo mẫu (customer, T), feature-as-of T, nhãn tương lai theo quy tắc tại mục 4; không chồng cửa sổ nhãn trong đánh giá.
2. Chia theo thời gian, có khoảng purge/gap tối thiểu N+L; mọi lát CV tiến dần. Mục tiêu chính là khách hiện có nếu CP1 duyệt. Khi đó cùng một khách có thể xuất hiện ở train và test tại các mốc khác nhau; không được trùng quan sát (customer, T). Nếu mục tiêu là khách mới, phải tách customer giữa các tập.
3. So với baseline lớp đa số và baseline chỉ Recency; thử Logistic Regression, Decision Tree, Random Forest bằng pipeline.
4. Chọn tham số và ngưỡng theo validation/OOF temporal trước khi mở test. Kiểm tra ngưỡng có chuyển được sang mô hình fit cuối; nếu cần, hiệu chỉnh xác suất trong validation.
5. Mở nhãn test đúng một lần; báo Precision, Recall, F1, PR-AUC/ROC-AUC, ma trận nhầm lẫn, số lớp, khoảng bất định và baseline. Không chọn lại mô hình/ngưỡng bằng test.
6. Báo cáo số dòng customer-T và số khách duy nhất. Metric chính theo cơ hội customer-T; bổ sung kết quả gộp theo khách nếu một khách có nhiều mốc. Bootstrap lấy mẫu theo khách.
7. Nếu lịch sử trạng thái/đặc trưng không dựng được, số lớp/khách quá ít hoặc mô hình không hơn baseline, kết luận “chưa đủ bằng chứng”; không tạo danh sách hành động cá nhân.

### Giai đoạn 6. Bài toán B

- Tạo giỏ từ đơn theo basket_order_rule đã duyệt; ghi rõ xử lý đơn huỷ/hoàn và sản phẩm không chuẩn hoá.
- Chạy Apriori hoặc FP-Growth; thử mức support và ghi tiêu chí lọc, số lần xuất hiện.
- Xuất support, confidence, lift, leverage và số giỏ hỗ trợ cho từng luật; tránh chỉ xếp hạng theo lift khi support rất thấp.
- Nếu giỏ nhiều sản phẩm quá ít để luật có ý nghĩa, báo “chưa đủ cơ sở” cho Xoaif; chỉ chạy minh hoạ Olist tách riêng nếu CP1 duyệt.
- Chỉ đề xuất combo có thể truy về luật. Nêu rõ đó là giả thuyết cần thử nghiệm A/B; không gọi doanh thu giả định là kết quả thực.
- Chỉ đề xuất giá/giảm/lợi nhuận nếu người dùng cung cấp giá vốn, tồn kho và giả định giảm; nếu không, ghi thiếu dữ liệu.

### Giai đoạn 7. Bài toán C

- Kiểm kê nguồn và khối lượng văn bản tại CP1; nếu đủ, tạo taxonomy với định nghĩa, ví dụ và phản ví dụ.
- Làm sạch/ẩn danh hoá; lưu từng bản ghi chỉ trong restricted.
- Tạo tập nhãn chuẩn bằng người gán; nếu có thể hai người gán một phần để đo đồng thuận. Lưu hướng dẫn gán nhãn.
- Chỉ dùng LLM ngoài sau duyệt nhà cung cấp. Chất lượng đánh giá trên tập giữ riêng chưa dùng prompt/model tuning; báo precision/recall/F1 từng lớp, số mẫu từng lớp, lỗi điển hình.
- “F1 chấp nhận được” và hành động kinh doanh tương ứng phải được định nghĩa trước khi xem kết quả kiểm tra. Ví dụ văn bản thật chỉ đưa vào báo cáo khi đã duyệt từng trích dẫn; ưu tiên dùng tổng hợp.

### Giai đoạn 8. Dashboard, báo cáo và thuyết trình

- Dashboard Streamlit tối đa bốn tab: doanh số, phân khúc/dự đoán, combo, vấn đề. Chỉ đọc shared; mọi bộ lọc tuân thủ ẩn nhóm nhỏ và chống suy ngược; chạy được với snapshot ngoại tuyến.
- Báo cáo PDF theo đề mẫu: EDA, tiền xử lý, học có giám sát nếu thực hiện, học không giám sát, kết luận/hạn chế/đạo đức. Thêm kiến trúc năm tầng, vai trò-công cụ-chức năng-tác dụng và data flow.
- PPTX khoảng 12–15 slide hoặc theo thời lượng giảng viên; mỗi slide một thông điệp, biểu đồ đọc được khi in. Q&A trả lời được vì sao chọn K, nhãn T, kiểm soát rò rỉ, đại diện dữ liệu, quyền riêng tư, giới hạn combo và giới hạn lớn nhất.
- Tất cả con số trong báo cáo/slide lấy từ outputs có run manifest; không điền số dự kiến như kết quả.

**CP2:** duyệt kết quả, hạn chế, giữ/xoá raw và phạm vi chia sẻ.  
**CP3:** duyệt bản nháp báo cáo cùng dàn ý slide.  
**CP4:** duyệt bản cuối PDF/PPTX, speaker notes và kịch bản demo.

### Giai đoạn 9. QA và đóng gói

- Chạy pipeline từ snapshot đã xử lý trên môi trường sạch; notebook chạy từ đầu đến cuối.
- Quét secret, PII, mã khách/đơn, văn bản từng bản ghi trong repo, lịch sử git, báo cáo, slide, shared và outputs.
- Đối chiếu số liệu báo cáo/slide với outputs/metrics; kiểm tra run manifest, snapshot hash, cấu hình, phiên bản thư viện và commit.
- Xác nhận cấu hình dashboard không trỏ tới restricted, chế độ demo không phụ thuộc mạng, README đủ để người khác chạy.
- Thực hiện chính sách xoá/giữ raw sau khi CP2 duyệt; ghi lại kết quả và căn cứ.

## 6. Đề mẫu và sản phẩm nộp

| Mục đề mẫu | Nội dung tương ứng |
| --- | --- |
| EDA | Phân phối, thiếu, ngoại lai, nhóm ít mẫu, quan hệ biến và xu hướng thời gian. |
| Tiền xử lý | Làm sạch, định nghĩa đơn hợp lệ, tạo feature, point-in-time, pipeline và chia tập không rò rỉ. |
| Học có giám sát | Bài toán A nếu đủ dữ liệu: baseline, Logistic Regression, Decision Tree/max_depth, Random Forest, temporal CV và test độc lập. |
| Học không giám sát | K-Means RFM; luật kết hợp cho bài toán B; DBSCAN chỉ khi có toạ độ thật. |
| Kết luận | Kết quả có điều kiện, hạn chế dữ liệu/mô hình, riêng tư, đề xuất cải tiến và thử nghiệm kinh doanh. |

**Bộ bàn giao:** mã nguồn và README; dữ liệu mẫu đã làm sạch; từ điển và chính sách dữ liệu; kho DuckDB phù hợp; notebook; hình/bảng/metrics; run manifest; báo cáo PDF; sơ đồ kiến trúc; dashboard Streamlit bản demo; PPTX và Q&A. Video demo dự phòng là tuỳ chọn.

## 7. Các quyết định và thông tin còn thiếu

Trước khi bắt đầu cần nhận hoặc xác nhận:

1. Tài liệu API Pancake thực tế, mẫu phản hồi đã được phép chia sẻ và quyền API chỉ đọc.
2. Cách cung cấp dữ liệu: agent chạy script trên máy có quyền API hay người dùng xuất snapshot rồi chuyển vào workspace.
3. Hạn nộp, thời lượng báo cáo, rubric chính thức, số thành viên và người phụ trách.
4. Xác nhận đầu ra nào giảng viên bắt buộc trong nhóm PDF, dashboard, PPTX, Q&A.
5. Có giá vốn/tồn kho không; có quyền dùng văn bản khách và có thể duyệt nhà cung cấp LLM không.

**Giả định tạm thời:** báo cáo tiếng Việt; Pancake là nguồn dữ liệu chính; Olist không trộn với Xoaif; không có kết quả số cho tới khi khảo sát và xử lý dữ liệu thật.

## 8. Tiêu chí chấp nhận kế hoạch

Chỉ bắt đầu nhánh phân tích sau khi: (a) quyền/API và snapshot được xác minh; (b) timezone, DATA_CUTOFF, W và quy tắc thời gian được chốt; (c) CP1 duyệt N/L, test window và điều kiện khách đủ tiêu chuẩn; (d) có quyết định rõ nhánh nào đủ dữ liệu. Mục tiêu của kế hoạch là đáp ứng rubric và tạo kết luận đáng tin, không phải bắt buộc phải có mô hình cho cả ba bài toán.
