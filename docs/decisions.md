# Nhật ký quyết định

## D-001 — Mốc bắt đầu phân tích hành vi

- **Ngày:** 2026-10-25
- **Người quyết định:** Chủ dự án
- **Quyết định:** Cửa hàng bắt đầu kinh doanh từ 2024-04-01 theo giờ Việt Nam. Các đơn có `inserted_at` trước mốc thuộc giai đoạn bán thử đầu tiên và bị loại khỏi mọi phân tích hành vi, RFM, nhãn, giỏ hàng và “doanh thu ghi nhận”. Raw không bị xóa.
- **Lý do:** Giai đoạn 2022-06 đến 2022-09 có các đơn trước khi cửa hàng hoạt động; khoảng 2022-10 đến 2024-03 không có đơn. Ngày mở là thông tin nghiệp vụ của chủ dự án.
- **Phạm vi:** Ghi tại `config/amendment_01_analysis_start.yaml`; hash amendment và hash split lock được ghi trong sidecar `config/amendment_01_analysis_start.lock.json`. Không sửa `config/split.yaml`.
- **Split giữ nguyên:** `N=180`, `L=7`, `W=180`; test T `[2025-10-22, 2026-04-20)`; `DATA_CUTOFF=2026-10-24` exclusive.
- **Thời điểm:** Quyết định được ghi trước khi nạp nhãn test hoặc mở test. Nhật ký vùng dành riêng chỉ ghi `eligibility_count`; kho ghi `test_labels_loaded=false`.
- **Hệ quả:** Kho dev dựng lại chỉ gồm `[2024-04-01, 2025-10-22)`. Thời gian hiệu dụng 569 ngày, xấp xỉ 18 tháng và chứa một chu kỳ Tết trọn vẹn.

## D-002 — Doanh thu ghi nhận, đơn tặng và bất thường tiền

> **Lịch sử:** D-002 được thay thế về quy tắc tiền bởi D-004/amendment 03 trước khi sinh nhãn hoặc mô hình Ngày 2. Giữ lại mục này để giải thích cổng 5% trước đây.

- **Ngày:** 2026-10-25
- **Người quyết định:** Chủ dự án/chủ cửa hàng
- **Quyết định:** `revenue_recognized = total_price - total_discount`, không gồm ship; chỉ status `3`, từ `analysis_start` đến trước `test_start`. Không dùng các trường thanh toán của app làm bằng chứng đã thu tiền. Định nghĩa đầy đủ và xử lý ngoại lệ nằm trong `docs/money_definition.md` và `config/amendment_02_money_and_gift_rules.yaml`.
- **Bằng chứng tiền:** Chủ dự án rà mẫu 13 đơn; công thức `after_sub_discount = total_price - total_discount + shipping_fee` khớp 12/13 và `total_price` khớp tổng `variation_info.retail_price × quantity` 13/13. Cột dashboard trong mẫu chưa điền; chủ cửa hàng xác nhận đơn tại quầy thu tiền mặt nhưng thao tác app thời gian đầu không đáng tin. Không coi đây là đối soát thanh toán độc lập.
- **Đơn tặng:** `total_price-total_discount == 0` hoặc `total_price == 0` và `after_sub_discount == 0`; giữ trong raw, đếm riêng, loại khỏi R/F/Monetary/nhãn/giỏ hàng/doanh thu.
- **Đơn bất thường:** sai đồng nhất sau-giảm-cộng-ship, `total_price=0` nhưng after dương, `cod<0`, hoặc `total_discount<0`. Loại khỏi doanh thu/Monetary chính; độ nhạy dùng `after_sub_discount-shipping_fee`, vẫn loại quà. Nếu tỷ lệ hợp vượt 5% số status 3 dev thì dừng phân tích.
- **Trạng thái đơn:** Chủ dự án đã đối chiếu số lượng theo status với Pancake, không có vấn đề.
- **Thời điểm và kiểm chứng:** Trước khi ghi quyết định, `outputs/logs/reserved_access.jsonl` chỉ có hai bản ghi `eligibility_count`, không có `label_load`/`test_behavior_load`; manifest kho dev và `dev_quality_summary.json` đều ghi `test_labels_loaded=false`. Hash và các đường dẫn bằng chứng được khóa trong sidecar amendment 02. Chưa đọc nhãn hoặc hành vi test.

