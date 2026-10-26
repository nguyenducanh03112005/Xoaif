# CP1: duyệt tính khả thi và thiết kế

**[LỊCH SỬ — rà soát ngày 25/10/2026, trước khi mở test]** Split đã khóa theo quyết định chủ dự án. Trạng thái hiện hành được cập nhật tại `docs/PROGRESS.md`.
Snapshot `20261024T052943Z` là nguồn duy nhất cho phân tích mới. Snapshot ban đầu
`20261023T174441Z` có một trang không còn khớp checksum; toàn bộ số liệu 12.009
đơn của snapshot đó đã hết hiệu lực và chỉ còn được giữ như lịch sử kiểm tra.
Chưa nạp nhãn test.

## Snapshot ban đầu 20261023T174441Z (lịch sử; không dùng cho phân tích mới)

- Snapshot local gồm 12.009 đơn trên 601 trang. `total_entries`, tổng số dòng,
  số trang, ID duy nhất và SHA-256 từng trang đều khớp manifest.
- Timestamp `inserted_at` có thể parse trong khoảng 2022-06-04 đến 2026-10-23
  nếu tạm coi chuỗi không múi giờ là UTC. Cả 12.009 `inserted_at` và
  `updated_at`, cùng 34.687 timestamp trạng thái, đều không có timezone offset;
  vì vậy đây chưa phải khoảng thời gian đã xác nhận theo giờ địa phương.
- 11.997 đơn có ít nhất một dòng hàng; có 51.002 dòng hàng. 50.043 dòng có
  `product_id` và `variation_id`. 11.667 đơn có `customer.customer_id`.
- 12.009 đơn có `status_history` không rỗng, với 34.687 event có timestamp
  parse được. Trong 9.611 đơn, timestamp tăng theo danh sách; 2.398 đơn có
  cùng một timestamp cho mọi event. Không event timestamp nào có offset.
- Status ở event có timestamp lớn nhất khớp status hiện tại ở 9.612 đơn; status
  của phần tử cuối danh sách khớp status hiện tại ở 12.005 đơn. `order.updated_at`
  muộn hơn timestamp trạng thái lớn nhất ở cả 12.009 đơn. Các dấu hiệu này cần
  được giải thích trước khi dựng nhãn quá khứ.

## Kết quả feasibility trước EDA phát triển

Trên snapshot mới, đã tạo bảng đếm status hiện tại, báo cáo DQ và hồ sơ khả thi.
Trước khi đếm eligibility đã ghi ngưỡng tối thiểu 30 khách duy nhất vào split.
Không mở/đọc nhãn: trước amendment ngày mở cửa hàng, tại ngày bắt đầu ứng viên
`2025-10-22`, N=180 có 5.499 khách đủ điều kiện; tại ứng viên `2025-04-20`,
N=365 có 3.931. Đây là số feasibility lịch sử theo phạm vi cũ, không dùng làm
cohort hiệu dụng sau amendment. Hai số dùng ngày bắt đầu khác nhau, nên không
phải so sánh cùng một cohort.

## Quyết định cần chốt tại CP1 (trạng thái ban đầu; xem cập nhật bên dưới)

1. Xác nhận timezone của các chuỗi thời gian Pancake không có offset, hoặc cung
   cấp căn cứ chính thức để chuyển về `Asia/Ho_Chi_Minh`.
2. Xác nhận cách hiểu `status_history`: thứ tự phần tử, ý nghĩa `updated_at`,
   nguyên nhân nhiều event có cùng timestamp, và liệu lịch sử có đầy đủ trước
   thời điểm bắt đầu snapshot. Nếu chưa xác minh được, giới hạn bài toán A ở
   phân khúc RFM mô tả.
3. Duyệt đơn mua hợp lệ và xử lý huỷ/hoàn/hoàn một phần; Pancake docs nói status
   16 là đã thu tiền, còn status 3 chỉ là đã nhận hàng.
4. Trước khi xem hành vi, chốt tập `N_candidates`, `L_candidates` và `W` theo
   ngày lịch; sau đó ghi hash vào `config/split.yaml`. Chưa tự điền ngày vì SLA
   đối soát và chu kỳ mua của cửa hàng chưa được xác nhận.
5. Duyệt quy tắc giỏ hàng (đơn nào được đưa vào, cách xử lý trả/đổi) và cách gọi
   chỉ số tiền. Chưa có giá vốn/tồn kho nên chưa tính chỉ số chi phí hoặc chênh lệch.
6. Xác nhận deadline, thời lượng thuyết trình, rubric chính thức, thành viên,
   và thời hạn lưu/xoá raw ở CP2. Mặc định tài liệu tiếng Việt.
