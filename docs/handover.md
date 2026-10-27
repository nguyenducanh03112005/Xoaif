# Bàn giao cho thành viên thứ hai

## Mục tiêu buổi đọc 1–2 giờ

Kết thúc buổi, người nhận cần tự giải thích được luồng Pancake → snapshot → ETL → DuckDB Star Schema → metric/biểu đồ; phân biệt DEV với test; trình bày ba nhóm khai phá; chỉ ra hạn chế và chạy được dashboard cùng nhánh hậu kiểm an toàn.

## Lịch đọc đề xuất

| Thời lượng | Việc cần làm | Tài liệu |
|---|---|---|
| 0–15 phút | Đọc quyết định, phạm vi, trạng thái test và điểm dừng | `README.md`, `docs/PROGRESS.md`, `docs/decisions.md` |
| 15–35 phút | Theo luồng nguồn, snapshot, schema, HMAC và chất lượng | `docs/data_dictionary.md`, `docs/data_governance.md`, `docs/day1_summary.md` |
| 35–55 phút | Nắm tiền, quà theo dòng, chống rò rỉ | `docs/money_definition.md`, `docs/money_audit.md`, `config/amendment_05_gift_lines.yaml`, `docs/test_report.md` |
| 55–80 phút | Giải thích mô hình, phân khúc và combo | `docs/day2_summary.md`, `outputs/metrics/test_eval.json`, `outputs/tables/test_combos_frozen.csv` |
| 80–100 phút | Mở dashboard, tập demo và phân vai hỏi đáp | `docs/demo_script.md`, `docs/qa.md`, `docs/qa_roles.md` |
| 100–120 phút | Chạy kiểm tra hậu mở và tự trình bày một kết quả | `.venv\Scripts\python scripts/run_all.py` |

## Luồng dữ liệu

1. `src/ingest/client.py` chỉ cho phép GET qua allowlist; API key chỉ nằm trong cấu hình riêng, không được chép vào báo cáo.
2. Snapshot `20261024T052943Z` được checksum-verify. Trước khi đọc nội dung đơn, pipeline kiểm tra `inserted_at` và phạm vi ngày theo `Asia/Ho_Chi_Minh`.
3. Các đơn trước `2024-04-01` được giữ trong raw nhưng không vào phân tích hành vi. DEV kết thúc trước `2025-10-22`.
4. ID khách/sản phẩm được HMAC trước khi vào DuckDB. Star Schema gồm `fact_orders`, `fact_order_items`, `dim_customer`, `dim_date`, `dim_order_status`, `dim_product`.
5. Dashboard dùng bảng tổng hợp trong `outputs/tables/`; không nối API và không đọc khóa khách/order.

## Phân công và đóng góp

Theo `docs/qa_roles.md`, Thành viên A trả lời chính về bài toán, kiến trúc, status 3/công thức tiền, mua lại DEV/test và CI, cổng hủy/hoàn, nhật ký amendment và khóa test. Thành viên B trả lời chính về snapshot/ETL/DQ/HMAC, phân khúc và proxy, luật kết hợp/gift line/mùa vụ/combo, cùng hạn chế và cách bàn giao. Người bổ sung nêu đúng phần trong bảng phân vai; không suy rộng thành phân công triển khai hoặc tỷ lệ đóng góp cá nhân.

## Những quyết định phải nhớ

