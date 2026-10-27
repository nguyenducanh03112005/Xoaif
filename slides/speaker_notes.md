# Ghi chú thuyết trình — Xoaif Garden

## Mục đích và cách dùng

Tài liệu này giúp hai thành viên trình bày thống nhất với bộ slide, số liệu aggregate và giới hạn đã ghi trong hồ sơ. Khi cần số chưa nhớ, mở đúng nguồn được ghi ở từng slide; không ước lượng và không đọc dữ liệu khách hoặc đơn từng dòng.

## Phân vai gợi ý

| Slide | Người trình bày | Vai trò phối hợp |
|---|---|---|
| 1 | A | Mở mục tiêu dự án |
| 2 | A | B bổ sung quy mô snapshot |
| 3 | A | B giải thích schema |
| 4 | B | A bổ sung mốc lọc và nhãn |
| 5 | A | B nêu quy tắc nghiệp vụ tiền |
| 6 | B | A giải thích giới hạn diễn giải |
| 7 | B | A bổ sung ảnh hưởng tới giỏ hàng |
| 8 | A | Giải thích cách đánh giá |
| 9 | A | B xác nhận lịch sử quyết định |
| 10 | A | B nêu provenance |
| 11 | B | A nhấn mạnh giới hạn nhãn |
| 12 | B | A nhấn mạnh đồng xuất hiện, không nhân quả |
| 13 | Cả hai | A thao tác dashboard; B dẫn lời theo kịch bản demo |
| 14 | B | A bổ sung phần mô hình và test |
| 15 | B | A bổ sung chu kỳ refresh và ranh giới dữ liệu |

Thời lượng và rubric chính thức chưa có trong hồ sơ. Tổng thời lượng đề xuất khoảng 14 phút 30–40 giây, gồm demo 4 phút ở slide 13 và thêm 30–40 giây cho slide 15; slide 6 và 7 có thể rút gọn nếu bị giới hạn thời gian.

## Slide 1 — Mở đầu

### Người trình bày và thời lượng
A — khoảng 1 phút.

### Thông điệp một câu
Dự án xây kho dữ liệu bán hàng có thể kiểm tra và trình bày kết quả khai phá cùng giới hạn của chúng.

### Lời thoại
Đây là dự án xây kho dữ liệu bán hàng và dùng kho đó để mô tả hành vi mua. Snapshot hiện hành có 12.011 đơn trên 601 trang, nhưng không phải mọi đơn đều thuộc cùng khoảng phân tích. Chúng tôi trình bày kết quả cùng provenance, cohort và giới hạn dữ liệu. Phần mở đầu sẽ đi từ câu hỏi dự án sang cách dữ liệu được xử lý.

### Số cần nhớ
- 12.011 đơn; 601 trang — docs/canonical_numbers.md, docs/api_notes.md.

### Giới hạn phải nói
Snapshot là đầu vào đã khóa; không đồng nghĩa mọi đơn được dùng trong mọi phân tích. Không hứa kết quả về lợi nhuận hay tác động kinh doanh.

### Câu hỏi dễ gặp
- Dự án giải quyết việc gì? — Xây kho dữ liệu bán hàng và dùng phân khúc, dự đoán mua lại, luật kết hợp; mở README.md.
- Vì sao phải nêu giới hạn ngay từ đầu? — Vì các kết quả phụ thuộc cohort và định nghĩa nghiệp vụ; mở docs/final_consistency_report.md.

### Chuyển slide
Trước khi nói về kết quả, tôi sẽ nêu rõ ba câu hỏi và phạm vi dữ liệu.

## Slide 2 — Câu hỏi và phạm vi

### Người trình bày và thời lượng
A — khoảng 1 phút; B bổ sung quy mô snapshot.

### Thông điệp một câu
Ba câu hỏi là mô tả dữ liệu, đánh giá tín hiệu mua lại và tìm sản phẩm thường đồng xuất hiện trong giỏ.