## D-003 — H_obs và quy tắc phân tích nhãn ghi trước

- **Ngày:** 2026-10-25; ghi trước khi sinh hoặc đọc nhãn dev.
- **H_obs:** Toàn bộ lịch sử hợp lệ từ `analysis_start` tới trước `T`, tức `[analysis_start,T)`. Không dùng đơn tạo vào ngày T hoặc sau T.
- **Mẫu dev:** T là ngày đầu tháng từ 2024-05-01 đến 2025-04-01. Mỗi khách chỉ có một dòng: mốc đầu tiên mà khách có ít nhất một đơn status 3 không phải quà trước T. Chỉ nhận T khi `T+N+L < test_start`; một dòng mỗi khách ngăn cùng khách xuất hiện ở cả train và validation.
- **Nhãn:** Dương nếu khách có ít nhất một đơn status 3 không phải quà trong `(T,T+N]`; dùng phạm vi dev và không truy vấn test. Giới hạn status hiện tại/no status-history được ghi trong báo cáo.
- **Ngưỡng đã ghi trước:** Nếu có dưới 100 mẫu dương **hoặc** tỷ lệ dương dưới 5%, chỉ dùng temporal cross-validation trên dev cùng bootstrap CI theo khách; không đưa ra kết luận mạnh. Nếu có dưới 30 mẫu dương tổng cộng, không fit/so sánh classifier; báo số liệu và đề xuất đổi câu hỏi sang “có đơn mua hợp lệ thứ hai trong 180 ngày kể từ đơn đầu”, rồi dừng để chủ dự án duyệt.
- **Chia validation:** expanding temporal folds; mọi nhãn train phải kết thúc trước T validation ít nhất `N+L` ngày, và tập khách train/validation rời nhau. Mọi preprocessing/scaler/feature selection chỉ fit bên trong train fold. Không mở test.

## D-004 — Quy tắc tiền điều chỉnh theo nghiệp vụ

- **Ngày:** 2026-10-25; quyết định được ghi trước khi sinh nhãn Ngày 2 hoặc fit mô hình.
- **Người quyết định:** Chủ dự án/chủ cửa hàng.
- **Quy tắc đang có hiệu lực:** Với đơn status 3 trong `[analysis_start,test_start)`, `revenue_recognized = total_price_after_sub_discount - shipping_fee`, trừ trường hợp `after_sub_discount == total_price - total_discount` và `shipping_fee > 0`, khi đó dùng `after_sub_discount` để tránh trừ ship hai lần. `price_adjustment = revenue_recognized - (total_price - total_discount)`; giữ mọi điều chỉnh và gắn `adj_unexplained` cho mẫu không khớp các quan hệ đã nhận diện. `gross_list_value = total_price`.
- **Bằng chứng và cách diễn giải:** Cột `dash_*` của mẫu vẫn trống. Căn cứ là rà soát mẫu 13 đơn cùng xác nhận bằng lời của chủ cửa hàng: status 3 là doanh thu đã nhận/ghi nhận; đơn tại quầy thu tiền mặt; các trường thanh toán app giai đoạn đầu chưa đáng tin. Không dùng `cash`, `cod`, `prepaid`, `transfer_money`, `money_to_collect` làm bộ lọc hay bằng chứng thanh toán; `cod` âm không loại đơn.
- **Đơn tặng và số âm:** Đơn có doanh thu ghi nhận bằng 0 (hoặc `total_price=0` và `after=0`) là quà/ưu đãi, loại khỏi F/R, nhãn, giỏ hàng, doanh thu và AOV, nhưng giữ raw và đếm riêng. Doanh thu âm gắn `negative_revenue`, Monetary của đơn bằng 0, vẫn giữ trong F/R. Cổng tiền kỹ thuật duy nhất dừng khi số đơn âm vượt 1% toàn bộ status-3 dev.
- **Thay đổi có chủ đích:** Cổng amendment 02 trước đây ghi nhận 701/6.400 (10,95%) vượt 5%. Chủ dự án thay quy tắc sau khi xem kết quả đó dựa trên kiến thức nghiệp vụ status 3 và phí/ưu đãi, không dựa trên nhãn hoặc hành vi test. Đây là thay đổi sau kiểm toán, cần được xem cùng độ nhạy, không phải kiểm định độc lập.
- **Độ nhạy ghi trước:** (A) dùng `total_price-total_discount` thay doanh thu chính, giữ loại quà và đặt đóng góp âm bằng 0; (B) loại hợp mọi đơn có `price_adjustment != 0` hoặc `adj_unexplained`. Báo cáo doanh thu tổng, tỷ lệ đơn chênh trên 1%, Spearman Monetary theo khách; các bài toán phân khúc và phân loại cũng chạy lại theo B khi đủ dữ liệu.
- **Phạm vi bất biến:** `split.yaml`, `split.lock.json`, amendment 01, `analysis_start=2024-04-01`, `H_obs=[analysis_start,T)` và quyết định `N=365,W=365` không khả thi được giữ nguyên. Quy tắc và hash nằm trong `config/amendment_03_money_adjustment.yaml` cùng sidecar. Nhật ký truy cập vùng dành riêng có hai dòng `eligibility_count`, không có truy vấn nhãn hay hành vi test; test chưa mở.

