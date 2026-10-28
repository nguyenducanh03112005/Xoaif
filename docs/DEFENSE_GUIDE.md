# Hướng dẫn demo và vấn đáp — Xoaif Garden

## Thông điệp chính

Dự án biến dữ liệu bán hàng thành kho phân tích, các chỉ số về doanh số và khách hàng, phân khúc RFM, phân tích sản phẩm thường mua cùng nhau, thử nghiệm mô hình mua lại, dashboard và báo cáo. Kết quả mô tả dữ liệu hiện có; không tự khẳng định tác động kinh doanh.

## Kịch bản trình bày 10–12 phút

1. **Bài toán:** cửa hàng cần hiểu xu hướng bán hàng, hành vi mua lại và quan hệ giữa sản phẩm.
2. **Hướng giải quyết:** lấy giao dịch, chuẩn hóa quy tắc ngày/tiền/trạng thái, tạo kho và đặc trưng, chạy phân tích, trình bày bằng dashboard.
3. **Dữ liệu:** Pancake POS gồm đơn hàng, dòng sản phẩm và thông tin khách. Mỗi kết quả dùng phạm vi giao dịch phù hợp; không đồng nhất số đơn với số khách.
4. **Công nghệ:** Python, Pandas cho xử lý; DuckDB cho truy vấn/kho cục bộ; scikit-learn cho K-Means và Logistic Regression; mlxtend cho FP-Growth; Streamlit/Plotly cho dashboard; Matplotlib/ReportLab cho báo cáo.
5. **Kết quả:** doanh số và giá trị khách theo thời gian; phân khúc mô tả RFM; các cặp thường xuất hiện cùng giỏ; mô hình mua lại được đánh giá theo thời gian.
6. **Demo:** tổng quan → phân khúc → combo. Mở tab mô hình khi giảng viên muốn xem cách ML được dùng.
7. **Kết luận:** đây là công cụ hiểu dữ liệu và hình thành giả thuyết. Hiệu quả hành động cần xác nhận riêng.

## Demo dashboard (3 phút)

- **Tổng quan:** lọc thời gian, đọc doanh thu ghi nhận và số đơn; nói rõ đây không phải lợi nhuận.
- **Phân khúc khách:** giải thích RFM và nhóm mua một lần/mua lặp lại.
- **Combo:** cho xem cặp sản phẩm và giải thích support, confidence, lift.
- **Mô hình (nếu được hỏi):** mô tả đầu vào, nhãn, cách chia theo thời gian và vai trò tham khảo.

Mở sẵn dashboard trước buổi trình bày. Nếu không thao tác được, chuyển sang hình dashboard trong slide.

## ML trong dự án

### K-Means — phân khúc không giám sát

**Bài toán:** khám phá nhóm khách có hành vi tương tự khi chưa có nhãn nhóm từ trước.

**Đặc trưng:** RFM — số ngày từ lần mua gần nhất (Recency), số lần mua (Frequency), doanh thu ghi nhận (Monetary). Các biến được chuẩn hóa để thang đo doanh thu không lấn át hai biến còn lại.

**Cách chạy:** K-Means khởi tạo K tâm cụm, gán mỗi khách vào tâm gần nhất theo khoảng cách trong không gian đặc trưng, cập nhật tâm bằng trung bình rồi lặp đến khi ổn định. K=2 trong dự án chủ yếu phân biệt khách mua một lần và khách mua lặp lại. Đây là mô tả hình học, không phải nhãn VIP/churn.

### Logistic Regression — phân loại/xếp hạng mua lại

**Bài toán:** tại thời điểm T, ước lượng khách có mua lại trong 180 ngày kế tiếp hay không. Mỗi dòng huấn luyện là khách tại một mốc thời gian.

**Nhãn:** 1 nếu có giao dịch hợp lệ trong cửa sổ sau T; 0 nếu không có. Khoảng chờ L=7 ngày giúp nhãn đủ trưởng thành. Nhãn được suy ra theo quy tắc giao dịch, không phải người gán tay.

**Đặc trưng:** Recency, Frequency, Monetary/doanh thu, giá trị đơn trung bình/lớn nhất, số lượng và độ đa dạng sản phẩm, khoảng cách giữa các lần mua, đặc trưng tháng/mùa và chỉ báo thiếu lịch sử. Mọi biến tại T chỉ được tính từ dữ liệu trước T. Khi được hỏi danh sách đầy đủ, cần nói rõ phiên bản mô hình đã khóa còn một biến phân loại tỉnh/thành lấy từ hồ sơ giao dịch; phần thuyết trình không trình bày phân tích địa lý.

**Cách hoạt động:** mô hình học trọng số cho các đặc trưng và dùng hàm logistic để chuyển tổng trọng số thành xác suất từ 0 đến 1. Hệ số cho biết chiều liên hệ trong mô hình khi các biến khác giữ nguyên; không chứng minh nguyên nhân. Ngưỡng 0,5 biến xác suất thành nhãn, còn điểm liên tục có thể dùng để xếp hạng.

**Đánh giá:** chia theo thời gian, so với baseline và chú ý Average Precision/precision/recall vì nhãn dương hiếm. Logistic Regression được giữ làm mô hình chính theo kế hoạch; cây quyết định và Random Forest là mô hình đối chiếu. Cây quyết định chia dữ liệu bằng các điều kiện dạng if/else; dễ giải thích nhưng cây sâu dễ học thuộc dữ liệu. Cây độ sâu 8 được so sánh; cây nông độ sâu 3, tối thiểu 50 mẫu mỗi lá được khảo sát như baseline, không thay mô hình chính.

### FP-Growth — luật kết hợp giỏ hàng