### Lời thoại
Dự án trả lời ba câu hỏi: dữ liệu mô tả ra sao, có tín hiệu xếp hạng mua lại hay không, và sản phẩm nào thường đồng xuất hiện. Snapshot có 12.011 đơn, kho DEV có 6.517 đơn, còn cohort scoring có 5.169 khách. Đây là đơn vị và điều kiện khác nhau, nên các số không thể tráo đổi. Kết quả không chứng minh lợi nhuận, hiệu quả can thiệp hay quan hệ nhân quả.

### Số cần nhớ
- Snapshot: 12.011 đơn/601 trang; DEV: 6.517 đơn; cohort scoring: 5.169 khách — docs/canonical_numbers.md.
- Ba câu hỏi và giới hạn suy luận — slides/xoaif_print.pdf, README.md.

### Giới hạn phải nói
Không gộp số đơn với số khách. Cohort scoring là cohort có điều kiện trước T, không phải toàn bộ khách trong snapshot.

### Câu hỏi dễ gặp
- Vì sao không dùng accuracy làm kết luận chính? — Lớp dương hiếm nên cần xem metric xếp hạng và precision/recall; mở docs/metric_rationale.md.
- Test có được mở nhiều lần để cải thiện không? — Không, test đã mở một lần; mở docs/test_report.md.

### Chuyển slide
Tiếp theo là luồng dữ liệu từ snapshot đến sản phẩm phân tích offline.

## Slide 3 — Kiến trúc dữ liệu

### Người trình bày và thời lượng
A — khoảng 1 phút; B bổ sung schema.

### Thông điệp một câu
Luồng năm tầng đưa dữ liệu từ nguồn đọc-only qua snapshot, ETL và kho đến dashboard/PDF aggregate.

### Lời thoại
Kiến trúc gồm năm tầng: thu nhận, snapshot, bảo vệ và ETL, kho và khai phá, rồi trình bày. Dashboard đọc CSV/JSON aggregate tại chỗ và không gọi Pancake API. Kho DEV tổ chức fact đơn, fact dòng hàng cùng các dimension cần cho truy vấn. Giới hạn là sản phẩm trình bày chỉ phản ánh các aggregate đã tạo, không cho phép suy ra dữ liệu chi tiết từng khách.

### Số cần nhớ
- Năm tầng; các bảng fact/dimension — slides/xoaif_print.pdf, docs/architecture_matrix.md, docs/data_dictionary.md.
- Dashboard có 5 tab — docs/canonical_numbers.md, src/app/streamlit_app.py.

### Giới hạn phải nói
Client API chỉ đọc; dashboard không gửi yêu cầu ghi hay cần API để xem aggregate đã lưu. Không đọc dữ liệu từng dòng khi bảo vệ.

### Câu hỏi dễ gặp
- Kho có các bảng nào? — Fact đơn, fact dòng hàng và dimension khách/ngày/trạng thái/sản phẩm; mở docs/data_dictionary.md.
- Dashboard lấy dữ liệu từ đâu? — Từ CSV/JSON aggregate cục bộ; mở src/app/streamlit_app.py.

### Chuyển slide
Sau kiến trúc, cần phân biệt các mốc thời gian và cohort trước khi diễn giải kết quả.

## Slide 4 — Mốc thời gian và cohort

### Người trình bày và thời lượng
B — khoảng 1 phút; A bổ sung mốc lọc và nhãn.

### Thông điệp một câu
Cầu khách 5.499 → 5.174 → 5.169 đã được đếm trực tiếp theo điều kiện pre-analysis-only và gift-only, dư 0.

### Lời thoại
Mốc phân tích DEV bắt đầu ngày 2024-04-01 và kết thúc trước T là 2025-10-22. Cầu khách đã được đếm trực tiếp: 5.499 khách status 3 có ID trước T, trừ 325 khách chỉ có status 3 trước analysis_start, còn 5.174 khách DEV; trừ 5 khách chỉ có đơn quà, còn 5.169 scoring. Phần dư chưa giải thích: 0. Trong nhóm 325, toàn bộ 325 có ít nhất một đơn trong 476 đơn bán thử ngày 2022-06-04 đến 2022-09-21. Cửa sổ test thực thi gồm ngày T; sai khác với quy tắc ghi trước sẽ được giải thích ở slide 10. Nguồn: docs/cohort_reconciliation.md.

