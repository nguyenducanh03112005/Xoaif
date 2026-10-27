# Artifact nộp và kiểm tra an toàn

Các file dưới đây được đưa vào Git để người chấm xem trực tiếp sau khi clone repo.

## PDF

- Báo cáo: [`report/xoaif_report.pdf`](../report/xoaif_report.pdf)
- Slide in 14 trang: [`slides/xoaif_print.pdf`](../slides/xoaif_print.pdf)

## Đầu vào tổng hợp của dashboard

Dashboard Streamlit đọc các bảng từ `outputs/tables/` và `outputs/metrics/`. Các aggregate sau được commit cùng mã nguồn:

**CSV**

- `dashboard_sales_monthly.csv`
- `dashboard_product_orders.csv`
- `dashboard_status_counts.csv`
- `test_segment_profiles.csv`
- `test_combos_frozen.csv`
- `combos_v2.csv`
- `seasonal_pair_metrics.csv`
- `gift_line_audit.csv`
- `gift_line_rates_monthly.csv`
- `gift_line_rates_order_size.csv`
- `dashboard_sales_province.csv` — không còn là đầu vào dashboard (91,92% doanh thu là `UNKNOWN`); được giữ vì `scripts/verify_day3_locks.py` và báo cáo PDF đọc bảng này. Có ô tỉnh chỉ 1–3 đơn; chỉ là aggregate, không có khách hay đơn riêng lẻ.

**JSON**

- `test_eval.json`
- `dev_final_models_v2.json`
- `dev_final_model.json`
- `day2_money_audit.json`
- `day3_combo_prereg.json`
- `day2_segmentation.json`

Đây là bảng/metric tổng hợp, không phải dữ liệu từng đơn hoặc từng khách. Bảng tỉnh/thành không còn là đầu vào dashboard vì phần lớn doanh thu bị gắn nhãn `UNKNOWN`.

## Chứng cứ toàn vẹn của lần mở test

- `outputs/metrics/test_opened.lock.json`, `outputs/metrics/day3_pretest_freeze.json`, `outputs/logs/test_eval_access.jsonl` được commit để người chấm kiểm tra rằng test chỉ mở một lần. Các file này chỉ chứa hash, cờ và mốc thời gian, không chứa giá trị hay định danh.
- Các hash được niêm phong trên byte gốc của working tree. Để checkout trên mọi hệ điều hành cho đúng byte, các file có hash được đánh dấu `-text` trong `.gitattributes` (khối do `scripts/fix_sealed_eol.py` sinh ra). Đừng chuẩn hóa xuống dòng các file này.
- Clone không có `data/raw/`, model `.joblib` và một số bảng trung gian, nên không thể xác minh đủ mọi hash. Dùng `python scripts/verify_day3_locks.py --shipped-only` để xác minh phần có trong repo; các input không có sẽ được liệt kê, không bị bỏ qua âm thầm. Chạy `python scripts/fix_sealed_eol.py --check` để biết file nào lệch byte.

## Rà soát dữ liệu

- `scripts/dashboard_smoke.py` kiểm tra 10 CSV và 6 JSON được dashboard dùng, schema cột và các tên trường định danh bị cấm.
- `scripts/verify_pii.py` đã chạy trên tài liệu, notebook và outputs; không phát hiện mẫu email, số điện thoại, địa chỉ hoặc giá trị trường nhạy cảm.
- Báo cáo và slide được dựng từ các bảng/metric aggregate trên, không đọc `data/raw/` hoặc `data/restricted/`.
- Không đưa snapshot raw, DuckDB restricted, bảng khách/đơn từng dòng, model artifact hoặc file môi trường vào danh sách nộp.

Chạy dashboard từ repo sau khi cài dependencies bằng `streamlit run src/app/streamlit_app.py`. Dashboard chỉ đọc dữ liệu cục bộ, không gọi API.
