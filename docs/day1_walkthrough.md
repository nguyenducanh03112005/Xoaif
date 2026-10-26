# Hướng dẫn Ngày 1 — kiểm tra được những gì?

**[LỊCH SỬ — trước lần mở test duy nhất]** Đây là hướng dẫn và trạng thái từ Ngày 1. Không chạy lại notebook để tái tạo các đầu ra đã khóa; trạng thái hiện hành ở `docs/PROGRESS.md` và kết quả test ở `docs/test_provenance_note.md`.

## Phạm vi

Chủ dự án xác nhận Xoaif Garden bắt đầu kinh doanh từ `2024-04-01` theo giờ Việt Nam. Vì vậy, các đơn trước ngày này vẫn được giữ nguyên trong raw nhưng thuộc giai đoạn bán thử đầu tiên và bị loại khỏi phân tích hành vi. Tập phát triển hiệu dụng là `[2024-04-01, 2025-10-22)`. Không dùng nhãn hay hành vi test.

Snapshot gốc là `20261024T052943Z` với 12.011 đơn trên 601 trang. Hash manifest là `3536a0e5303d83a6fbddd19e6f52375ed70dd53a070d1cadb8691a66ad4acf5c`. Cấu hình split `config/split.yaml` được giữ nguyên; amendment riêng và hash sidecar nằm trong `config/amendment_01_analysis_start.yaml` và `config/amendment_01_analysis_start.lock.json`.

## Các file và bước chính

| File/bước | Làm gì và vì sao | Đầu vào | Đầu ra |
|---|---|---|---|
| `config/split.yaml` + `config/split.lock.json` | Khóa snapshot và mốc test; được giữ nguyên để kết quả so sánh được. | Quyết định split đã chốt | Hash cấu hình và mốc `test_start` |
| `config/amendment_01_analysis_start.yaml` + sidecar `.lock.json` | Ghi riêng quyết định ngày mở cửa hàng; sidecar giữ SHA-256 của YAML và hash của split lock. YAML không tự chứa hash của chính nó vì việc đó tạo vòng lặp. | Quyết định chủ dự án ngày 2026-10-25 | Mốc `analysis_start=2024-04-01`, lý do và hash kiểm chứng |
| `scripts/profile_analysis_start.py` | Đếm đơn theo tháng, phân loại đơn trước ngày mở, và rà trường tiền chỉ trong status 3 của dev sau ngày mở. Với ngày từ `test_start` trở đi chỉ dùng `inserted_at` để loại dòng. | Snapshot đã khóa và amendment | Bảng tổng hợp trong `outputs/tables/`; không xuất mã khách hoặc giá trị tiền từng đơn |
| `scripts/build_dev_warehouse.py` | Dựng kho chỉ với `[analysis_start,test_start)`, HMAC các ID và bỏ tiền/văn bản/lịch sử trạng thái. | Snapshot, split, amendment | `data/restricted/xoaif_dev.duckdb` |
| `fact_orders`, `fact_order_items`, các bảng `dim_*` | Lưu đơn, liên kết dòng hàng và các bảng tra cứu. | Dữ liệu dev đã lọc | Star Schema dùng được bằng SQL; không có giá trị tiền hay dữ liệu trước ngày mở |
| Notebook `notebooks/01_day1_development_eda.ipynb` | Tạo thống kê và biểu đồ mô tả tập dev. | Kho DuckDB dev | Bảng/biểu đồ, không phải mô hình |
| `scripts/run_all.py` | Kiểm tra split, amendment, GET-only, PII, pytest; rà dữ liệu, dựng kho, làm mới hình và chạy notebook. | Môi trường `.venv` và snapshot | Log kiểm tra; không tự cài gói |

## Số liệu chính

**Tổng quan snapshot để kiểm tra nguồn:** status hiện tại: 0 = 2, 1 = 14, 3 = 11.841, 4 = 1, 5 = 25, 6 = 128 (tổng 12.011). Đây là số liệu tổng hợp nguồn đã ghi nhận, không đưa đơn test vào phân tích phát triển. DQ snapshot: 342 đơn thiếu `customer_id`; 12 đơn không có dòng hàng; 959/51.012 dòng hàng thiếu `product_id`.

**Kho phát triển sau khi áp dụng ngày mở:** 6.517 đơn từ `2024-04-01` đến `2025-10-21`, gồm status 3 = 6.400, status 5 = 13, status 6 = 104. Có 5.174 khách có ít nhất một đơn status 3. DQ trong kho hiệu dụng: 286 đơn status 3 thiếu `customer_id`; 5 đơn status 3 không có dòng hàng; 726 dòng hàng thiếu `product_id`; không có cấu trúc dòng hàng sai.