### Số cần nhớ
- DEV: 6.517 đơn, gồm 6.400 đơn status 3; preflight: 5.499 khách; DEV status 3: 5.174 khách; scoring: 5.169 khách — docs/canonical_numbers.md.
- DEV có 3.508 mẫu nhãn qua nhiều mốc T và 260 dương — docs/canonical_numbers.md.
- Cửa sổ thực thi [2025-10-22, 2026-04-20) — outputs/metrics/test_eval.json.

### Giới hạn phải nói
Đây là đếm HMAC trong RAM trên snapshot, chỉ xét đơn có local date trước T; không in/lưu ID. A−B gồm 325 khách chỉ có đơn status 3 trước 2024-04-01 và cả 325 đều có ít nhất một đơn trong 476 đơn bán thử. Phần dư của cầu bằng 0. Cửa sổ test có ngày T; ảnh hưởng sai khác giao thức chưa xác định.

### Câu hỏi dễ gặp
- Vì sao giữ 476 đơn trước analysis_start nhưng loại khỏi phân tích? — Đó là giai đoạn bán thử theo hồ sơ; mở docs/cohort_definitions.md.
- Ba cohort 5.499/5.174/5.169 liên hệ thế nào? — 5.499 − 325 khách chỉ có status 3 trước 2024-04-01 (cả 325 thuộc nhóm có đơn trong 476 đơn bán thử) = 5.174 − 5 khách chỉ có đơn quà theo Amendment 03 = 5.169; dư 0. Đây là đếm HMAC trong RAM trên snapshot, chỉ đơn local date < T. Nguồn: docs/cohort_reconciliation.md, outputs/tables/cohort_bridge_verified.json.

### Chuyển slide
Khi đã rõ mẫu số, slide kế tiếp giải thích quy tắc chất lượng dữ liệu và doanh thu ghi nhận.

## Slide 5 — Chất lượng dữ liệu và quy tắc tiền

### Người trình bày và thời lượng
A — khoảng 1 phút; B nêu quy tắc nghiệp vụ.

### Thông điệp một câu
Status 3 là quy ước nghiệp vụ để tính doanh thu ghi nhận, với các giới hạn về mã khách và lịch sử trạng thái.

### Lời thoại
Chúng tôi dùng status 3 theo xác nhận nghiệp vụ của chủ cửa hàng để xác định đơn hợp lệ và doanh thu ghi nhận. Trong 6.400 đơn status 3 ở DEV, có 286 đơn thiếu mã khách và 22 đơn quà cấp đơn. Có 2 đơn doanh thu âm, tương đương 0,03%, thấp hơn cổng dừng 1%. Doanh thu ghi nhận không phải lợi nhuận hay đối soát ngân hàng, và status hiện tại không phải lịch sử chuyển trạng thái.

### Số cần nhớ
- 6.400 đơn status 3; 286 thiếu mã khách; 22 đơn quà; 2/6.400 đơn doanh thu âm (0,03%) — docs/canonical_numbers.md.
- Cổng dừng âm: 1%; công thức và Amendment 03 — docs/money_definition.md, docs/money_audit.md.

### Giới hạn phải nói
Gọi đúng là “doanh thu ghi nhận”. Không gọi là lợi nhuận hoặc đối soát ngân hàng; không suy diễn trạng thái lịch sử từ status hiện tại.

### Câu hỏi dễ gặp
- Vì sao status 3 được tính? — Chủ cửa hàng xác nhận đó là đơn đã nhận/ghi nhận; đây không phải kiểm toán ngân hàng. Mở docs/money_definition.md.
- price_adjustment có nghĩa gì? — Chênh giữa doanh thu ghi nhận và giá sau giảm theo định nghĩa; có thể phản ánh phí hoặc ưu đãi. Mở docs/money_definition.md.

### Chuyển slide
Từ chất lượng và định nghĩa tiền, chúng ta chuyển sang mô tả dữ liệu DEV.

## Slide 6 — EDA trên DEV

### Người trình bày và thời lượng
B — khoảng 1 phút; có thể rút gọn khi thiếu thời gian. A nhấn mạnh giới hạn diễn giải.

### Thông điệp một câu
EDA cho thấy phần lớn khách status 3 DEV chỉ có một đơn, nhưng biểu đồ chỉ mô tả dữ liệu quan sát.

