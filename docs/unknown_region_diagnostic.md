# Chẩn đoán nhãn UNKNOWN theo nguồn

**Kết luận: chưa xác định.** Kho DEV restricted đã kiểm tra chỉ có các cột khách, ngày, trạng thái, sản phẩm và chỉ tiêu đơn; không có trường nguồn, kênh đặt hàng, loại đơn, địa chỉ giao hàng hoặc trường province. Do đó không thể phân rã aggregate doanh thu/đơn `UNKNOWN` theo các trường yêu cầu.

Không đọc raw để bổ sung trường và không suy diễn rằng thiếu địa chỉ giao hàng là nguyên nhân. Tỷ lệ UNKNOWN 91,92% chỉ được giữ như một giới hạn đã biết; chưa thể kết luận nó tập trung ở kênh hay loại đơn nào.
