# Dữ liệu minh họa tổng hợp

**DỮ LIỆU TỔNG HỢP, KHÔNG PHẢI DỮ LIỆU CỬA HÀNG, KHÔNG DÙNG ĐỂ SUY RA KẾT QUẢ DỰ ÁN.**

Toàn bộ giá trị trong thư mục này do `scripts/make_sample_data.py` tự sinh; script không đọc dữ liệu cửa hàng, snapshot, DuckDB, bảng khách hay dữ liệu test. Seed cố định: `20261026`.

Sinh lại bằng Python của dự án:

```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
.venv\Scripts\python.exe -B scripts/make_sample_data.py
```

## Ánh xạ cột

- `sample_orders.csv` theo schema `fact_orders` được khai báo trong `scripts/build_dev_warehouse.py`: `order_key`, `customer_key`, `local_date`, `status_code`, `distinct_product_count`. Khóa chỉ dùng mã `SAMPLE-...`; `local_date` là ngày địa phương trong DEV `[2024-04-01, 2025-10-22)`.
- `sample_order_items.csv` dùng `order_key` và `product_key` theo các khóa của `fact_order_items`. `is_gift_line` là cờ minh họa riêng trong dữ liệu mẫu; không thêm khẳng định rằng đây là cột của kho restricted. Các mã sản phẩm đều là `SAMPLE-PRD-...`.
- `sample_aggregates_monthly.csv` dùng cùng cấu trúc với `outputs/tables/dashboard_sales_monthly.csv`: `month`, `recognized_revenue_vnd`, `orders`. Số tiền chỉ là giá trị minh họa tổng hợp được tạo bằng 100.000 đồng nhân số đơn mẫu status 3 của tháng; không phải số liệu kết quả dự án.

Các khóa khách, đơn và sản phẩm là mã giả được tạo riêng cho mẫu. Tệp này không được dashboard đọc; dashboard tiếp tục đọc các bảng tổng hợp trong `outputs/`.