### Lời thoại
Trong DEV, 4.526 trên 5.174 khách status 3 có một đơn, tương đương 87,5%. Vì vậy, biểu đồ tần suất mô tả một nhóm khách mua lặp lại nhỏ hơn trong cohort này. Tháng 10/2025 chỉ có dữ liệu đến ngày 21. Không gọi biến động theo tháng là mùa vụ hay nguyên nhân.

### Số cần nhớ
- 4.526/5.174 khách có một đơn, 87,5% — docs/canonical_numbers.md.
- DEV kết thúc trước 2025-10-22 — docs/canonical_numbers.md, outputs/metrics/eda_dev_summary.json.

### Giới hạn phải nói
Đây là mô tả DEV, không phải kiểm định mùa vụ hay bằng chứng về nguyên nhân hành vi. Tháng cuối chưa trọn.

### Câu hỏi dễ gặp
- Dữ liệu có chứng minh mùa vụ không? — Không; DEV có một mùa Tết trọn vẹn và biểu đồ không kiểm định nguyên nhân. Mở docs/metric_rationale.md.
- Vì sao không so sánh doanh thu theo tỉnh? — 91,92% doanh thu UNKNOWN trên phạm vi dashboard DEV+test; DEV riêng là 91,56% đơn và 90,73% doanh thu trong nhóm thiếu tỉnh. Mở docs/unknown_region_diagnostic.md.

### Chuyển slide
Một quyết định ảnh hưởng trực tiếp đến giỏ là cách nhận diện quà theo từng dòng hàng.

## Slide 7 — Phân loại dòng quà

### Người trình bày và thời lượng
B — khoảng 1 phút; có thể rút gọn khi thiếu thời gian. A bổ sung ảnh hưởng đến giỏ.

### Thông điệp một câu
Dòng quà được nhận diện theo quy tắc đã khóa; phần suy luận subset sum có độ tin cậy thấp.

### Lời thoại
Trong 30.049 dòng DEV được khảo sát, có 4 dòng direct zero-price và 903 dòng inferred subset. Nhóm 24 cặp chính được giữ khi ổn định ở ít nhất 4/6 ô nhạy cảm và có mặt tại ô chính. Quy tắc không dùng tên sản phẩm để gán nhãn quà. Phần suy luận có thể gán nhầm vì chưa xác minh thủ công từng dòng.

### Số cần nhớ
- 30.049 dòng DEV; 4 direct zero-price; 903 inferred subset — docs/canonical_numbers.md.
- 24 cặp chính, điều kiện ít nhất 4/6 ô — docs/canonical_numbers.md, outputs/metrics/day3_combo_prereg.json.

### Giới hạn phải nói
903 dòng inferred subset có độ tin cậy thấp. Không coi đây là nhãn được xác minh thủ công; không suy luận từ tên hàng hay support của cặp.

### Câu hỏi dễ gặp
- Vì sao không gắn quà theo tên sản phẩm? — Cùng một sản phẩm có thể bán thật hoặc được tặng tùy đơn; mở docs/decisions.md.
- Subset sum đáng tin đến đâu? — Có thể gán nhầm và cần xác nhận trước quyết định vận hành; mở docs/qa.md, outputs/metrics/day3_gift_field_survey.json.

### Chuyển slide
Sau quy tắc giỏ hàng, phần tiếp theo mô tả cách đánh giá bài toán mua lại.

## Slide 8 — Phương pháp supervised

### Người trình bày và thời lượng
A — khoảng 1 phút.

### Thông điệp một câu
Đánh giá mua lại dùng đặc trưng trước T, nhãn N=180 và validation theo thời gian để hạn chế rò rỉ.

### Lời thoại
Đặc trưng được tạo từ dữ liệu trước T, còn nhãn xem có mua lại trong N=180 ngày hay không. DEV có 3.508 mẫu nhãn qua nhiều mốc T, trong đó 260 là dương, tương đương 7,41%. Vì lớp dương hiếm, accuracy đơn lẻ không đủ để mô tả chất lượng xếp hạng. Chúng tôi xem ROC-AUC và AP cùng baseline, rồi mới đọc precision, recall và confusion matrix tại ngưỡng đã khóa.

