# Nhật ký rà soát nhất quán cuối

Ngày rà soát: 2026-10-26. Phạm vi gồm tài liệu giao nộp, README/PROGRESS, dashboard, hai PDF đầu ra và script dựng PDF/slide. Nguồn số liệu được đối chiếu chỉ là bảng/JSON aggregate và quyết định đã khóa.

## Phạm vi an toàn

- Không đọc dòng đơn hàng, nhãn, hành vi hoặc dữ liệu `data/restricted`; không nạp bảng customer-HMAC/label-level.
- Không chạy evaluator, notebook, model fit/refit hay chọn lại mô hình; không gọi API.
- Không sửa split, Amendment 01–05, sidecar/lock, lock mở test, `test_eval.json`, access log hay D-001–D-020. Diễn giải mới được ghi ở D-021/D-022.
- Không cài package và không tạo PPTX. PDF là bản in dự phòng đã chọn.

## Các điểm phát hiện và sửa

1. **Metric và vai trò mô hình:** bổ sung CI ROC-AUC, AP và paired ΔAP cho cả C=10 và feature-v2; chuẩn hóa vai trò C=10 là mô hình chính theo D-005 và feature-v2 là khảo sát Amendment 04, không thay mô hình chính. Làm rõ quy tắc tín hiệu áp dụng cho cả hai classifier; cờ `feature_v2_signal_supported` vẫn chỉ thuộc feature-v2.
   Tên chuẩn: **Logistic Regression C=10 — mô hình chính theo D-005**; **Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính**.
2. **Giới hạn ngày T:** thống nhất câu caveat bắt buộc ở tài liệu kết quả, QA, bàn giao, demo, progress, speaker notes, dashboard và nguồn dựng PDF/slide. Tách “thỏa ngưỡng số liệu” khỏi kết luận tuân thủ giao thức; không khẳng định cổng ghi trước đã được đáp ứng.
3. **Cohort và số tổng hợp:** thống nhất các định nghĩa riêng của 5.499, 5.174 và 5.169; sửa tỷ lệ một đơn theo đúng mẫu số; giữ 24 combo theo điều kiện ổn định ít nhất 4/6 ô và báo đúng 21/24 lift > 1 trên 2.174 giỏ.
4. **Lịch sử và tiền:** gắn nhãn các đoạn trạng thái trước khi mở test là lịch sử; phân biệt định nghĩa tiền Amendment 02 với Amendment 03; sửa cách ghi số tiền để PII regex không nhầm thành số điện thoại mà vẫn giữ nguyên giá trị.
5. **Đầu ra và chỉ dẫn:** đồng bộ README/PROGRESS; sửa hiển thị `C=0,1` trong PDF builder; dựng lại PDF 15 trang và slide PDF 14 trang; cập nhật ảnh tab Model. Thêm guard để builder tài liệu tiền mở không ghi đè nội dung sau khi test đã mở.

## Vòng kiểm tra cuối

Đã render lại các trang báo cáo 7–15 và slide 6–14 sau lần dựng cuối. Kiểm tra trực quan xác nhận trang metric, caveat ngày T, kết luận, combo và checklist trình bày không bị tràn/cắt. Số trang xác nhận bằng `pdfinfo`: báo cáo 15 trang A4, slide in 14 trang ngang. `pdftotext` không có trong runtime; vì vậy phần chữ được kiểm qua nguồn dựng và ảnh render, không qua trích xuất văn bản PDF.

Các vòng kiểm tra:

- Scan ban đầu phát hiện 5 thiếu sót: `qa_roles.md` chưa có caveat nguyên văn và hai tên vai trò chuẩn; nhật ký mới chưa ghi đủ hai tên vai trò. Đã sửa cả 5 mục.
- Dashboard smoke sau đó phát hiện checker kỳ vọng 5 JSON trong khi app đọc 6 JSON aggregate. Đã sửa kỳ vọng, cập nhật canonical/progress/slide và dựng lại slide PDF.
- Final consistency scan 1: **0 findings**.
- Final consistency scan 2: **0 findings**.

Phạm vi scan: tên/vai trò mô hình; caveat ở mọi vị trí nêu tín hiệu test; các mốc combo/cohort; số trang và liên kết README; dashboard data-contract; dấu hiệu trạng thái tiền mở bị trình bày như trạng thái hiện hành; cú pháp và nội dung các đầu ra đã dựng.

**Câu caveat chuẩn:** Cấu hình ghi >T, evaluator dùng [T,end) (gồm ngày T); ảnh hưởng chưa xác định; đây là kết quả số liệu của lần chạy thực tế, không phải khẳng định tuân thủ đầy đủ giao thức, không gọi là 'đạt cổng ghi trước'.

## Chưa xác minh / việc chuyển giao