## D-005 — Đăng ký trước vòng bổ sung Day 2B

- **Ngày:** 2026-10-25; đăng ký trước mọi thử nghiệm bổ sung.
- **Quyết định:** Giữ test đóng, không bắt đầu Day 3, giữ nguyên mô hình mua lại Logistic Regression đã chọn theo PR-AUC trung bình 5 fold (C=10). Không thay mô hình này sau khi thấy bất nhất với PR-AUC OOF gộp; ghi cả hai kết quả.
- **Căn cứ kết quả hợp lệ:** Nếu tiêu chí ghi trước không đạt, kết luận “không đủ bằng chứng để dự đoán mua lại từ dữ liệu hiện có”; không xem đó là thất bại và không thử biến thể mới.
- **Phạm vi thử nghiệm được phép:** Một lần chạy combo đã loại dòng giá 0 với 5 mức support định trước; một lần chạy phân khúc K=2/3/4 với 5 seed cố định và phân khúc theo quy tắc nghiệp vụ; một lần so sánh mô hình mua lại với bộ đặc trưng mới, bootstrap OOF 2.000 lần; mô hình hủy/hoàn chỉ chạy nếu từng fold có ít nhất 20 mẫu dương. Không được retry hoặc sửa đặc trưng sau khi xem kết quả.
- **Cổng tín hiệu mua lại:** Cận dưới bootstrap 95% ROC-AUC phải >0,55 và cận dưới bootstrap 95% chênh PR-AUC OOF so với baseline phải >0. Nếu thiếu một trong hai, dừng.
- **Cổng hủy/hoàn:** Nhãn status 5/6 so với status 3 không tặng; status-3 quà và status 0/1/4 loại. Đặc trưng định trước là số sản phẩm, `total_price` tại đơn, channel nếu có, tỉnh/thành, tháng và khách mới/cũ; không dùng discount ratio. Sau 180 ngày đầu làm train-only, chia thời gian dev còn lại thành 5 validation window liền nhau; nếu bất kỳ window nào có dưới 20 mẫu dương, ghi fold counts và bỏ mô hình này.
- **Bằng chứng khóa:** Nội dung và nguồn hash được khóa tại `config/amendment_04_followup.yaml` và `.lock.json`. Khi đăng ký, log không có truy vấn nhãn/hành vi test; test giữ đóng. Thời hạn vòng này tối đa 6 giờ.

## D-006 — Quà tặng theo dòng hàng và mở test một lần