### Số cần nhớ
- N=180; DEV: 3.508 mẫu nhãn qua nhiều mốc T, 260 dương, 7,41% — docs/canonical_numbers.md, outputs/metrics/day2_label_audit.json.
- Validation temporal expanding 5 folds; ngưỡng 0,5 — docs/metric_rationale.md, outputs/metrics/dev_final_model.json.

### Giới hạn phải nói
Metric phụ thuộc cohort và cách chia theo thời gian. Không dùng accuracy để kết luận khi lớp dương hiếm, và không tối ưu ngưỡng trên test.

### Câu hỏi dễ gặp
- Vì sao chia theo thời gian? — Đặc trưng chỉ dùng lịch sử trước T, nhãn ở sau T; mở docs/qa.md.
- Vì sao OOF có 1.558 mẫu? — Các mốc đầu không đủ khoảng đệm; chỉ cohort hợp lệ được giữ. Mở docs/qa.md.

### Chuyển slide
Slide kế tiếp phân biệt vai trò mô hình đã chọn với khảo sát bổ sung.

## Slide 9 — Vai trò mô hình

### Người trình bày và thời lượng
A — khoảng 1 phút; B xác nhận lịch sử quyết định.

### Thông điệp một câu
Mô hình chính theo quyết định D-005 và mô hình khảo sát bổ sung được giữ thành hai vai trò riêng.

### Lời thoại
Logistic Regression C=10 — mô hình chính theo D-005. Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính. DEV OOF của mô hình chính có ROC-AUC 0,5096, gần ngẫu nhiên; feature-v2 có 0,4969. Vì development chưa xác nhận tín hiệu xếp hạng rõ, ROC-AUC test khoảng 0,70 chỉ được gọi là tín hiệu yếu chưa được DEV xác nhận.

### Số cần nhớ
- C=10 DEV OOF: ROC-AUC 0,5096; AP 0,0699 — docs/canonical_numbers.md, outputs/metrics/dev_final_model.json.
- Feature-v2 DEV OOF: ROC-AUC 0,4969; AP 0,0645 — docs/canonical_numbers.md, outputs/metrics/dev_final_models_v2.json.

### Giới hạn phải nói
Không nói mô hình tốt, hiệu quả hoặc chính xác. Không dùng test để tinh chỉnh, đổi ngưỡng hay chọn lại mô hình.

### Câu hỏi dễ gặp
- Vì sao có hai mô hình? — C=10 giữ vai trò chính theo D-005; feature-v2 là khảo sát bổ sung theo Amendment 04. Mở docs/decisions.md.
- DEV OOF nói gì? — C=10 gần ngẫu nhiên, còn development chưa xác nhận tín hiệu rõ. Mở docs/test_report.md.

### Chuyển slide
Bây giờ là kết quả aggregate của lần mở test duy nhất, cùng caveat về ranh giới ngày.

## Slide 10 — Đánh giá test một lần

### Người trình bày và thời lượng
A — khoảng 1 phút; B nêu provenance.

### Thông điệp một câu
Kết quả test là mô tả lần chạy thực tế và phải đọc cùng sai khác giữa quy tắc ghi trước với cửa sổ evaluator.

### Lời thoại
Đây là kết quả aggregate của lần mở test duy nhất, không phải căn cứ để chọn lại mô hình. Cohort có 5.169 khách và 237 dương; ROC-AUC của Logistic Regression C=10 là 0,7024 với CI 95% từ 0,6651 đến 0,7365. Con số này là tín hiệu yếu chưa được DEV xác nhận, vì DEV OOF C=10 là 0,5096 gần ngẫu nhiên. Cấu hình ghi >T, evaluator dùng [T,end) (gồm ngày T); ảnh hưởng chưa xác định; đây là kết quả số liệu của lần chạy thực tế, không phải khẳng định tuân thủ đầy đủ giao thức, không gọi là 'đạt cổng ghi trước'.

