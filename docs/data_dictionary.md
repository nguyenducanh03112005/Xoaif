# Từ điển dữ liệu nguồn (bản đầu)

Nguồn phân tích hiện hành: snapshot local `20261024T052943Z`. Snapshot
`20261023T174441Z` đã bị thay thế; mọi số liệu 12.009 đơn từ snapshot cũ hết
hiệu lực. Đây là từ điển mức API, không phải schema DuckDB đã duyệt.
Schema inspector chỉ xuất tên trường/kiểu; raw JSON chứa dữ liệu nhạy cảm và
chỉ nằm trong `data/raw/`.

Phạm vi hành vi hiện hành được chủ dự án bổ sung ngày 2026-10-25: cửa hàng bắt
đầu hoạt động ngày `2024-04-01` theo giờ Việt Nam. Đơn có ngày địa phương trước
mốc này vẫn được giữ trong raw nhưng không vào phân tích hành vi/RFM/nhãn/giỏ
hàng/doanh thu ghi nhận. Quyết định nằm trong `config/amendment_01_analysis_start.yaml`;
không sửa split đã khóa.

| Trường/nhóm | Ý nghĩa dự kiến | Phân loại | Quyết định hiện tại |
| --- | --- | --- | --- |
| `id`, `shop_id`, `page_id`, `post_id`, `conversation_id`, `ad_id` | Mã bản ghi/nguồn liên kết | Định danh | Chỉ giữ trong raw restricted; HMAC khi tạo kho phân tích |
| `customer.customer_id`, `customer.id`, `customer.fb_id` | Mã khách/định danh mạng xã hội | Định danh cá nhân | HMAC theo namespace; không xuất shared |
| `bill_full_name`, `bill_phone_number`, `customer.name`, `customer.phone_numbers`, `customer.emails` | Thông tin liên hệ | PII trực tiếp | Không allowlist cho phân tích |
| `shipping_address`, `bill_email`, `customer.notes` | Địa chỉ, liên hệ, ghi chú khách | PII/văn bản tự do | Restricted; bỏ khỏi mô hình trừ khi được duyệt riêng |
| `note`, `note_print`, `order_link`, `payment_link`, `tracking_link` | Ghi chú hoặc đường dẫn cá nhân/đơn | Văn bản nhạy cảm/credential-bearing | Không allowlist; không gửi LLM ngoài |
| `inserted_at`, `updated_at` | Thời gian tạo/cập nhật đơn | Dữ liệu thời gian | Chủ dự án quyết định timestamp nguồn là UTC; chuyển sang `Asia/Ho_Chi_Minh` trước phép tính theo ngày. Quyết định dựa trên dashboard do chủ dự án mô tả; chưa có bản đối chiếu lưu trong repo. |
| `status`, `status_name` | Trạng thái đơn hiện tại | Dữ liệu vận hành | Theo quyết định chủ dự án: chỉ status `3` là mua hợp lệ; status `0`, `1`, `4`, `5`, `6` loại khỏi doanh thu ghi nhận, RFM, nhãn và basket. Mã ngoài danh sách phải báo và loại tạm thời. |
| `status_history[]` | Lịch sử trạng thái | Dữ liệu vận hành theo thời gian; có editor ID | Không dùng để tạo feature hoặc label theo quyết định chủ dự án. Các timestamp trùng và ngữ nghĩa chưa xác minh vẫn là hạn chế được ghi nhận. |
| `items[]`, `product_id`, `variation_id`, `quantity`, `return_quantity`, `returning_quantity` | Dòng hàng/sản phẩm/số lượng | Dữ liệu giao dịch; ID nhạy cảm | Basket chỉ dùng đơn status `3`, có ít nhất hai `product_id` khác nhau; gộp biến thể theo `product_id`. ID sản phẩm không đưa vào shared nếu chưa được duyệt. |
| `total_price`, `total_price_after_sub_discount`, `total_discount`, `shipping_fee`, `money_to_collect`, `cash`, `cod` | Giá trị/thu tiền/chiết khấu/phí | Dữ liệu kinh doanh nhạy cảm | Chưa được duyệt định nghĩa “doanh thu ghi nhận”; cần đối soát trường và hoàn tiền |
| `customer.order_count`, `customer.purchased_amount`, `customer.last_order_at` | Tổng hợp hồ sơ khách hiện tại | Trạng thái hiện tại, có nguy cơ leakage | Không dùng như feature lịch sử tại T |
| `last_editor`, `creator`, `warehouse_info`, `page`, `customer` | Thông tin tài khoản/người/kho/khách lồng | Có thể chứa PII | Không đưa nguyên object vào bảng phân tích |

Allowlist Ngày 1 chỉ giữ các trường cần để dựng kho và EDA phát triển: thời gian
tạo đơn, status hiện tại, order ID, customer ID và product ID. Các ID được HMAC
trong kho restricted. Chưa đưa số tiền, địa chỉ, ghi chú, thông tin khách hiện
tại, lịch sử trạng thái hoặc tên sản phẩm vào kho phân tích. Không suy đoán
endpoint sản phẩm, review, khách hàng hoặc tồn kho.

## Quy tắc do chủ dự án chốt — 24/10/2026

- Status hợp lệ theo chủ dự án: `0` mới; `1` đã xác nhận; `3` đã nhận; `4` đang
  hoàn; `5` đã hoàn; `6` đã hủy. Chỉ status hiện tại `3` được tính là mua hợp lệ.
- Trong snapshot `20261024T052943Z`, bảng code sinh
  `outputs/tables/status_counts.csv` ghi 2 đơn status `0`, 14 đơn status `1`,
  11.841 đơn status `3`, 1 đơn status `4`, 25 đơn status `5`, 128 đơn status
  `6`; không quan sát mã số khác hoặc status thiếu/không nguyên.
- Đây là bảng số lượng trạng thái hiện tại, không phải chỉ số tiền hay hành vi mua
  lại. Không dùng nó để kết luận về chất lượng mô hình.