- **Ngày:** 2026-10-26; quy tắc dòng hàng được ghi trước khi chạy phân tích giỏ hàng Day 3.
- **Người quyết định:** Chủ dự án.
- **Khảo sát nguồn:** Snapshot đơn Pancake GET đã khóa, 6.400 đơn status 3 và 30.049 dòng hàng trong `[2024-04-01,2025-10-22)`. Trường `items.is_bonus_product` có đủ 30.049 giá trị nhưng đều `false`; `discount_each_product`, `is_discount_percent`, `total_discount`, `quantity`, `variation_info.retail_price` cũng có đủ. Không có trường giá bán thực riêng. `variation_info.category_ids` có trong payload, nhưng chỉ có ID danh mục, không có tên danh mục lịch sử. Endpoint sản phẩm/kho không nằm trong allowlist; không thêm endpoint vì thông tin lịch sử cần thiết đã có trong dòng hàng. Tồn kho hiện tại không dùng để suy luận lịch sử.
- **Quy tắc:** Theo thứ tự ưu tiên: cờ `is_bonus_product` đã được xác nhận là bonus/quà; giảm giá 100% giá niêm yết từ cặp trường giảm giá dòng và loại giảm giá; duy nhất một tập con 1–6 dòng khớp chính xác `order.total_discount` với tổng `retail_price × quantity` được gán `inferred_subset` và cờ tin cậy thấp; phần còn lại là hàng bán. Giá niêm yết bằng 0, tên, giá thấp và support không tự tạo nhãn quà. Giá/field có nghĩa chưa xác minh chỉ làm cờ kiểm tra.
- **Độ nhạy combo:** Ba cách xử lý dòng (giữ mọi dòng; bỏ cờ và giảm giá đủ căn cứ nhưng giữ dòng suy luận; bỏ mọi dòng gift), kết hợp hai mức support 1% và 5%, FP-Growth, tối thiểu 5 giỏ. Combo chính chỉ gồm cặp ổn định trong ít nhất 4/6 cấu hình. Cặp chỉ xuất hiện trong cửa sổ ±14 ngày quanh đúng một ngày lễ đã liệt kê được gắn mô tả “theo mùa”. Một mùa Tết trọn vẹn không đủ kết luận chu kỳ năm.
- **Opend test:** Một lượt duy nhất cho baseline, LR gốc C=10 và LR feature-v2 C=0,1; ngưỡng 0,5; 2.000 bootstrap ghép cặp; K-Means K=2/3/4 và quy tắc phân khúc được áp từ mô hình/ngưỡng dev đã đóng băng; luật/combo hash-locked được chấm trên test. Không chọn lại, fit lại hay thử lại. `test_opened.lock.json` được tạo độc quyền trước lần đọc; nếu có file này, script từ chối chạy.
- **Bằng chứng trước mở:** `outputs/logs/reserved_access.jsonl` có đúng hai dòng eligibility-only, hash được ghi ở amendment 05; chưa có nhãn hoặc hành vi test. Không thay đổi sau khi mở.
- **Giới hạn:** Suy luận tập con có thể gán nhầm; không có giá vốn; biến thể/giá niêm yết lịch sử có thể thiếu; dữ liệu dev chỉ có một mùa Tết trọn vẹn.
- **Cấu hình:** `config/amendment_05_gift_lines.yaml` cùng sidecar; cấu hình chính xác đánh giá test được khóa riêng ở `config/amendment_05_test_open.yaml` trước lần mở.

## D-007 — Sửa phạm vi tổng hợp hồ sơ sản phẩm trước khi mở test

- **Ngày:** 2026-10-26; trước khi đóng băng combo cuối và trước mọi lần đọc test.
- **Lý do:** Rà soát đầu ra trung gian phát hiện bảng hồ sơ sản phẩm bỏ sót các dòng nằm trong đơn quà tặng ở cấp đơn, trong khi kiểm toán dòng đã tính chúng. Việc sửa chỉ mở rộng phạm vi mô tả product profile và đếm số đơn theo source; không thay quy tắc phân loại dòng, tập giỏ, support, K-Means hay mô hình.
- **Thực hiện:** Tính lại tổng hợp dev với cùng amendment 05; báo riêng đơn quà tặng cấp đơn; product profile dùng toàn bộ dòng status 3 dev. Giỏ combo vẫn giữ quy tắc đơn quà của amendment 03 rồi bỏ từng dòng quà đã phân loại. Lưu dấu vết và hash đầu ra cuối trước khi mở test.
- **Kiểm soát:** Log reserved access vẫn giữ đúng hai dòng eligibility-only; không đọc nhãn/hành vi test. Không thay threshold, candidate models, support grid hay tiêu chí ổn định.