### Số cần nhớ
- Test: 5.169 khách, 237 dương (4,59%); C=10 ROC-AUC 0,7024, CI 0,6651–0,7365 — docs/canonical_numbers.md, outputs/metrics/test_eval.json.
- DEV OOF C=10: ROC-AUC 0,5096 — docs/canonical_numbers.md.
- Cửa sổ thực thi và sai khác giao thức — docs/test_provenance_note.md, docs/test_report.md.

### Giới hạn phải nói
Dùng nguyên văn caveat trong lời thoại. Không gọi đây là “đạt cổng ghi trước”, không tuyên bố tuân thủ đầy đủ, không chạy lại evaluator hoặc dùng test để tinh chỉnh.

### Câu hỏi dễ gặp
- Kết quả test có chứng minh mô hình tốt không? — Không; DEV OOF gần ngẫu nhiên nên tín hiệu test chưa được development xác nhận. Mở docs/test_report.md.
- Ngày T có được tính không? — Có trong lần chạy thực tế [T,end); ảnh hưởng của sai khác với quy tắc >T chưa xác định. Mở docs/test_provenance_note.md.

### Chuyển slide
Sau kết quả mua lại, slide tiếp theo quay về phân khúc như mô tả lịch sử trước T.

## Slide 11 — Phân khúc RFM

### Người trình bày và thời lượng
B — khoảng 1 phút; A nhấn mạnh giới hạn nhãn.

### Thông điệp một câu
K=2 là phân đoạn mô tả theo tần suất mua (một lần / lặp lại) trong hồ sơ trước T, không phải nhãn về hành vi tương lai.

### Lời thoại
K-Means K=2 là phân đoạn mô tả theo tần suất mua (một lần / lặp lại) với silhouette 0,508. Trong cohort scoring, 4.530 trên 5.169 khách có một đơn, tương đương 87,6%; nhóm proxy giá trị lớn có 62 khách. RFM mô tả lịch sử trước T chứ không dự báo tình trạng tương lai. Proxy giá trị lớn không xác minh pháp nhân và chưa chứng minh ý nghĩa kinh doanh của các nhóm.

### Số cần nhớ
- K=2, silhouette 0,508 — docs/canonical_numbers.md, outputs/metrics/day2_segmentation.json.
- Một đơn: 4.530/5.169 khách (87,6%); proxy giá trị lớn: 62/5.169 — docs/canonical_numbers.md, outputs/metrics/day2_label_audit.json.

### Giới hạn phải nói
Không gọi proxy là pháp nhân đã xác minh. Không fit lại trên test; metric so sánh bằng 0 phát sinh từ cùng profile trước T, không chứng minh ổn định tương lai.

### Câu hỏi dễ gặp
- K=2 có nghĩa là hai phân khúc kinh doanh khác nhau không? — Chưa chứng minh; phân đoạn mô tả theo tần suất mua (một lần / lặp lại). Mở docs/test_report.md.
- Proxy giá trị lớn có phải nhãn doanh nghiệp thật không? — Không, đây là proxy theo phân vị DEV. Mở docs/qa.md.

### Chuyển slide
Từ phân khúc khách hàng, chúng ta chuyển sang các cặp sản phẩm đồng xuất hiện.

## Slide 12 — Luật kết hợp và combo

### Người trình bày và thời lượng
B — khoảng 1 phút; A nhấn mạnh giới hạn nhân quả.

### Thông điệp một câu
Các luật chỉ mô tả đồng xuất hiện của những cặp đã freeze trước khi mở test.

### Lời thoại
Nhóm đã freeze 24 cặp và chấm trên 2.174 giỏ test đủ điều kiện. Trong số đó, 21 cặp có lift lớn hơn 1. Support, confidence và lift chỉ mô tả đồng xuất hiện trong giỏ. Không có giá vốn và không phân bổ chiết khấu xuống từng sản phẩm, nên không kết luận lợi nhuận hay tác động nhân quả.

### Số cần nhớ
- 24 cặp; 21/24 có lift > 1; 2.174 giỏ đủ điều kiện — docs/canonical_numbers.md, outputs/metrics/test_eval.json.
- Tiêu chí freeze ít nhất 4/6 ô nhạy cảm — outputs/metrics/day3_combo_prereg.json.

### Giới hạn phải nói
Không nói bán kèm sẽ tăng doanh thu. Không tìm luật mới trên test; không tính lợi nhuận khi thiếu giá vốn và phân bổ giảm giá.

