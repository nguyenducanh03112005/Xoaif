# Thiết kế OLAP/DSS — Kho DEV

**Nhãn:** khám phá, chưa xác nhận ngoài mẫu. Giao thức A4: `docs/analysis_plan_wp_olap.md`; SHA-256 `170b6f74f7d60ee43e3da2132b2869aef59ddd33122abd9c90bd2d3374a0c745`. Nguồn thực thi: `scripts/build_dss_cuboids_dev.py`. Tài liệu ánh xạ môn học: `docs/course_alignment.md`.

## Lược đồ và lớp ngữ nghĩa

Kho vật lý DuckDB có sáu bảng: `fact_orders`, `fact_order_items`, `dim_date`, `dim_order_status`, `dim_customer`, `dim_product`. Fact giữ order key HMAC, customer key HMAC, ngày địa phương, status và số sản phẩm phân biệt; fact dòng hàng giữ product key HMAC. Lược đồ vật lý không bị sửa.

Các thuộc tính tiền, quà, kênh và tỉnh chưa có trong fact. Vì vậy script mở DuckDB **read-only**, dùng loader có date gate DEV status 3 để tạo bảng enrichment tạm trong RAM, nối với kho bằng order key HMAC. Nối 6.400/6.400 đơn status 3, đối chiếu ngày và customer key, sau đó xóa khóa khỏi mọi bảng aggregate. Lớp tạm không ghi ra DuckDB hay file.

Không có nhãn nhóm sản phẩm trong `dim_product`; product key là HMAC nên không dùng làm chiều kinh doanh. Thay vào đó cuboid dùng cỡ giỏ (số product ID distinct sau loại dòng quà). Đây là chiều có thể giải thích từ schema hiện tại, không phải nhóm ngành hàng.

## Câu hỏi quyết định → KPI → chiều và cuboid

| Câu hỏi cửa hàng | KPI mô tả | Chiều/độ đo trong kho và lớp ngữ nghĩa | Cuboid / nguồn | Cách đọc |
|---|---|---|---|---|
| Tháng nào và kênh nào ghi nhận đơn/doanh thu ở nhóm khách nào? | Số đơn, khách distinct, doanh thu ghi nhận | Tháng (`dim_date`), kênh đã chuẩn hóa, nhóm RFM A1; số đơn status 3 không quà | `outputs/tables/cube_month_channel_segment_dev.csv` | Slice theo tháng; dice tháng × kênh; suppression khi đơn hoặc khách <30. |
| Đóng góp đơn/doanh thu đến từ giỏ cỡ nào theo nhóm khách? | Số đơn, khách distinct, doanh thu ghi nhận | Tháng, basket size `0–1/2/3+`, nhóm RFM A1 | `outputs/tables/cube_month_basket_segment_dev.csv` | Roll-up cỡ giỏ hoặc tháng; không chia doanh thu xuống từng sản phẩm. |
| Dữ liệu địa lý đủ để định tuyến hàng/giao nhận chưa? | Số đơn, khách distinct, doanh thu ghi nhận, tỷ trọng đơn | Tỉnh/thành chuẩn hóa; nhóm tỉnh n<30 được gộp; UNKNOWN riêng | `outputs/tables/cube_province_dev.csv` | Không dùng làm ước lượng tiềm năng thị trường; suppression theo đơn/khách. |
| Bao nhiêu đơn và khách theo trạng thái/tháng? | Số đơn, khách có khóa | Tháng, `status_code` từ `fact_orders` | `outputs/tables/cube_month_status_dev.csv` | Status ngoài 3 không gán doanh thu; measure revenue để trống. |

Doanh thu là doanh thu ghi nhận theo `docs/money_definition.md`, không phải lãi hay lợi nhuận. Khách distinct là measure không cộng được qua tháng: một khách có thể xuất hiện ở nhiều tháng; khi roll-up phải tính lại `COUNT DISTINCT`, không cộng số khách tháng.

## Phép OLAP có thể lặp lại

Hàm `olap_operation()` trong script nhận các order facts tạm trong RAM; nó lọc chiều trước khi nhóm, chạy aggregate và áp suppression cuối cùng.

- **Roll-up:** tháng → quý/năm hoặc cỡ giỏ → tổng. Thực thi trên DEV: 2 nhóm năm, 7 nhóm quý, 19 nhóm tháng; tổng order count đối soát giữa các mức.
- **Drill-down:** năm → quý → tháng; measures tính lại từ order facts thay vì cộng distinct-customer counts.
- **Slice:** chọn tháng 2024-04, trả 9 nhóm kênh × RFM trước suppression.
- **Dice:** chọn tháng 2024-04 và Facebook, trả 4 nhóm RFM trước suppression.
- **Pivot:** đổi trục tháng × kênh cho một lát cắt RFM; kết quả mẫu có 3 cột gồm trục tháng và hai nhóm kênh hiện diện.

Các phép này là query trên facts đã kiểm tra, không phải tổng hợp từ bảng đã suppression. Đầu ra phát hành mới được che sau khi thao tác, tránh cộng các ô đã ẩn.

## Nhật ký thực thi

Lần chạy thử đầu tiên tạo cuboid tạm nhưng `run_all.py` chặn tại seal vì loader dùng cho join đang có một chỉnh sửa tạm; thay đổi đó đã được gỡ bỏ. Bản tạm không được dùng làm deliverable và được tạo lại bằng hàm date-gated riêng trong A4, giữ nguyên loader đã khóa. Lần tái tạo không thay đổi cohort, công thức hay cuboid đã đăng ký; metadata và bảng đang được rà soát là đầu ra cuối.

## Kết quả kiểm soát và giới hạn

- Warehouse có 6.517 đơn trong DEV; 6.400 status 3 được ghép với loader. Sau loại 22 quà cấp đơn còn 6.378 đơn và 5.169 khách có khóa.
- Tỉnh/thành UNKNOWN: 5.840/6.378 đơn (91,56%); trường tỉnh có giá trị 538/6.378 đơn (8,44%). Các nhóm tỉnh nhỏ được gộp; cuboid còn Hà Nội 506 đơn, nhóm tỉnh khác (32 đơn) và UNKNOWN 5.840 đơn. Dữ liệu tỉnh quá thiếu để quyết định thị trường địa lý.
- Kênh có mặt ở 3.996/6.378 đơn (62,64%); “Instagram + nguồn hiếm” là nhóm gộp, không diễn giải nguồn riêng.
- Ngưỡng suppression 30. Cuboid tháng × kênh × RFM có 195 ô, 143 ô ẩn; tháng × cỡ giỏ × RFM có 198 ô, 156 ô ẩn; tháng × status có 41 ô, 22 ô ẩn. Chỉ xuất bảng aggregate, không có HMAC key hay PII.
- Phân khúc RFM dùng đúng quy tắc A1 đã đăng ký, p90 M=830.000₫; không đổi phân đoạn theo kết quả A4. Kho vật lý được mở read-only và không sửa.
- Nhãn sản phẩm, trạng thái tồn kho, giá vốn, chiến dịch và lý do hủy không đủ trong kho hiện hành. Không suy ra lợi nhuận, nguyên nhân hay quyết định đặt hàng tự động.