## D-008 — Cấu hình mở test một lần

- **Ngày:** 2026-10-26; khóa trước khi nạp nhãn hoặc hành vi test.
- **Quyết định:** Theo lệnh chủ dự án, mở test đúng một lần cho baseline, Logistic Regression C=10 và Logistic Regression feature-v2 C=0,1; mọi ngưỡng cố định 0,5. Không fit lại hay chọn lại mô hình. Cổng hủy/hoàn không được vượt ngưỡng mẫu dương ở từng fold nên không có mô hình được fit.
- **Phân khúc:** Áp dụng K-Means K=2/3/4 và quy tắc nghiệp vụ với scaler, mô hình, ngưỡng DEV đã khóa. Không fit lại.
- **Luật combo:** Chấm đúng 24 cặp đã đóng băng tại `outputs/tables/combos_v2.csv`; không khai phá/chọn luật mới.
- **Độ đo và diễn giải:** Precision, recall, F1, ROC-AUC, average precision/PR-AUC, confusion matrix tại ngưỡng 0,5; bootstrap ghép cặp 2.000 lượt, seed 20261026; tín hiệu chỉ khi cận dưới ROC-AUC > 0,55 và cận dưới chênh PR-AUC so baseline > 0. Split kết thúc loại trừ ngày 2026-04-20; nhãn chỉ dùng ngày test quan sát được sau T.
- **Khóa cấu hình (lịch sử):** Bản ghi ban đầu trỏ tới SHA-256 `75358e47df854997dc9e1814810e98823ed44c3efb8d3b163c05526c6803af48`; đây là cấu hình trước phần sửa kỹ thuật ở D-009. Sidecar `.lock.json` khóa 39 nguồn.
- **Đính chính hash:** Cấu hình cuối trước lần mở duy nhất có SHA-256 `7964367ae28aa10d31e4c573772b7c3bc22b3f8b3d340c3292d0593bf6f30272`, như D-009 và lock hiện hành. Test vẫn chưa mở tại thời điểm seal; log khi đó có hai truy vấn `eligibility_count`.
- **Bảo vệ:** `outputs/metrics/test_opened.lock.json` được tạo độc quyền trước khi đọc test; evaluator từ chối nếu lock tồn tại. Sau khi mở, `run_all.py` chỉ chạy xác minh an toàn và pytest, không chạy notebook, fit mô hình hoặc đánh giá test lần nữa.

## D-009 — Sửa lỗi kỹ thuật tiền mở, không tiêu thụ lượt test

- **Ngày:** 2026-10-26; trước khi có test-open lock.
- **Sự cố:** Lần gọi evaluator đầu dừng khi đếm status DEV vì YAML trả `test_start` dưới kiểu ngày, trong khi bước tổng hợp yêu cầu chuỗi.
- **Kiểm chứng:** Tại thời điểm dừng, `outputs/metrics/test_opened.lock.json` và `outputs/logs/test_eval_access.jsonl` đều chưa tồn tại; evaluator chưa tạo lock độc quyền, chưa nạp trường test, chưa ghi test metric.
- **Sửa:** Chuẩn hóa `test_start` thành chuỗi ISO trước phân tích DEV. Không đổi cohort, đặc trưng, ngưỡng, mô hình, số bootstrap, luật, hay tiêu chí diễn giải. Chạy lại 6 kiểm tra focused; đếm 6.517 dòng status DEV an toàn; tái khóa cấu hình.
- **Hash cuối trước mở:** `config/amendment_05_test_open.yaml` SHA-256 `7964367ae28aa10d31e4c573772b7c3bc22b3f8b3d340c3292d0593bf6f30272`. Test vẫn đóng, log truy cập pre-open giữ nguyên.

