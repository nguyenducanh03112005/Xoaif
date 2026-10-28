# Ghi chú thuyết trình — Xoaif Garden

Kịch bản theo mạch: bài toán → dữ liệu → phương pháp → kết quả → demo → hỏi đáp. Trình bày kết quả đã có; không đưa lịch sử chỉnh sửa hoặc công việc ngoài phạm vi vào bài nói.

## 01 — Kho dữ liệu và khai phá dữ liệu bán hàng

Mở đầu: cửa hàng có dữ liệu giao dịch nhưng cần một cách đọc thống nhất để hiểu xu hướng, hành vi khách và sản phẩm thường mua cùng nhau. Dự án biến giao dịch thành các chỉ số và công cụ xem kết quả.

## 02 — Từ dữ liệu bán hàng đến câu trả lời kinh doanh

Đặt ba câu hỏi: doanh số thay đổi ra sao; khách hàng mua một lần hay quay lại; sản phẩm nào thường cùng xuất hiện trong giỏ. Mục tiêu là mô tả và hỗ trợ hình thành giả thuyết.

## 03 — Từ giao dịch đến phân tích và kết quả

Giải thích luồng: giao dịch → chuẩn hóa → đặc trưng → phân tích → dashboard/báo cáo. Công cụ chính: Python, Pandas, DuckDB, scikit-learn, mlxtend và Streamlit.

## 04 — Phạm vi dữ liệu phân tích

Nêu nguồn Pancake POS và khoảng giao dịch hợp lệ được dùng. Số đơn và số khách là hai đơn vị khác nhau; chỉ dùng giao dịch đáp ứng quy tắc nghiệp vụ.

## 05 — Từ dữ liệu nguồn đến kết quả phân tích

Giải thích dữ liệu giao dịch, khách và sản phẩm được chuẩn hóa, nối trong kho DuckDB, rồi tạo bảng tổng hợp cho dashboard. Không cần đi sâu cấu trúc thư mục.

## 06 — Giá trị khách hàng trong 180 ngày

Retention cho biết tỷ lệ khách quay lại theo định nghĩa cửa sổ 180 ngày. CLV trong dự án là doanh thu ghi nhận lịch sử 180 ngày đầu, không phải dự báo hay lợi nhuận.

## 07 — Phân khúc khách hàng theo RFM

RFM gồm Recency (lần mua gần nhất), Frequency (số lần mua) và Monetary (doanh thu ghi nhận). K-Means gom khách có đặc trưng gần nhau; kết quả chủ yếu tách mua một lần và mua lặp lại, dùng để mô tả hành vi.

## 08 — Xếp hạng khả năng mua lại

Tại mốc T, mô hình nhận đặc trưng tính từ lịch sử trước T và dự đoán khách có phát sinh giao dịch hợp lệ trong 180 ngày tiếp theo hay không. Logistic Regression tạo điểm xếp hạng; kết quả dùng để nghiên cứu, không phải quyết định tự động cho khách.

## 09 — Tạo đặc trưng và nhãn mua lại

Feature gồm độ gần lần mua, tần suất, doanh thu/giá trị đơn, số sản phẩm và nhịp mua. Nhãn được tạo từ giao dịch sau T theo cửa sổ 180 ngày và khoảng chờ trưởng thành. Đánh giá theo các mốc thời gian để giữ đúng thứ tự quá khứ–tương lai.

## 10 — Tìm sản phẩm thường xuất hiện cùng giỏ

FP-Growth tìm các tập sản phẩm phổ biến. Support là tỷ lệ giỏ có cặp; confidence là tỷ lệ giỏ có B trong các giỏ có A; lift so sánh đồng xuất hiện với mức nền. Đây là liên hệ thống kê, không chứng minh món này gây ra món kia.

## 11 — Các cặp sản phẩm gợi ý cách kết hợp

Trình bày các cặp được giữ qua các lần phân tích ổn định. Kết quả có thể gợi ý bundle hoặc cách trưng bày để thử nghiệm; chưa diễn giải thành lợi nhuận.

## 12 — Dashboard kết quả phân tích

Dashboard có các trang tổng quan, phân khúc, combo, chất lượng dữ liệu và mô hình. Nêu rõ từng tab trả lời câu hỏi nào.

## 13 — Sản phẩm dự án

Tóm tắt đầu ra: kho phân tích, kết quả doanh số/khách/giỏ hàng, mô hình thử nghiệm, dashboard, báo cáo và slide. Tập trung vào kết quả người dùng có thể đọc được.

## 14 — Demo dashboard

Trình tự: tổng quan doanh số → phân khúc khách → combo. Với mỗi tab, chỉ ra bộ lọc, chỉ số và cách diễn giải. Có thể mở tab mô hình nếu giảng viên hỏi về ML.

## 15 — Kết luận

Dự án đã chuyển dữ liệu giao dịch thành các phân tích mô tả và công cụ trình bày. Mô hình mua lại và các cặp sản phẩm là đầu vào tham khảo; quyết định kinh doanh cần được xác nhận bằng dữ liệu và thử nghiệm phù hợp. Mời giảng viên hỏi đáp.
