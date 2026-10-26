# Rà soát rò rỉ — dự đoán hủy/hoàn (Day 2B)

## Phạm vi và quyết định

Phạm vi chỉ status 3/5/6 có `inserted_at` địa phương trong `[2024-04-01, 2025-10-22)`. Nhãn status 5/6 so với status 3 không tặng; loại status 0/1/4 và status-3 quà. Kết quả gate: **skipped_preregistered_positive_support_gate**; số model attempt: 0. Fold dương: F1: 30 / 1330, F2: 13 / 801, F3: 6 / 920, F4: 1 / 726, F5: 18 / 1007. At least one temporal validation fold has fewer than 20 positive status-5/6 orders or lacks both classes in its training data.

## Đặc trưng được đăng ký

Chưa fit mô hình. Bộ feature dự kiến được khóa trước: số product_id phân biệt; `total_price` theo trường đơn; `order_sources_name` nếu có; province; tháng tạo; trạng thái khách mới/cũ từ status-3 không tặng trước thời điểm đơn.

`total_price` và channel chỉ có phiên bản snapshot; nguồn không cung cấp lịch sử trường để xác nhận chúng chưa đổi sau tạo đơn. Đây là giới hạn dữ liệu. Khóa khách và product chỉ dùng HMAC trong bộ nhớ/đầu ra kiểm soát; không được đưa làm predictor.

## Trường bị loại

- `status_history`, `updated_at`: cập nhật sau tạo đơn; `status` chỉ làm nhãn.
- `cash`, `cod`, `prepaid`, `transfer_money`, `money_to_collect` và mọi trường thanh toán: không phải thông tin ổn định tại thời điểm tạo, đã bị cấm trong amendment 04.
- Tên, điện thoại, địa chỉ chi tiết, order/customer/product ID, free text và mọi trường sau tạo: định danh, dữ liệu nhạy cảm hoặc rò rỉ tương lai.
- Discount ratio và nhóm sản phẩm không nằm trong feature list đã đăng ký cho task này.

Không truy vấn nhãn/hành vi test. Báo cáo này không đánh giá nguyên nhân hủy/hoàn và không dùng làm quyết định tự động.
