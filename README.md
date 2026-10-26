# Xoaif Garden — phân tích dữ liệu bán hàng

Dự án Python cho snapshot Pancake POS, kho DuckDB và phần khai phá dữ liệu theo từng ngày làm việc. Kế hoạch tổng thể ở [Ke_hoach_cuoi_cung_Xoaif_Garden.md](Ke_hoach_cuoi_cung_Xoaif_Garden.md).

## Trạng thái dự án

- Snapshot khóa: `20261024T052943Z`, 12.011 đơn trên 601 trang. Manifest SHA-256: `3536a0e5303d83a6fbddd19e6f52375ed70dd53a070d1cadb8691a66ad4acf5c`.
- Chủ dự án xác nhận cửa hàng mở từ `2024-04-01`. Mốc này ghi trong `config/amendment_01_analysis_start.yaml`; `config/split.yaml` không bị sửa.
- Kho dev hiệu dụng: `[2024-04-01, 2025-10-22)`, 6.517 đơn; 6.400 status 3; 5.174 khách có đơn status 3.
- Split giữ nguyên: `N=180`, `L=7`, `W=180`, test T `[2025-10-22, 2026-04-20)`. Test đã mở đúng một lần theo cấu hình Amendment 05; xem `outputs/metrics/test_eval.json` và `docs/test_report.md`.
- Vai trò mô hình được giữ thống nhất: Logistic Regression C=10 — mô hình chính theo D-005; Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính. ROC-AUC DEV OOF C=10 khoảng 0,51, gần mức ngẫu nhiên; ROC-AUC test khoảng 0,70 là tín hiệu yếu chưa được development xác nhận, không đủ để kết luận mô hình hoạt động tốt. Test đã mở và không dùng để tiếp tục tinh chỉnh. Xem `docs/test_report.md` và `docs/test_provenance_note.md`.
- Amendment 03 là quy tắc tiền đang có hiệu lực; amendment 02 giữ làm lịch sử. Audit DEV ghi nhận 22 đơn quà, 2/6.400 đơn doanh thu âm (0,03%), đạt cổng 1%. Quy tắc quà tặng theo từng dòng và các combo đã được khóa trước khi mở test.
- Hạn nộp: **2026-10-27**. Thời lượng thuyết trình và rubric chính thức chưa có trong hồ sơ; xem [lịch](docs/schedule.md).
- Sản phẩm Ngày 3: dashboard Streamlit, PDF, slide in dạng PDF, kịch bản demo, QA và hướng dẫn bàn giao ở các đường dẫn bên dưới. Không có file PPTX vì môi trường không cài `python-pptx`; đã dùng phương án PDF fallback mà không cài gói mới.

Xem [tổng kết Ngày 2](docs/day2_summary.md), [hướng dẫn kiểm tra](docs/day2_walkthrough.md), [tiến độ](docs/PROGRESS.md), [định nghĩa tiền](docs/money_definition.md), [kiểm toán tiền dev](docs/money_audit.md) và [đầu vào dự kiến cho Ngày 3](docs/day3_inputs.md).

## Hồ sơ phân tích và audit

- [Định nghĩa cohort](docs/cohort_definitions.md), [rà soát leakage/test](docs/test_audit.md), [metric phân loại](docs/metric_rationale.md) và [ma trận kiến trúc](docs/architecture_matrix.md).
- [Sổ số chuẩn](docs/canonical_numbers.md) ghi giá trị aggregate, cohort, đơn vị và khóa nguồn; [nhật ký nhất quán](docs/consistency_log.md) ghi các vòng rà soát.
- [Báo cáo rà soát cuối](docs/final_consistency_report.md) tóm tắt phạm vi, kết quả hậu kiểm và các việc nhóm cần làm trước khi nộp.
- EDA tổng hợp DEV: [notebook 01b](notebooks/01b_eda_dev.ipynb), [script chỉ đọc](scripts/build_eda_dev_artifacts.py), JSON aggregate và hình `outputs/figures/eda_dev_*.png`.

## Chạy kiểm tra trên Windows

Luôn gọi đúng Python của repo:

```powershell
.venv\Scripts\python scripts/run_all.py
```

Sau khi test đã mở, `run_all.py` chỉ xác minh split, API GET-only, hash khóa, chạy pytest và quét PII. Nó không chạy lại evaluator, notebook hay bước fit/chọn mô hình. Không chạy lại `scripts/evaluate_test_once.py`: script từ chối khi `outputs/metrics/test_opened.lock.json` tồn tại.

## Sản phẩm bàn giao

- Dashboard offline: `streamlit run src/app/streamlit_app.py`. Tab Tổng quan mặc định phủ 2024-04–2026-04, gồm DEV và cửa sổ test (9.104 đơn; tháng cuối chưa trọn), không chỉ DEV.
- Báo cáo: `report/xoaif_report.pdf`.
- Bộ slide thuyết trình dạng PDF in 14 trang: `slides/xoaif_print.pdf`; ghi chú từng slide và phân vai ở `slides/speaker_notes.md`. Không tạo PPTX do `python-pptx` không có trong môi trường; không cài gói mới.
- Demo dự phòng, QA và bàn giao: `docs/demo_script.md`, `docs/qa.md`, `docs/qa_roles.md`, `docs/handover.md`.
- Kết quả test: `outputs/metrics/test_eval.json`, `docs/test_report.md`.
- Các artifact phục vụ người chấm được commit gồm hai PDF và các CSV/JSON aggregate mà dashboard đọc trực tiếp; danh sách đầy đủ ở `docs/submission_artifacts.md`. Dashboard không cần raw/restricted data.

Dashboard chỉ đọc bảng tổng hợp từ `outputs/`; không gọi API. Không so sánh doanh thu theo tỉnh/thành vì 91,92% doanh thu mang nhãn `UNKNOWN`. Bài phân loại phản hồi bị bỏ qua do thiếu dữ liệu phản hồi có nhãn. K-Means K=2 chủ yếu tách khách mua một lần với khách mua lặp lại; chưa chứng minh ý nghĩa kinh doanh của các nhóm. Không có giá vốn nên không kết luận lợi nhuận combo. Do giảm giá/điều chỉnh ở cấp đơn, dashboard không phân bổ doanh thu ghi nhận cho từng sản phẩm.

## Dữ liệu và an toàn

- Raw snapshot nằm trong `data/raw/`; không xóa đơn trước ngày mở và không commit raw.
- DuckDB restricted nằm tại `data/restricted/xoaif_dev.duckdb`; ID đã được HMAC. Kho không chứa trường tiền, địa chỉ, văn bản tự do, `status_history`, đơn trước ngày mở hoặc dữ liệu test.
- Snapshot cũ `20261023T174441Z` có 12.009 đơn và sai checksum trang; mọi số liệu từ snapshot cũ đã hết hiệu lực.
- Pancake Open API dùng API key qua query string và key có quyền cao. Không đưa key vào chat hoặc commit. Client dự án chỉ cho phép GET.

Thông tin API và các giới hạn đã biết nằm ở [docs/api_notes.md](docs/api_notes.md); từ điển trường ở [docs/data_dictionary.md](docs/data_dictionary.md).
