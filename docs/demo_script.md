# Kịch bản demo offline — 4 phút

## Chuẩn bị

1. Từ thư mục dự án chạy `.venv\Scripts\python -m streamlit run src/app/streamlit_app.py`.
2. Để toggle làm mới ở trạng thái tắt; dashboard chỉ đọc snapshot và không gọi API.
3. Chọn toàn bộ khoảng tháng, scheme K=2 và “Tất cả” phân khúc.
4. Nếu máy chiếu không có Python, mở các ảnh chụp thật trong `docs/demo_screens/` theo thứ tự bên dưới và dùng PDF slide in.

## Lời dẫn và thao tác

| Thời gian | Màn hình | Lời dẫn |
|---|---|---|
| 0:00–0:25 | Mở dashboard | “Đây là bản chạy offline từ snapshot đã khóa. Không có thông tin khách hàng và không có nút ghi dữ liệu lên API.” |
| 0:25–1:05 | Tab Tổng quan doanh số | Chọn khoảng tháng. Mặc định 2024-04–2026-04 gồm DEV và test, không chỉ DEV; tháng cuối chưa trọn. Đọc doanh thu ghi nhận và số đơn; UNKNOWN chiếm 91,92% doanh thu theo tỉnh/thành, nguyên nhân chưa phân tích. Không phân bổ doanh thu xuống từng sản phẩm. |
| 1:05–1:40 | Tab Phân khúc khách | Chọn K=2 rồi quy tắc nghiệp vụ. Giải thích nhóm doanh nghiệp là proxy; doanh thu test được trình bày tách khỏi RFM trước T. |
| 1:40–2:15 | Tab Combo gợi ý | Chỉ vào support, confidence, lift dev/test và giá niêm yết gộp. Nhắc đây là đồng xuất hiện, không phải nguyên nhân hay lợi nhuận. |
| 2:15–2:55 | Tab Chất lượng & kiểm toán | Nêu status, đơn quà, 903 dòng inferred_subset độ tin cậy thấp, snapshot và hash split. |
| 2:55–3:35 | Tab Mô hình mua lại | Nêu đúng hai tên mô hình: Logistic Regression C=10 — mô hình chính theo D-005; Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính. Amendment 05: cận dưới CI ROC-AUC > 0,55 và cận dưới CI ΔAP > 0. Nói: “Cấu hình ghi >T, evaluator dùng [T,end) (gồm ngày T); ảnh hưởng chưa xác định; đây là kết quả số liệu của lần chạy thực tế, không phải khẳng định tuân thủ đầy đủ giao thức, không gọi là 'đạt cổng ghi trước'.” Chênh lệch DEV/test chưa giải thích. |
| 3:35–4:00 | Chốt | Nhắc giới hạn một Tết, không có giá vốn, status hiện tại không phải lịch sử trạng thái; mời hỏi về kho và quyết định nghiệp vụ. |

## Kịch bản chụp ảnh màn hình dự phòng

Không cần quay video; dùng 5 ảnh dashboard đã chụp trực tiếp từ app offline trong `docs/demo_screens/` để dự phòng:

1. `01-overview.png`: tab tổng quan, toàn thời gian.
2. `02-segments.png`: K=2, bảng DEV và nhóm khách tại T.
3. `03-combos.png`: bảng combo với support/confidence/lift test.
4. `04-quality.png`: status, audit tiền và gift-line.
5. `05-model.png`: metric DEV/test cùng khoảng tin cậy và kết luận.

Chụp sau khi tắt sidebar debug, không mở raw, không hiện terminal có biến môi trường. Tên ảnh chỉ theo số thứ tự; không chụp thông tin khách/đơn.