- Các cohort 5.499 / 5.174 / 5.169 chưa được phân rã đối soát; không suy diễn quan hệ giữa chúng.
- Nguyên nhân doanh thu tỉnh UNKNOWN chiếm 91,92% chưa được phân tích.
- Chênh lệch DEV–test và giả thuyết lịch sử đặc trưng dài hơn/mùa vụ/prevalence chưa được kiểm chứng. Không chạy chẩn đoán anchor; D-022 ghi rõ muốn kiểm tra hợp lệ phải có thiết kế rolling-origin, amendment mới và duyệt của chủ dự án.
- Thời lượng thuyết trình và rubric chính thức chưa có trong hồ sơ.
- Không còn artifact combo Day2B sạch để dựng lại bản tóm tắt Day2B; builder hiện từ chối chạy sau khi lock test tồn tại, tránh ghi đè bản lưu trữ bằng artifact không đúng schema.
- Runtime thiếu công cụ trích xuất chữ PDF; đã kiểm source và render trực quan.
- Một literal lịch sử trong YAML Amendment 04 đã khóa và trường metadata/code tương ứng không được sửa theo ranh giới bảo vệ; không dùng trong narrative bàn giao.

Trước hạn 2026-10-27, hai thành viên tự chạy kiểm tra an toàn và mở đủ 5 tab trên máy riêng; tập demo 4 phút có mạng và không mạng; kiểm bản in đen trắng; mỗi người luyện ít nhất 10 câu hỏi chéo. Hướng dẫn hiện hành: `docs/PROJECT_GUIDE.md` và `docs/DEFENSE_GUIDE.md`.

## Cập nhật hồ sơ nộp — 2026-10-26

- Đưa diễn giải về ROC-AUC DEV gần 0,51 và test khoảng 0,70 về mức tín hiệu test yếu, chưa được DEV xác nhận; nêu rõ không tinh chỉnh sau khi test đã mở.
- Làm rõ K=2 là phân đoạn mô tả theo tần suất mua (một lần / lặp lại), chưa chứng minh ý nghĩa kinh doanh; ghi nhận bài phân loại phản hồi bị bỏ qua do thiếu nhãn.
- Bỏ bảng tỉnh/thành khỏi dashboard và ảnh tổng quan cũ vì 91,92% doanh thu mang nhãn UNKNOWN; PDF nêu caveat thay cho xếp hạng khu vực.
- Dựng lại hai PDF và commit 10 CSV/6 JSON aggregate dashboard sau khi smoke/schema và PII regex đạt. Không đưa raw, restricted hoặc bảng khách/đơn từng dòng vào repo.

## Cập nhật rà soát — 2026-10-27

- Đối soát read-only: 6.517 đơn DEV = 6.400 status 3 + 117 status khác 3. Ba cohort khách 5.499/5.174/5.169 vẫn **chưa giải thích được**; không có bảng cầu nối aggregate, nên ghi rõ giới hạn và không gỡ mục này khỏi báo cáo cuối.
- Không có prediction artifact đã lưu trong `outputs/`; Amendment 06 sensitivity dừng theo điều kiện, không tạo lại prediction, không đọc test restricted.
- Schema warehouse không có source/channel/type/address/province; UNKNOWN diagnostic kết luận **chưa xác định**.
- K=2 được chuẩn hóa thành “phân đoạn mô tả theo tần suất mua (một lần / lặp lại)” trong narrative, dashboard và PDF/slide builders. Tạo hướng dẫn refresh theo lô; extractor không chạy.
- Hygiene: `git ls-files` không tìm thấy env secret, raw/restricted data, DuckDB hay artifact dòng khách/nhãn/prediction; kết quả `xoaif.env.example` là mẫu cấu hình. `.codex/` không được track và đã nằm trong `.gitignore`.
- Hậu kiểm sau cập nhật: Day 3 locks và hash bảo vệ đạt; `run_all.py` hậu mở đạt, 75 pytest, PII scan, dashboard smoke (5 tab/10 CSV/6 JSON/405 dòng) đều đạt. Không evaluator, notebook hoặc fit/refit.

## Cập nhật hậu mở theo D-024 — 2026-10-28

Phạm vi: aggregate đã có, bảng nhãn DEV và lịch công khai thủ công. Không đọc order pages, không truy cập kho restricted, không đọc lại test records/labels hoặc gọi API. `verify_split_lock.py` chỉ đọc manifest metadata để xác minh hash theo kiểm tra bắt buộc. Lịch sử các vòng rà soát trước vẫn giữ nguyên; kết quả dưới đây là bổ sung theo Amendments 06–10.