7. Chọn có dùng Olist minh hoạ riêng hay bỏ; không trộn Olist vào kết luận Xoaif.
8. Duyệt phạm vi văn bản khách và nhà cung cấp LLM trước khi mở nhánh C. Hiện
   chưa gọi endpoint review/hội thoại hoặc gửi dữ liệu văn bản ra ngoài.

## Nguyên tắc tiếp tục

Sau khi CP1 được duyệt, tạo run mới với cấu hình và snapshot hash đã khoá; chỉ
EDA phát triển trước `test_start`. Nếu lịch sử trạng thái không đạt yêu cầu,
giữ RFM mô tả và luật kết hợp có giới hạn; không mở test để cố tạo kết quả dự
đoán.

## Cập nhật CP1 từ chủ dự án — 24/10/2026

- **Timezone:** quyết định coi timestamp nguồn là UTC và đổi sang
  `Asia/Ho_Chi_Minh` (+7) trước phân tích theo ngày. Đây là quyết định của chủ
  dự án dựa trên đối chiếu dashboard; repo chưa lưu bản đối chiếu độc lập.
- **Đơn hợp lệ:** chỉ trạng thái hiện tại `3` được tính là mua hợp lệ; trạng
  thái `0`, `1`, `4`, `5`, `6` bị loại. Mã khác phải báo số lượng, mặc định loại
  và chờ chủ dự án. Snapshot mới không có mã ngoài danh sách này.
- **Lịch sử trạng thái:** không dùng `status_history` làm feature hoặc label;
  tie timestamp vẫn được ghi là hạn chế dữ liệu.
- **N/L/W (đã chốt):** `N=180`, `L=7`, `W=180` là kỳ chính;
  `test_start=2025-10-22`, `test_end_exclusive=2026-04-20`. `N=365`, `W=90` và
  `W=365` chỉ là độ nhạy trên tập phát triển. `config/split.yaml` đã khóa; hash
  snapshot và config nằm trong split YAML và sidecar lock.
- **Basket / tiền:** chỉ đơn trạng thái `3`, ít nhất hai sản phẩm khác nhau,
  gộp biến thể theo `product_id`; chỉ dùng tên “doanh thu ghi nhận” sau khi chủ
  dự án duyệt định nghĩa.
- **Phạm vi khác:** Olist bỏ; nhánh văn bản/LLM hoãn, chỉ cho phép đếm cục bộ
  trường văn bản/số bản ghi nếu được duyệt; raw xóa sau buổi bảo vệ và giữ bản
  đã ẩn danh.
- **Bảo vệ API:** khóa GET-only, allowlist đường dẫn và quét mã nguồn đã thêm;
  kết quả chạy ghi trong `docs/PROGRESS.md`.

## Amendment ngày mở cửa hàng — 25/10/2026

- Chủ dự án xác nhận hoạt động kinh doanh bắt đầu `2024-04-01` giờ Việt Nam.
  Các đơn trước mốc được giữ trong raw nhưng loại khỏi phân tích hành vi/RFM,
  nhãn, basket và “doanh thu ghi nhận”.
- Amendment riêng: `config/amendment_01_analysis_start.yaml`; SHA-256
  `23da1216cf06c32003d52eb7831ed528dc4a4259d3480a9e3025fcb394100cfd`.
  Hash hiện hành của `split.lock.json` ghi trong amendment sidecar là
  `cb6d983a9b32f43bfcbb671f7d71af1b012a70b8af999efbed3691ceb3e04440`.
- Không sửa `config/split.yaml`: N=180, L=7, W=180, test T
  `[2025-10-22, 2026-04-20)` giữ nguyên. Nhật ký vùng dành riêng chỉ có
  `eligibility_count`, không có `label_load`; metadata kho xác nhận
  `test_labels_loaded=false`.
- Kho dev hiệu dụng sau amendment có 6.517 đơn, 6.400 status 3 và 5.174 khách
  có đơn status 3. Số preflight 5.499/3.931 ở trên được giữ làm lịch sử, không
  đại diện phạm vi kinh doanh mới.
- Một số bullet trong yêu cầu mới gọi N là cửa sổ quan sát đặc trưng và W là
  cửa sổ nhãn; cấu hình/protocol đã khóa định nghĩa N là chân trời nhãn, W là
  độ dài cửa sổ T. Giữ nguyên nghĩa của split trong Day 1; cần xác nhận thuật
  ngữ trước khi bước sang modeling.

## Hạn chế mùa vụ

Nhãn quay lại 180 ngày (`N=180`) có thể đánh giá thấp khách quay lại chủ yếu vào
dịp lễ theo chu kỳ khoảng một năm. `N=365` là độ nhạy nhãn trên tập phát triển;
`W=365` là độ nhạy độ dài cửa sổ đánh giá trên phát triển, không làm thay đổi
horizon nhãn. Không mở thêm test. EDA phát triển hiệu dụng chỉ dùng ngày địa
phương từ `analysis_start=2024-04-01` đến trước `test_start`.