### Câu hỏi dễ gặp
- Lift > 1 chứng minh bán kèm hiệu quả không? — Không; đây là đồng xuất hiện, không phải quan hệ nhân quả. Mở docs/qa.md.
- Vì sao chỉ chấm cặp đã freeze? — Để không chọn luật mới từ test đã mở. Mở docs/test_report.md.

### Chuyển slide
Tiếp theo là demo cách xem các kết quả aggregate trong dashboard offline.

## Slide 13 — Dashboard demo

### Người trình bày và thời lượng
A thao tác, B dẫn lời — khoảng 4 phút trong phần trình bày.

### Thông điệp một câu
Dashboard đọc aggregate cục bộ qua năm tab và không cần gọi API.

### Lời thoại
Đây là dashboard offline với năm tab; A sẽ thao tác và B dẫn lời. Kịch bản demo đi qua tổng quan, phân khúc, combo, chất lượng và mô hình trong khoảng 4 phút. Trên bảng địa lý, 91,92% doanh thu mang nhãn UNKNOWN nên chúng tôi không so sánh địa bàn. Dashboard không hiển thị dữ liệu khách hay đơn từng dòng và bài phân loại phản hồi bị bỏ qua vì thiếu dữ liệu có nhãn.

### Số cần nhớ
- 5 tab, 10 CSV aggregate và 6 JSON aggregate — docs/canonical_numbers.md, scripts/dashboard_smoke.py.
- 91,92% doanh thu tỉnh/thành là UNKNOWN — docs/canonical_numbers.md.
- Kịch bản demo 4 phút — docs/demo_script.md.

### Giới hạn phải nói
Khoảng mặc định gồm DEV và cửa sổ test; tháng cuối chưa trọn. Không so sánh địa bàn, không phân bổ doanh thu xuống sản phẩm, không tinh chỉnh theo test. Giữ toggle làm mới ở trạng thái tắt.

### Câu hỏi dễ gặp
- Dashboard có gọi API không? — Không, chỉ đọc aggregate cục bộ; mở docs/demo_script.md.
- Vì sao bỏ bài phân loại phản hồi? — Thiếu dữ liệu có nhãn đủ tin cậy để huấn luyện và kiểm định. Mở docs/test_report.md.

### Chuyển slide
Cuối cùng, chúng tôi chốt những giới hạn còn lại và cách chuẩn bị cho phần hỏi đáp.

## Slide 14 — Giới hạn và chuẩn bị

### Người trình bày và thời lượng
B — khoảng 1 phút; A bổ sung phần mô hình/test.

### Thông điệp một câu
Câu trả lời bảo vệ cần nêu được điều dữ liệu cho phép nói và điều còn chưa được xác minh.

### Lời thoại
Các giới hạn chính là một mùa Tết trọn vẹn trong DEV, tỷ lệ UNKNOWN cao trên bảng địa lý và 903 dòng inferred subset có thể gán nhầm. Cầu cohort đã khớp bằng đếm trực tiếp; kết quả test vẫn có sai khác ranh giới ngày đã công khai. Hạn nộp là 2026-10-27, còn thời lượng và rubric chính thức chưa có trong hồ sơ. Hai thành viên sẽ tập trả lời chéo và giữ nguyên ranh giới test đã khóa.

### Số cần nhớ
- 91,92% UNKNOWN trên dashboard DEV+test; DEV thiếu tỉnh 91,56% đơn/90,73% doanh thu; 903 inferred subset — docs/canonical_numbers.md, docs/unknown_region_diagnostic.md.
- Hạn nộp 2026-10-27; rubric và thời lượng chính thức chưa có — docs/qa_roles.md, docs/schedule.md.

### Giới hạn phải nói
Không tuyên bố tổng quát hóa từ một cửa sổ test; không khẳng định lợi nhuận, nhân quả hoặc trạng thái lịch sử. Không chạy lại evaluator hay notebook để chuẩn bị.

### Câu hỏi dễ gặp
- Những việc nào cần xác nhận với giảng viên? — Thời lượng và rubric chính thức; mở docs/schedule.md.
- Nếu không nhớ số liệu thì làm gì? — Mở docs/qa.md hoặc metric aggregate tương ứng, không ước lượng.

