# Kịch bản demo offline — 4 phút

## Chuẩn bị

1. Từ thư mục dự án chạy `.venv\Scripts\python -m streamlit run src/app/streamlit_app.py`.
2. Để toggle làm mới ở trạng thái tắt; dashboard chỉ đọc snapshot và không gọi API.
3. Chọn toàn bộ khoảng tháng, scheme K=2 và “Tất cả” phân khúc.
4. Nếu máy chiếu không có Python, dùng các ảnh chụp các tab còn lại trong `docs/demo_screens/` cùng PDF slide in; tổng quan và các giới hạn được ghi trong slide để tránh dùng ảnh tỉnh/thành cũ.

## Lời dẫn và thao tác

| Thời gian | Màn hình | Lời dẫn |
|---|---|---|
| 0:00–0:25 | Mở dashboard | “Đây là bản chạy offline từ snapshot đã khóa. Không có thông tin khách hàng và không có nút ghi dữ liệu lên API.” |
| 0:25–1:05 | Tab Tổng quan doanh số | Chọn khoảng tháng. Mặc định 2024-04–2026-04 gồm DEV và test, không chỉ DEV; tháng cuối chưa trọn. Đọc doanh thu ghi nhận và số đơn. Không hiển thị so sánh theo tỉnh/thành vì 91,92% doanh thu mang nhãn UNKNOWN; nguyên nhân chưa phân tích. Không phân bổ doanh thu xuống từng sản phẩm. |
| 1:05–1:40 | Tab Phân khúc khách | Chọn K=2 rồi quy tắc nghiệp vụ. Nêu rõ K=2 chủ yếu tách khách mua một lần khỏi khách mua lặp lại; chưa chứng minh ý nghĩa kinh doanh. Giải thích nhóm doanh nghiệp là proxy; doanh thu test được trình bày tách khỏi RFM trước T. |
| 1:40–2:15 | Tab Combo gợi ý | Chỉ vào support, confidence, lift dev/test và giá niêm yết gộp. Nhắc đây là đồng xuất hiện, không phải nguyên nhân hay lợi nhuận. |
| 2:15–2:55 | Tab Chất lượng & kiểm toán | Nêu status, đơn quà, 903 dòng inferred_subset độ tin cậy thấp, snapshot và hash split. |
| 2:55–3:35 | Tab Mô hình mua lại | Nêu ROC-AUC DEV C=10 khoảng 0,51, gần ngẫu nhiên; test khoảng 0,70 là tín hiệu yếu mà DEV chưa xác nhận, không kết luận mô hình tốt. Test đã mở, không tinh chỉnh trên test. Nêu hai vai trò mô hình và caveat ngày T nguyên văn: “Cấu hình ghi >T, evaluator dùng [T,end) (gồm ngày T); ảnh hưởng chưa xác định; đây là kết quả số liệu của lần chạy thực tế, không phải khẳng định tuân thủ đầy đủ giao thức, không gọi là 'đạt cổng ghi trước'.” |
| 3:35–4:00 | Chốt | Nêu bài phân loại phản hồi bị bỏ qua vì thiếu dữ liệu có nhãn; nhắc giới hạn một Tết, không có giá vốn, status hiện tại không phải lịch sử trạng thái; mời hỏi về kho và quyết định nghiệp vụ. |

## Kịch bản chụp ảnh màn hình dự phòng

Không cần quay video; dùng ảnh dashboard đã chụp trực tiếp từ app offline trong `docs/demo_screens/` và slide PDF để dự phòng:

1. `02-segments.png`: K=2, bảng DEV và nhóm khách tại T.
2. `03-combos.png`: bảng combo với support/confidence/lift test.
3. `04-quality.png`: status, audit tiền và gift-line.
4. `05-model.png`: metric DEV/test cùng khoảng tin cậy và kết luận.

Chụp sau khi tắt sidebar debug, không mở raw, không hiện terminal có biến môi trường. Tên ảnh chỉ theo số thứ tự; không chụp thông tin khách/đơn.
