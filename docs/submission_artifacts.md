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

**JSON**

- `test_eval.json`
- `dev_final_models_v2.json`
- `dev_final_model.json`
- `day2_money_audit.json`
- `day3_combo_prereg.json`
- `day2_segmentation.json`

Đây là bảng/metric tổng hợp, không phải dữ liệu từng đơn hoặc từng khách. Bảng tỉnh/thành không còn là đầu vào dashboard vì phần lớn doanh thu bị gắn nhãn `UNKNOWN`.

## Rà soát dữ liệu

- `scripts/dashboard_smoke.py` kiểm tra 10 CSV và 6 JSON được dashboard dùng, schema cột và các tên trường định danh bị cấm.
- `scripts/verify_pii.py` đã chạy trên tài liệu, notebook và outputs; không phát hiện mẫu email, số điện thoại, địa chỉ hoặc giá trị trường nhạy cảm.
- Báo cáo và slide được dựng từ các bảng/metric aggregate trên, không đọc `data/raw/` hoặc `data/restricted/`.
- Không đưa snapshot raw, DuckDB restricted, bảng khách/đơn từng dòng, model artifact hoặc file môi trường vào danh sách nộp.

Chạy dashboard từ repo sau khi cài dependencies bằng `streamlit run src/app/streamlit_app.py`. Dashboard chỉ đọc dữ liệu cục bộ, không gọi API.