Không phải mô hình phân loại. Thuật toán nén các giỏ thành FP-tree để tìm tập sản phẩm thường xuất hiện cùng nhau, sau đó tạo luật A→B.

- **Support:** tỷ lệ giỏ chứa A và B.
- **Confidence:** tỷ lệ giỏ có B trong số giỏ có A.
- **Lift:** confidence chia cho tỷ lệ nền của B. Lift lớn hơn 1 cho thấy đồng xuất hiện cao hơn mức độc lập thống kê, không chứng minh nhân quả.

## Câu hỏi giảng viên có thể hỏi

**Vì sao chọn DuckDB thay Spark?** Quy mô hiện tại phù hợp phân tích một máy; DuckDB hỗ trợ SQL và xử lý cột hiệu quả mà không cần cụm phân tán.

**Data lấy từ đâu và gồm gì?** Pancake POS: đơn, dòng hàng, sản phẩm và thông tin khách. Các bảng được nối theo khóa nghiệp vụ và chuẩn hóa trước khi phân tích.

**Data được lưu thế nào?** Snapshot nguồn lưu cục bộ; dữ liệu phân tích nạp vào DuckDB; bảng tổng hợp được xuất cho dashboard. Mẫu CSV trong dự án là dữ liệu giả lập để minh họa cấu trúc.

**Doanh thu có phải lợi nhuận?** Không. Là doanh thu ghi nhận theo quy tắc nghiệp vụ đã xác nhận; không có đủ giá vốn và chi phí để tính lợi nhuận.

**Vì sao dùng RFM?** Ba biến dễ giải thích và gắn trực tiếp với hành vi mua: gần đây, thường xuyên và giá trị. RFM hỗ trợ mô tả khách trước khi đặt giả thuyết hành động.

**K-Means có gán nhãn sẵn không?** Không. Thuật toán tự gom theo khoảng cách đặc trưng; nhóm chỉ được đặt tên sau khi xem hành vi trung bình/đặc trưng của cụm.

**Tại sao nhãn mua lại như vậy?** Giao dịch tương lai là outcome quan sát được cho câu hỏi mua lại. Cửa sổ 180 ngày thống nhất chân trời dự đoán; nhãn là proxy theo trạng thái giao dịch.

**Có rò rỉ tương lai không?** Feature tại từng mốc chỉ dùng lịch sử trước mốc đó; tập đánh giá được sắp theo thời gian. Nhãn chỉ dùng giao dịch sau mốc để chấm.

**Tại sao chọn Logistic Regression?** Là baseline phân loại dễ giải thích, cho điểm xác suất và phù hợp dữ liệu bảng. Kế hoạch chọn mô hình không chỉ dựa một metric; kết quả cần được đọc cùng baseline và đánh giá theo thời gian.

**Mô hình dự đoán tốt đến đâu?** Nếu được hỏi trực tiếp, trả lời thẳng: ROC-AUC OOF của mô hình chính trên DEV là 0,5096, gần mức ngẫu nhiên nên development chưa xác nhận khả năng xếp hạng ổn định. Test một lần cho ROC-AUC 0,7024 và AP 0,123, nhưng không nên lấy riêng kết quả này để kết luận mô hình tốt; test không dùng để tinh chỉnh. Cấu hình mốc ngày và evaluator có khác biệt ở ngày biên, nên diễn giải test cần nêu rõ giới hạn.

**Cây quyết định hoạt động thế nào?** Tìm ngưỡng chia một đặc trưng để các nhánh thuần nhãn hơn. Lặp việc chia tạo các luật if/else. Giới hạn độ sâu và số mẫu lá giúp giảm overfit; cây dễ trình bày nhưng không mặc nhiên tốt hơn.

**Nếu bỏ biến tỉnh/thành thì điểm mô hình hiện tại còn đúng không?** Không thể khẳng định. Điểm hiện có thuộc phiên bản mô hình đã khóa, có dùng biến phân loại tỉnh/thành. Muốn bỏ biến này phải tạo phiên bản feature mới và đánh giá lại trên DEV; kết quả test cũ không đại diện cho phiên bản mới.

**Vì sao không dùng accuracy?** Khi đa số khách không mua lại, đoán tất cả là không mua vẫn có accuracy cao. Average Precision và precision/recall cho biết chất lượng nhận diện lớp dương rõ hơn.

**FP-Growth nói được điều gì?** Sản phẩm nào thường cùng xuất hiện trong các giỏ đủ điều kiện. Không nói được món nào gây ra món kia, cũng không cho biết lợi nhuận.

**Lift lớn hơn 1 có nghĩa combo tốt?** Chỉ là đồng xuất hiện cao hơn mức nền. Cần xem số giỏ, confidence, tồn kho, giá vốn và kiểm chứng bằng thử nghiệm trước khi khuyến nghị.

**Hạn chế chính?** Kết quả phụ thuộc vào chất lượng và khoảng thời gian dữ liệu; nhãn mua lại là proxy nghiệp vụ; mô hình chưa thay thế quyết định kinh doanh; luật kết hợp không chứng minh nhân quả; chưa có giá vốn để kết luận lợi nhuận.

## Câu kết

“Dự án đã xây dựng được quy trình từ dữ liệu bán hàng đến phân tích và dashboard. RFM giúp mô tả nhóm khách, FP-Growth tìm sản phẩm thường cùng giỏ, còn Logistic Regression thử xếp hạng khả năng mua lại theo thời gian. Các kết quả giúp đặt câu hỏi và tạo giả thuyết; hiệu quả kinh doanh cần được xác nhận bằng dữ liệu và thử nghiệm tiếp theo.”