1. **Cohort:** cầu nối đã đối soát `5.499 − 325 = 5.174 − 5 = 5.169`, dư chưa giải thích bằng 0. Định nghĩa từng bước ở `docs/cohort_definitions.md` và `docs/cohort_reconciliation.md`.
2. **Tỉnh/thành:** DEV có tên/mã tỉnh chính ở 540/6.400 đơn status 3; 5.860/6.400 (91,56%) UNKNOWN. Doanh thu UNKNOWN là 2.384.693.718/2.628.354.091 VND (90,73%). `new_province_id` bổ sung 23 mã chưa có mapping xác minh; không khôi phục tab tỉnh.
3. **Ngày T:** độ nhạy DEV có 3 mẫu khách–T có đơn đúng T; do thiếu cờ quà cấp đơn, chỉ báo cận 260–262/3.508 (7,41%–7,47%), không gọi là ước lượng chính xác và không suy ra tác động test.
4. **Kênh:** DEV có Facebook 3.722/6.400 (58,16%), thiếu nguồn 2.404/6.400 (37,56%), Instagram gộp với nguồn hiếm 274/6.400 (4,28%). Không thấy nhãn Shopee/sàn tường minh không chứng minh shop không bán trên sàn. Ô nhỏ được ẩn theo `docs/channel_monthly_coverage.md`.
5. **Probe Pancake:** probe chỉ GET trên 5 endpoint allowlist, mẫu tối đa 500; products 832 entries/482 mẫu/394 match (81,74%), customers 13.232 entries/482 mẫu/194 match `customer_id` (40,25%), ba endpoint còn lại có 0 entries. Match là trên mẫu, không đại diện population; chưa ingest endpoint nào.
6. **Phân cụm:** K=2 còn là phân đoạn mô tả một lần/lặp lại, chưa chứng minh ý nghĩa kinh doanh. RFM silhouette trung bình qua 5 seed: K=3 0,390146; K=4 0,385302; K=5 0,392276 — gần nhau, không đủ cơ sở chọn phân cụm kinh doanh.
7. **Lịch thời gian:** chạy DEV-only rolling-origin, 3.508 mẫu, 5 folds/1.558 dự đoán OOF; pooled ROC-AUC/AP 0,5279/0,0800 cho feature gốc và 0,5181/0,0767 khi thêm thời gian. Không cải thiện và không thay mô hình chính.
8. **Refresh/dashboard:** live refresh bị chặn vì hợp đồng `updated_at` chưa xác minh; chế độ replay không chạy vì cần đọc/ghi `data/raw`. Dashboard chỉ dùng aggregate khóa, nêu snapshot `20261024T052943Z` và ghi rõ chưa có dữ liệu refresh được xác minh.
9. **Kiểm chứng:** pytest 105 passed; dashboard smoke 5 tab/10 CSV/6 JSON/405 hàng pass; PII text scan pass; `git diff --check` pass. `verify_split_lock.py` và `verify_day3_locks.py --shipped-only` pass; lock hiện có 39 sealed input hashes và tất cả input đã kiểm tra khớp. Không chạy evaluator test, notebook hay API.

Các thay đổi hồ sơ được gắn Amendments 06–10 trong `docs/amendment_log.md`; không đổi `config/split.yaml`, split/test locks, Amendment 01–05, test artifact hay field allowlist.

## Cập nhật phát hành aggregate — 2026-10-28

- Bổ sung bảng `dashboard_sales_province.csv` vào bước xử lý ô nhỏ: 20 tỉnh dưới 10 đơn được gộp thành `Các tỉnh khác — từng tỉnh dưới 10 đơn` (38 đơn; 16.674.000 VND). Tổng orders và recognized revenue được bảo toàn; `UNKNOWN` giữ nguyên để tính tỷ lệ thiếu tỉnh. Không thay đổi test lock, split hay metric test; có bổ sung metric thời gian DEV-only ở `outputs/metrics/holiday_time_supplement_dev.json`.
- Chính sách đã chọn: giữ số 5 khách chỉ có đơn quà trong cầu cohort để giải thích `5.499 − 325 = 5.174 − 5 = 5.169`; giữ count gift-line vì đó là số dòng hàng, không phải số khách/đơn.
- Chạy lại sanitizer và dựng báo cáo/slide PDF. Test tập trung suppression + holiday + endpoint probe + batch refresh: 16 passed; full suite trên checkout có dữ liệu: 108 passed. PII scanner được giới hạn whitespace địa chỉ trong một dòng để không nối các dòng CSV liền kề; test hồi quy xác nhận hành vi này. PII scan, dashboard smoke, split lock, shipped Day 3 lock và `git diff --check` đều pass. Kiểm tra hiển thị PDF và metadata: báo cáo A4 15 trang, slide 15 trang; trang EDA nêu rõ 91,92% UNKNOWN cùng dòng gộp 20 tỉnh dưới ngưỡng.
- Kiểm tra clone sạch ở commit `ef82631`: cài `.[analysis,dashboard,dev]`; `run_all.py` clone mode pass; 107 passed, 1 skipped do DuckDB DEV restricted không có trong clone; PII scan và dashboard smoke pass. `verify_split_lock.py` chủ ý bị bỏ qua trong clone mode vì manifest raw bị loại; bản gốc đã xác minh split lock.