Trong 5.174 khách có mã và ít nhất một đơn status 3, 648 (12,52%) có từ hai đơn status 3 trở lên trên toàn giai đoạn dev. Đây là tần suất mô tả, không phải tỷ lệ nhãn mua lại.

## Khoảng trống và đơn trước ngày mở

Từ 2022-06-04 đến 2022-09-21 có 476 đơn: status 3 = 462, status 5 = 8, status 6 = 6. Tổng cộng có 887 dòng hàng; 429 đơn có `customer_id`, 47 đơn thiếu mã khách. Không có tên sản phẩm khớp từ khóa kiểm tra `test`, `sample`, `demo`, `thử`, `mẫu`, `init`, `khởi tạo`. Không phát hiện dấu hiệu tên không chứng minh rằng mọi đơn cũ là đơn thử; việc loại toàn bộ trước mốc là quyết định chủ dự án.

Các tháng 2022-10 đến 2024-03 đều có 0 đơn ở mọi trạng thái trong snapshot. Theo thông tin chủ dự án, cửa hàng chưa kinh doanh trong thời gian này. Bảng tất cả tháng trước test ở [day1_monthly_orders_all_status.csv](../outputs/tables/day1_monthly_orders_all_status.csv); chi tiết ngày mở ở [data_gap_report.md](data_gap_report.md).

## Lệnh PowerShell tự kiểm tra

Chạy tại thư mục gốc dự án. Các lệnh chỉ đọc kho dev ở chế độ chỉ đọc, không in mã định danh.

```powershell
.\.venv\Scripts\python.exe -c "import duckdb; c=duckdb.connect('data/restricted/xoaif_dev.duckdb', read_only=True); print(c.execute('SELECT COUNT(*) AS dev_orders, MAX(local_date) AS max_dev_order_date FROM fact_orders').fetchall())"
```

```powershell
.\.venv\Scripts\python.exe -c "import duckdb; c=duckdb.connect('data/restricted/xoaif_dev.duckdb', read_only=True); print(c.execute('SELECT status_code, COUNT(*) AS orders FROM fact_orders GROUP BY status_code ORDER BY status_code').fetchall())"
```

```powershell
.\.venv\Scripts\python.exe -c "import duckdb; c=duckdb.connect('data/restricted/xoaif_dev.duckdb', read_only=True); print(c.execute('SELECT COUNT(DISTINCT customer_key) AS customers FROM fact_orders WHERE status_code=3 AND customer_key IS NOT NULL').fetchall())"
```

Chạy lại pipeline kiểm tra và phát triển Ngày 1/2:

```powershell
.\.venv\Scripts\python.exe scripts/run_all.py
```

## Split và chống rò rỉ

Split test không đổi: `test_start=2025-10-22`, test T `[2025-10-22, 2026-04-20)`, `N=180`, `L=7`, `W=180`; `DATA_CUTOFF=2026-10-24` là mốc loại trừ. Trong cấu hình khóa, N là chân trời nhãn quay lại và W là độ dài cửa sổ các thời điểm T; `H_obs` là toàn bộ lịch sử hợp lệ `[analysis_start,T)` theo amendment 03. Độ nhạy `N=365`/`W=365` chỉ dùng phát triển; kiểm tra lịch/cohort sơ bộ được nêu trong [day1_summary.md](day1_summary.md). Nhãn dev hiện đã tạo; test chưa mở.

Hình [split_timeline.png](../outputs/figures/split_timeline.png) cho thấy mốc mở cửa, cửa sổ dev, test, N, L và cutoff. (1) EDA dev chỉ dùng ngày từ `analysis_start` đến trước `test_start`. (2) Đặc trưng tại T chỉ được tạo từ dữ liệu có trước hoặc tại T; nhãn dự kiến nhìn về sau T. (3) N và L phải kết thúc trước cutoff để trạng thái nhãn có thời gian ổn định; vùng test vẫn chưa mở.

## Kết thúc Ngày 1

Tại thời điểm chốt Ngày 1, amendment 02 ghi nhận 10,95% đơn bất thường và kích hoạt cổng 5%. Amendment 03 sau đó thay quy tắc tiền trước khi sinh nhãn; Ngày 2 đã hoàn thành theo cổng doanh thu âm 1%. Xem [day2_summary.md](day2_summary.md), [money_audit.md](money_audit.md) và [PROGRESS.md](PROGRESS.md). Test vẫn đóng và Ngày 3 chưa bắt đầu.
