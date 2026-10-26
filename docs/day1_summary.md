# Tổng kết Ngày 1

Ngày cập nhật: 2026-10-25  
Snapshot: `20261024T052943Z`  
Phạm vi phân tích dev: `[2024-04-01, 2025-10-22)` theo `Asia/Ho_Chi_Minh`

**[LỊCH SỬ — trước lần mở test duy nhất]** Tài liệu ghi lại trạng thái ở Ngày 1. Các câu “test chưa mở” mô tả đúng thời điểm đó; trạng thái hiện hành và kết quả test ở `test_provenance_note.md`.

## Đã làm

- Khóa snapshot `20261024T052943Z` (12.011 đơn, 601 trang; manifest SHA-256 `3536a0e5303d83a6fbddd19e6f52375ed70dd53a070d1cadb8691a66ad4acf5c`) và giữ nguyên `config/split.yaml` cùng hash.
- Ghi quyết định ngày mở cửa hàng trong amendment riêng. Raw không bị xóa/sửa; các đơn trước 2024-04-01 không đi vào kho phát triển hiệu dụng hay các phân tích hành vi.
- Dựng lại Star Schema DuckDB chỉ cho ngày địa phương từ `2024-04-01` đến trước `2025-10-22`; ID được HMAC. Không ghi trường tiền, văn bản tự do, `status_history`, nhãn hoặc hành vi test.
- Tạo bảng số đơn mọi trạng thái theo tháng, phân loại các đơn trước ngày mở, cập nhật hình split và khảo sát trường tiền trên status 3 thuộc tập phát triển. Cuối Ngày 1, amendment 02 kích hoạt cổng lịch sử 5%; amendment 03 sau đó thay quy tắc tiền trước khi tạo nhãn và cho phép tiếp tục.

## Số liệu

**Kiểm kê snapshot nguồn:** 12.011 đơn trên 601 trang. Trạng thái hiện tại đã ghi nhận: status 0 = 2; 1 = 14; 3 = 11.841; 4 = 1; 5 = 25; 6 = 128. Snapshot DQ: 342 đơn thiếu `customer_id`; 12 đơn không có dòng hàng; 959/51.012 dòng hàng thiếu `product_id`. Đây là tổng hợp kiểm tra nguồn; các số này không được dùng để phân tích hành vi test.

**Giai đoạn bán thử đầu tiên (trước ngày mở):** 476 đơn từ 2022-06-04 đến 2022-09-21; status 3 = 462, status 5 = 8, status 6 = 6; 887 dòng hàng; 429 đơn có mã khách, 47 thiếu mã khách. Có 0/476 đơn có tên sản phẩm khớp các từ khóa kiểm tra thử/demo/mẫu. Chủ dự án xác nhận đây là giai đoạn bán thử đầu tiên; loại toàn bộ trước mốc khỏi phân tích hành vi, không coi là lỗi dữ liệu.

**Tập phát triển hiệu dụng:** 6.517 đơn từ 2024-04-01 đến 2025-10-21; status 3 = 6.400, status 5 = 13, status 6 = 104. Có 5.174 khách có ít nhất một đơn status 3. DQ: 286 đơn status 3 thiếu mã khách; 5 đơn status 3 không có dòng hàng; 726 dòng hàng thiếu `product_id`; 0 cấu trúc dòng hàng sai. Có 648/5.174 khách (12,52%) với từ hai đơn status 3 trở lên trong toàn giai đoạn; đây là tần suất mô tả, chưa phải tỷ lệ nhãn.

Khoảng trống 2022-10–2024-03 có 0 đơn mỗi tháng ở mọi trạng thái. Theo chủ dự án, cửa hàng chưa kinh doanh khi đó.

## Quyết định và giới hạn

- `analysis_start=2024-04-01` được ghi tại `config/amendment_01_analysis_start.yaml`; SHA-256 của amendment ở sidecar `config/amendment_01_analysis_start.lock.json`. Sidecar cũng ghi hash `split.lock.json` đang hiệu lực: `cb6d983a9b32f43bfcbb671f7d71af1b012a70b8af999efbed3691ceb3e04440`.
- Split chính giữ nguyên: `N=180`, `L=7`, `W=180`, test T `[2025-10-22, 2026-04-20)`, `DATA_CUTOFF=2026-10-24` exclusive. Log truy cập vùng dành riêng chỉ có hai sự kiện `eligibility_count`; không ghi `label_load`. Metadata kho ghi `test_labels_loaded=false`. Test chưa mở.
- Dev hiệu dụng là 569 ngày (18 tháng 21 ngày), chứa một dịp Tết trọn vẹn. Kiểm tra khả thi cohort theo ngày, chưa tạo nhãn: `N=180,W=365` có 138 khách đủ điều kiện trước T đầu `2024-04-18`; `N=365,W=180` cũng có 138 khách trước T đầu `2024-04-18`; `N=365,W=90` có 925 trước T đầu `2024-07-17`. Các cửa sổ này vượt 30 khách theo sàn vận hành nhưng không bảo đảm lực thống kê. Kết hợp `N=365,W=365` bắt đầu `2023-10-16`, trước ngày cửa hàng mở, nên **không khả thi**; số khách đủ điều kiện trong phạm vi hiệu dụng là 0.
- **Lịch sử Ngày 1:** theo amendment 02, định nghĩa `total_price-total_discount` cho 701/6.400 đơn bất thường (10,95%), vượt cổng 5%. Chủ dự án sau đó ban hành amendment 03 theo nghiệp vụ; đây là lịch sử cổng cũ, không còn là quy tắc dừng đang hoạt động.
- **Cập nhật Ngày 2:** amendment 03 dùng `after_sub_discount-shipping_fee` cùng ngoại lệ đã khóa; audit mới có 22 đơn tặng và 2/6.400 đơn doanh thu âm (0,03%), dưới ngưỡng dừng 1%. Đã tạo đặc trưng, nhãn dev, phân khúc, phân loại và luật giỏ hàng; xem [day2_summary.md](day2_summary.md) và [money_audit.md](money_audit.md). Test chưa mở.
- Một phần đơn thiếu customer/product ID; các đơn đó không thể dùng ở mức khách hoặc giỏ hàng tương ứng. Mốc UTC được chuyển sang ngày `Asia/Ho_Chi_Minh` theo quyết định trước đó; bản đối chiếu dashboard độc lập chưa có trong repo.

## Việc chủ dự án cần làm

**Đã xác nhận:** chủ dự án đối chiếu số đơn theo trạng thái với dashboard Pancake; không có vấn đề.

**Điểm dừng ở cuối Ngày 1 (lịch sử):** cổng amendment 02 dừng phân tích. Amendment 03 đã thay quyết định này trước khi sinh nhãn; Ngày 2 hiện hoàn tất và điểm dừng hiện tại là chờ chủ dự án xem kết quả trước khi mở test.

`N` và `W` giữ nguyên theo config; `H_obs=[analysis_start,T)` hiện được ghi trong amendment 03 và [glossary.md](glossary.md).