## D-010 — Công khai sai khác nhãn ngày T sau lần mở test

- **Ngày:** 2026-10-26.
- **Quyết định của chủ dự án:** Báo cáo kết quả đúng theo cách evaluator thực tế đã chạy trên khoảng `[T, end)`, đồng thời công khai sai khác với quy tắc đã khóa yêu cầu ngày nhãn `> T`. Không đọc lại test để ước lượng ảnh hưởng và không sửa evaluator để chạy lại.
- **Sai khác đã xác định bằng mã:** `config/amendment_05_test_open.yaml` ghi nhãn từ ngày địa phương `> T`; `scripts/evaluate_test_once.py` lọc cửa sổ bằng `day >= start` và `day < end`, rồi gán nhãn cho mọi đơn đủ điều kiện trong danh sách đó mà không loại riêng ngày T. Kết quả và access log đã được tạo trong lần mở duy nhất; không được nạp lại dữ liệu test.
- **Cách diễn giải:** Theo cách chạy thực tế, các chỉ số vượt ngưỡng tín hiệu đã ghi trước. Có sai khác giao thức đã công khai; ảnh hưởng chưa xác định. Feature-v2 có ROC-AUC 0,703 (95% CI 0,665–0,737), chênh AP so với baseline +0,0774 (95% CI +0,0554 đến +0,1111). Đây không phải khẳng định 'đạt cổng ghi trước'. Xem `docs/test_provenance_note.md`.
- **DEV và cohort:** DEV OOF feature-v2 có ROC-AUC 0,497 và PR-AUC 0,065; tỷ lệ dương DEV 7,41%, test 4,59%. Số 5.169 của test trùng số tiền kiểm đã lưu; khác biệt với preflight lịch sử 5.499 và DEV status-3 5.174 chưa được phân rã đầy đủ. Không coi số trùng là bằng chứng identity hay rò rỉ.
- **Bảo vệ:** Không thay `split.yaml`, các sidecar khóa hoặc evaluator; không fit/chọn mô hình, đổi ngưỡng, chạy evaluator hay đọc lại nhãn/hành vi test. Các báo cáo tiếp theo phải nêu sai khác ngày T, ảnh hưởng chưa xác định, và giới hạn diễn giải kết quả test.
- **Tài liệu provenance:** Diễn giải protocol, cách phát hiện và giới hạn ước lượng được ghi trong `docs/test_provenance_note.md`.

## D-011 — Xác nhận nhập giảm giá thủ công cho quà theo dòng

- **Ngày:** 2026-10-26.
- **Người quyết định:** Chủ dự án, đồng thời là chủ cửa hàng.
- **Quyết định và nguồn:** Chủ cửa hàng xác nhận bằng lời rằng cửa hàng không dùng cờ `is_bonus_product` để đánh dấu quà; nhân viên nhập giảm giá thủ công cho quà tặng. Đây là lời xác nhận nghiệp vụ, chưa được kiểm tra riêng trên từng đơn.
- **Phạm vi:** Khảo sát 30.049 dòng DEV ghi nhận cờ API đều false. Có 907 dòng được phân loại quà; 903 dòng `inferred_subset` tiếp tục được ghi độ tin cậy thấp đến vừa. Không mở rộng suy luận sang tên/giá thấp và không sửa nhãn lịch sử.

## D-012 — Quy ước timezone của timestamp nguồn

- **Ngày:** 2026-10-26; quyết định nghiệp vụ ban đầu ghi tại CP1 ngày 2026-10-24.
- **Người quyết định:** Chủ dự án.
- **Quyết định:** Timestamp nguồn không có offset được coi là UTC, sau đó chuyển sang `Asia/Ho_Chi_Minh` (UTC+7) trước phép tính ngày kinh doanh.
- **Lý do và phạm vi:** Giữ thống nhất ngày cửa hàng, split, cohort và báo cáo. Không thay dữ liệu hoặc khóa trong quyết định này.

## D-013 — Mã trạng thái và đơn hợp lệ