- `revenue_recognized` là doanh thu ghi nhận theo xác nhận nghiệp vụ status 3, không phải đối soát ngân hàng và không phải lợi nhuận.
- Amendment 03 thay quy tắc tiền sau cổng 5% cũ; báo cáo phải nêu thay đổi và độ nhạy A/B.
- Quà tặng được phân loại theo từng dòng. `inferred_subset` có độ tin cậy thấp; không loại cố định sản phẩm theo tên.
- DEV có 18 tháng hiệu dụng và một Tết trọn vẹn. Nhãn DEV có 3.508 mẫu nhãn qua nhiều mốc T, 260 dương. Hủy/hoàn không fit vì fold dương lần lượt 30/13/6/1/18.
- Mô hình chính: Logistic Regression C=10 — mô hình chính theo D-005. Mô hình phụ: Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính. DEV OOF ROC-AUC C=10 khoảng 0,51, gần ngẫu nhiên; test khoảng 0,70 chỉ là tín hiệu yếu chưa được DEV xác nhận, không đủ để kết luận mô hình hoạt động tốt. Test đã mở; không dùng để tinh chỉnh hoặc chọn lại. Nêu tiếp: “Cấu hình ghi >T, evaluator dùng [T,end) (gồm ngày T); ảnh hưởng chưa xác định; đây là kết quả số liệu của lần chạy thực tế, không phải khẳng định tuân thủ đầy đủ giao thức, không gọi là 'đạt cổng ghi trước'.” Xem `docs/test_provenance_note.md`.
- K=2 là phân đoạn mô tả theo tần suất mua (một lần / lặp lại); chưa chứng minh các nhóm có ý nghĩa kinh doanh. 24 combo được đóng băng trước test; 21 cặp có lift > 1 trong test. Luật chỉ biểu thị đồng xuất hiện. Không có giá vốn nên không kết luận lợi nhuận combo.
- Không so sánh doanh thu theo tỉnh/thành: 91,92% UNKNOWN trên phạm vi dashboard DEV+test; DEV riêng là 91,56% đơn mua hợp lệ thiếu tỉnh và 90,73% doanh thu nằm ở nhóm thiếu tỉnh. Chưa xác định nguyên nhân nghiệp vụ. Bài phân loại phản hồi bị bỏ qua vì thiếu dữ liệu có nhãn.
- Cầu cohort được đếm trực tiếp: 5.499 − 325 pre-analysis-only = 5.174 − 5 gift-only = 5.169; phần dư chưa giải thích: 0. Xem `docs/cohort_reconciliation.md`.
- Quy trình đề xuất refresh snapshot mỗi tuần; giữ snapshot cũ, so manifest/tổng đơn/thay đổi status. Huấn luyện lại là chu kỳ riêng, có rolling-origin và amendment mới; không mở lại test cũ.
- Hạn nộp: 2026-10-27. Thời lượng chính thức và rubric chưa có trong hồ sơ. Mỗi thành viên tập trả lời ít nhất 10 câu thuộc phần của người kia.

## File và lệnh quan trọng

- Cấu hình split: `config/split.yaml`, `config/split.lock.json`.
- Cấu hình tiền/quà: `config/amendment_03_money_adjustment.yaml`, `config/amendment_05_gift_lines.yaml`.
- Cấu hình test: `config/amendment_05_test_open.yaml` và sidecar.
- Khóa mở một lần: `outputs/metrics/test_opened.lock.json`.
- Kết quả test: `outputs/metrics/test_eval.json`, `docs/test_report.md`.
- Artifact đã commit cho người chấm: hai PDF cùng các bảng/JSON dashboard, xem `docs/submission_artifacts.md`.
- Dashboard: `.venv\Scripts\python -m streamlit run src/app/streamlit_app.py`.
- Hậu kiểm: `.venv\Scripts\python scripts/run_all.py`; sau khi mở test, runner tự chuyển sang chế độ xác minh không fit/rerun.

## Bài tập tự kiểm tra

1. Giải thích vì sao status 3 là doanh thu ghi nhận nhưng chưa phải xác nhận ngân hàng.
2. Nêu hai ngưỡng tín hiệu, sai khác ngày T, và vì sao không thể khẳng định kết quả tuân thủ hoàn toàn giao thức đã khóa.
3. Chỉ ra vì sao TV phân khúc bằng 0 không chứng minh hành vi ổn định theo thời gian.
4. Mở `docs/qa.md`, tự trả lời một câu về `price_adjustment`, một câu về Spark và một câu về luật kết hợp.

Thành viên thứ hai đọc hết tài liệu trước khi chỉnh sửa bản trình bày cuối. Mọi thay đổi số liệu phải đối chiếu `outputs/metrics` hoặc DuckDB và giữ nguyên khóa test một lần.

## Không chia sẻ

- Không đưa `data/raw/`, `data/restricted/`, `data/restricted/quarantine/` hoặc bất kỳ file raw order page nào vào gói chia sẻ.
- Không chia sẻ bảng customer-HMAC, label-level hoặc prediction theo khách, gồm `day2_features_*.csv`, `day2_label_samples_*.csv`, `segments*.csv`, bảng test/customer profiles và model files trong `outputs/models/`.
- Không đưa file môi trường/local key vào gói. Chỉ xuất các bảng đã rà PII và được owner phê duyệt; chưa có release package được duyệt.