### Chuyển slide
Xin mời hội đồng đặt câu hỏi; người phụ trách trả lời trước và người còn lại bổ sung khi cần.

## Lỗi hay mắc, tuyệt đối tránh

- Không nói mô hình tốt, hiệu quả hoặc chính xác chỉ vì ROC-AUC test khoảng 0,70; dùng câu “tín hiệu yếu chưa được DEV xác nhận” và nhắc DEV OOF khoảng 0,51, gần ngẫu nhiên.
- Giữ nguyên hai tên vai trò: “Logistic Regression C=10 — mô hình chính theo D-005”; “Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính”.
- Khi nói về test, dùng nguyên văn: “Cấu hình ghi >T, evaluator dùng [T,end) (gồm ngày T); ảnh hưởng chưa xác định; đây là kết quả số liệu của lần chạy thực tế, không phải khẳng định tuân thủ đầy đủ giao thức, không gọi là 'đạt cổng ghi trước'.”
- Gọi là doanh thu ghi nhận theo status 3 và Amendment 03; không gọi là lợi nhuận hoặc đối soát ngân hàng.
- Chỉ gọi luật kết hợp là đồng xuất hiện; không nói combo có lợi nhuận hay làm tăng doanh thu.
- Trình bày cầu 5.499 → 5.174 → 5.169 với điều kiện và số đếm trực tiếp; không so sánh địa bàn khi 91,92% dashboard là UNKNOWN.

## Slide 15 — Vận hành: làm mới dữ liệu

**Thời lượng đề xuất:** 30–40 giây. **Người dẫn:** B.

Chu kỳ đề xuất là snapshot mới mỗi tuần. Mỗi snapshot có timestamp và manifest/checksum; giữ snapshot cũ và so sánh tổng đơn cùng số đơn có đổi trạng thái. Huấn luyện lại tách riêng, theo tháng hoặc khi đủ dữ liệu; cần rolling-origin và amendment mới, không mở lại test cũ.

API cho phép lấy đơn mới nên gần real-time khả thi; nhóm chọn snapshot bất biến để tái lập; chưa khảo sát lọc theo thời gian cập nhật; chưa tự động hóa trong bản nộp. API không có snapshot token, status hiện tại không phải lịch sử trạng thái, split/test/cohort khóa bằng hash và mô hình chưa có tín hiệu xác nhận.

- Ước lượng theo bảng tháng: khoảng 2024-04-01 đến 2026-04-19 (ngày cuối tính được; tháng cuối chưa trọn), 749 ngày; công thức `9.104 đơn status 3 không quà / 749 ngày = 12,15`, xấp xỉ 12,2 đơn/ngày. Đây là tốc độ của giai đoạn dashboard, không phải trung bình toàn snapshot. Nguồn: `outputs/tables/dashboard_sales_monthly.csv`, `docs/canonical_numbers.md`.
- Nguồn: `docs/refresh_procedure.md`, `docs/canonical_numbers.md`.
- Không gọi proxy giá trị lớn là pháp nhân đã xác minh; RFM chỉ mô tả lịch sử trước T.
- Nêu rõ test đã mở một lần; không đề nghị chạy lại evaluator, notebook hay tinh chỉnh trên test.
- Không gán nhãn phản hồi khi chưa có dữ liệu đủ tin cậy.

## Checklist trước giờ bảo vệ

- Thử máy chiếu, âm thanh và mở sẵn file slides/xoaif_print.pdf.
- Mở dashboard từ thư mục dự án bằng .venv\Scripts\python -m streamlit run src/app/streamlit_app.py; giữ thao tác làm mới ở trạng thái tắt.
- Chuẩn bị ảnh dự phòng trong docs/demo_screens/ nếu máy chiếu không có Python.
- Cả hai tập demo 4 phút theo docs/demo_script.md và tập trả lời ít nhất 10 câu thuộc phần của người kia theo docs/qa_roles.md.
- Kiểm tra README, PDF và ảnh không để lộ thông tin khách hoặc đơn từng dòng; không mở raw hay terminal có biến môi trường.