- **Ngày:** 2026-10-26.
- **Người quyết định:** Chủ dự án.
- **Quyết định:** Snapshot có các mã 0, 1, 3, 4, 5, 6. Theo quy tắc nghiệp vụ, chỉ status 3 là đơn đã nhận/đơn mua hợp lệ cho doanh thu ghi nhận và cohort mua lại; các mã còn lại không tính là mua hợp lệ. Status hiện tại không được diễn giải thành lịch sử chuyển trạng thái.
- **Lý do:** Không có lịch sử trạng thái đầy đủ để khôi phục thời điểm status thay đổi; dùng quy ước hiện trạng đã được chủ dự án xác nhận.

## D-014 — Mốc cửa hàng bắt đầu hoạt động

- **Ngày:** 2026-10-26; xác nhận ban đầu ngày 2026-10-24.
- **Người quyết định:** Chủ dự án.
- **Quyết định:** Cửa hàng bắt đầu hoạt động ngày 2024-04-01 theo giờ Việt Nam. Đơn trước mốc giữ trong raw nhưng loại khỏi hành vi, nhãn, giỏ và doanh thu ghi nhận.
- **Lý do:** Các đơn trước mốc thuộc giai đoạn bán thử theo xác nhận nghiệp vụ.

## D-015 — Diễn giải đơn 0 đồng

- **Ngày:** 2026-10-26.
- **Người quyết định:** Chủ dự án.
- **Quyết định:** Đơn status 3 có doanh thu ghi nhận bằng 0, hoặc `total_price=0` và `after=0`, được coi là quà/ưu đãi theo quy tắc tiền hiện hành; giữ raw, đếm riêng, loại khỏi hành vi và doanh thu chính.
- **Lý do:** Đây là quy ước nghiệp vụ về đơn miễn phí; giá niêm yết bằng 0 ở riêng một dòng không tự tạo nhãn quà.

## D-016 — Diễn giải chênh lệch trường tiền

- **Ngày:** 2026-10-26.
- **Người quyết định:** Chủ dự án.
- **Quyết định:** Chênh lệch giữa doanh thu ghi nhận và `total_price-total_discount` được giải thích theo nghiệp vụ là phí phát sinh hoặc ưu đãi/khuyến mãi. Status 3 được tính là doanh thu ghi nhận theo xác nhận chủ cửa hàng.
- **Giới hạn:** Đây là diễn giải nghiệp vụ dựa trên mẫu 13 đơn và lời xác nhận; không phải đối soát độc lập sổ kế toán/ngân hàng. DuckDB DEV không có trường tiền.

## D-017 — Quản lý khóa HMAC

- **Ngày:** 2026-10-26.
- **Người quyết định:** Chủ dự án.
- **Quyết định:** Giữ khóa HMAC analytics được tạo và ghi cục bộ bằng phần mềm; không tự đổi khóa trong quá trình này vì sẽ mất liên kết giả danh giữa các đầu ra đã tạo.
- **Bảo vệ:** Giá trị khóa chỉ ở file môi trường local bị ignore; không ghi vào log, báo cáo, repository hay gói bàn giao.

## D-018 — Chọn chân trời N=180

- **Ngày:** 2026-10-26.
- **Người quyết định:** Chủ dự án.
- **Quyết định:** Giữ phương án 1 với chân trời nhãn N=180 ngày trong split đã khóa; không đổi sang N=365 trong các kết quả đã tạo.
- **Lý do:** Đây là lựa chọn đã đăng ký để giữ cohort khả thi trong khoảng dữ liệu quan sát; cấu hình split và hash bất biến.

## D-019 — Giữ riêng các số cohort chưa đối soát

- **Ngày:** 2026-10-26.
- **Người quyết định:** Codex trong phạm vi kiểm toán đã được chủ dự án duyệt.
- **Quyết định:** Công bố 5.499 eligibility-preflight, 5.174 khách status-3 DEV và 5.169 khách scoring đã freeze như các cohort khác nhau; ghi rõ chưa có phân rã nối tiếp được xác minh.
- **Lý do:** Tránh suy diễn nguyên nhân chênh lệch hoặc tái dựng row-level cohort sau mở test. Chỉ dùng metadata aggregate đã tồn tại.

## D-020 — EDA hậu mở chỉ dùng DEV và đóng băng notebook fit

- **Ngày:** 2026-10-26.
- **Người quyết định:** Codex theo phạm vi do chủ dự án duyệt.
- **Quyết định:** Notebook 01b và hình EDA chỉ dùng kho DEV trước T cùng mẫu nhãn DEV lịch sử; notebook 02–05 dừng ngay khi test-open lock tồn tại. Hash output cache trước khi sửa được ghi lại và giữ nguyên.
- **Lý do:** Duy trì ranh giới DEV/test, tránh chạy lại pipeline có thể ghi đè artifact đã freeze, và cho phép đối chiếu outputs lịch sử mà không nạp test.

## D-021 — Cách diễn đạt cổng tín hiệu sau khi xác minh khóa

- **Ngày:** 2026-10-26.
- **Căn cứ:** Mục `classification` của Amendment 05 khai báo cùng một quy tắc cận dưới ROC-AUC 95% CI > 0,55 và cận dưới paired ΔAP CI > 0 cho các classifier được liệt kê; D-008 ghi cả Logistic Regression C=10 và feature-v2 C=0,1. Metric aggregate có bootstrap CI cho cả hai mô hình. `feature_v2_signal_supported=True` là cờ lưu riêng của v2; không thêm cờ cho C=10.
- **Quyết định diễn giải:** Báo rõ CI aggregate của cả hai mô hình thỏa các cận số liệu theo cách chạy thực tế. Vai trò không đổi: Logistic Regression C=10 là mô hình chính theo D-005; Logistic Regression feature-v2 C=0,1 là khảo sát bổ sung theo Amendment 04 và không thay mô hình chính.
- **Câu bắt buộc ở nơi báo kết quả:** “Cấu hình ghi >T, evaluator dùng [T,end) (gồm ngày T); ảnh hưởng chưa xác định; đây là kết quả số liệu của lần chạy thực tế, không phải khẳng định tuân thủ đầy đủ giao thức, không gọi là 'đạt cổng ghi trước'.”
- **Giới hạn:** Không đọc lại test, không thay config/metric test, không tạo cờ tín hiệu mới cho C=10. Nguồn: `config/amendment_05_test_open.yaml` (mục classification, chỉ đọc), `outputs/metrics/test_eval.json` (metric aggregate, chỉ đọc) và `docs/test_provenance_note.md`.

## D-022 — Không mở Amendment 06 cho chẩn đoán anchor DEV

- **Ngày:** 2026-10-26.
- **Quyết định:** Không chạy chẩn đoán anchor DEV trong phạm vi và thời hạn hiện tại; không tạo Amendment 06.
- **Lý do:** Một đánh giá hợp lệ theo từng anchor cần rolling-origin, mỗi mô hình chỉ được fit trên dữ liệu có trước anchor. Mô hình đã fit trên DEV đầy đủ có thể đã thấy dữ liệu tương lai của anchor lịch sử; chấm trực tiếp sẽ rò rỉ thời gian. Chạy rolling-origin cần fit mới, hiện bị cấm; test đã mở và hạn nộp là 2026-10-27.
- **Điều kiện nếu xem xét sau này:** Chủ dự án phải duyệt phạm vi riêng và Amendment 06 mới. Phân tích chỉ mang tính thăm dò, phải báo cả kết quả không ủng hộ giả thuyết và không đổi kết luận hiện hành. Metric theo fold DEV OOF đã lưu có thể được trích mô tả mà không tính lại; không có metric anchor dựng mới trong phạm vi hiện tại.

## D-023 — Đóng gói bàn giao

- **Ngày:** 2026-10-26.
- **Quyết định:** Đóng gói bàn giao: dọn file tạm, thêm dữ liệu mẫu tổng hợp (data/sample, không từ dữ liệu thật), thêm docs/INDEX.md; không đổi kết luận, không di chuyển docs.


