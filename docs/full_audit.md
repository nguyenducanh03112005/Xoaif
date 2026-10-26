# Xoaif Garden — kiểm toán toàn bộ trước khi tiếp tục

Ngày kiểm toán: 2026-10-26 (Asia/Ho_Chi_Minh). Phạm vi: Ngày 0 đến mục 4.1; chỉ kiểm tra. Không sửa source, cấu hình hay đầu ra cũ. Hai file mới trong phạm vi là báo cáo này và outputs/tables/audit_checklist.csv.

## Tóm tắt điều hành

- Checklist: **50 mục** — PASS **20**, FAIL **20**, CHƯA XÁC MINH **10**.
- Findings đã khử trùng lặp: **P0 4 / P1 13 / P2 0**.
- Sai khác quan trọng nhất: quy tắc ghi nhãn yêu cầu >T nhưng evaluator thực thi [T,end); ảnh hưởng không thể xác định nếu không đọc lại test, việc này bị cấm.
- Một số báo cáo/dashboard/PDF vẫn nói test đạt cổng ghi trước; script PDF còn ghi 24/24 combo lift>1 trong khi metric có 21/24.
- README liệt kê slides nhưng không có file; PDF bàn giao hiện tại 7 trang, còn builder mới tạo 15 trang.
- Đề xuất: sửa diễn giải/provenance trước; đồng bộ số liệu và PDF tiếp; hoàn thiện slide/EDA/kiến trúc sau khi chủ dự án duyệt.

## 1. Phạm vi, ranh giới và lệnh đã chạy

- Đã đọc manifest/metadata và tính hash raw snapshot page bytes nhưng **không giải mã hay phân tích nội dung 1.202 trang raw**; không đọc đơn/nhãn/hành vi test. DuckDB được mở read-only, chỉ truy vấn schema/ngày/count trên DEV.
- Không chạy evaluator, notebook, refit/chọn mô hình, hoặc đọc lại test. test_eval.json chỉ được đọc ở dạng aggregate đã lưu; lock/access log được kiểm tra metadata và số sự kiện.
- Lệnh: .venv\Scripts\python.exe -m pytest -q → 73 passed, 12,17 giây; .venv\Scripts\python.exe scripts/run_all.py → safe post-open branch, 73 passed trong 9,79 giây, tổng 20,71 giây; split/GET-only/day3 locks/PII pass; không warning. Runner ghi rõ không refit/evaluate lại.
- Khác: scripts/verify_split_lock.py, scripts/verify_day3_locks.py, scripts/verify_readonly.py đạt; pip check không có broken requirements; kiểm tra hash/config, CSV/JSON/PNG, pdfinfo/pdftoppm. Dashboard AppTest headless bị treo quá 45 giây và ngắt thủ công; tốc độ app là CHƯA XÁC MINH.
- Không in/lưu API key, shop identifier, PII, mã đơn, hay nội dung raw trong báo cáo này. Quét secret bỏ qua raw pages, quarantine, .venv, .git và không OCR ảnh/PDF; vì vậy không khẳng định “không có trong toàn repo”.

## 2. Findings theo mức độ

| Mã | Check | Mô tả | Bằng chứng | Hệ quả | Đề xuất sau duyệt | Ước lượng |
|---|---|---|---|---|---|---:|
| P0-01 | B3, E3.11 | Quy tắc khóa yêu cầu ngày nhãn >T, code đã chạy bao gồm ngày T ([T,end)). Ảnh hưởng lên kết quả không thể xác định nếu không mở lại test. | config/amendment_05_test_open.yaml:12; scripts/evaluate_test_once.py:93–126; docs/decisions.md:97–101; outputs/metrics/test_eval.json:10–11. | Không thể gọi đây là kết quả tuân thủ đầy đủ cổng ghi trước; metric có giới hạn protocol. | Giữ nguyên lock; diễn giải là kết quả của cửa sổ thực chạy; công khai ảnh hưởng chưa xác định; không rerun. | 45–60 phút |
| P0-02 | E4, G1, G2 | Nhiều tài liệu/UI/PDF builder vẫn khẳng định “đạt tiêu chí ghi trước” dù D-010 đã xác nhận sai khác ngày T. | docs/test_report.md:19; docs/qa.md:7; docs/handover.md:32,48; docs/demo_script.md:19; src/app/streamlit_app.py:261; scripts/build_report_pdf.py:322,363. | Hội đồng có thể nhận kết luận sai về tính hợp lệ của test. | Đồng bộ kết luận, cảnh báo dashboard và lời demo với D-010. | 60–90 phút |
| P0-03 | E3.5 | PDF builder ghi mọi 24 combo đều lift>1; số aggregate là 21/24. | scripts/build_report_pdf.py:353; outputs/metrics/test_eval.json:285; docs/test_report.md:29. | Số liệu sai trong báo cáo được nộp. | Sửa câu số liệu sau duyệt; đối chiếu bảng frozen combo; không chọn luật mới. | 15–25 phút |
| P0-04 | D8, G3 | Slides/PDF in/ghi chú được README báo là sản phẩm nhưng không tồn tại. | README.md:28–31; slides/ rỗng; kiểm kê file. | Thiếu sản phẩm chấm bắt buộc/đã công bố là bàn giao. | Tạo slide và ghi chú; thêm dependency có pin; dùng font sẵn có; render và QA. | 240–360 phút |
| P1-01 | A4, E3.1 | Mốc 6.993 bị mô tả như số đơn pre-analysis; hồ sơ cho thấy 476 pre-analysis + 6.517 DEV. Ba cohort khách 5.499/5.174/5.169 chưa có phân rã chính xác. | outputs/tables/day1_analysis_start_profile.json; outputs/tables/day1_eda_summary.json; outputs/tables/eligibility_preflight.csv; docs/cp1_review.md:101–103. | Khó giải thích universe, bộ lọc và các con số trong vấn đáp. | Lập bảng định nghĩa count theo từng giai đoạn từ metadata đã có; nếu thiếu chứng cứ thì giữ nhãn chưa xác minh. | 45–90 phút |
| P1-02 | A6 | Shop identifier xuất hiện trong manifest; quét rộng bị giới hạn; quarantine chưa được đối chiếu với gói phát hành chưa tồn tại. | Manifest snapshot; .gitignore:5; docs/shared_release.md:32–33; giới hạn quét tại mục 1. | Có thể đưa metadata nhận diện vào bản chia sẻ tương lai. | Rà manifest và danh sách package khi có gói; kiểm tra secret bằng quy trình không ghi giá trị ra log. | 30–60 phút |
| P1-03 | B4, C2, C3 | Money totals khớp aggregate nhưng DuckDB DEV không có trường tiền để tính lại; xác nhận giảm giá thủ công của chủ cửa hàng chưa thấy ghi nhận riêng. | docs/money_audit.md; outputs/metrics/day2_money_audit.json; outputs/tables/money_diagnosis.csv; outputs/metrics/day3_gift_field_survey.json; docs/decisions.md:61–63. | Không thể hoàn thành đối soát độc lập nguồn; một giả định quà vẫn thiếu owner evidence. | Nêu giới hạn; bổ sung xác nhận nghiệp vụ có provenance sau khi duyệt; không dựng lại từ test. | 45–90 phút |
| P1-04 | D1 | EDA thiếu tổng quan kiểu/thiếu/phân loại, outlier/capped/ít mẫu, đặc trưng-target và nhận xét địa lý theo tỉnh. | notebooks/01_day1_development_eda.ipynb; outputs/tables/day1_eda_summary.json; hình Day 1. | Chưa đáp ứng đủ đề mẫu California Housing theo biến thể dữ liệu bán hàng. | Bổ sung EDA DEV có kiểm soát và giải thích tác động của từng nhận định tới tiền xử lý/mô hình. | 180–240 phút |
| P1-05 | D5, D6 | Chưa giải thích RMSE/MAE/R² không áp dụng cho phân loại; thiếu ma trận kiến trúc vai trò/bài toán/công cụ/tác dụng/chức năng. | scripts/build_report_pdf.py:198–230,301–303; docs/qa_roles.md:7; không thấy giải thích RMSE/MAE/R² trong docs. | Thiếu phần yêu cầu giảng viên dù đã có sơ đồ luồng và Star Schema. | Thêm giải thích classifier-vs-regression và ma trận 5 tầng. | 90–120 phút |
| P1-06 | D7, G2 | Tệp PDF hiện tại 7 trang; builder mới tạo 15 trang; PDF bàn giao cũ dừng ở phần đầu/kho/EDA. | pdfinfo report/xoaif_report.pdf → 7 pages; build vào thư mục tạm → 15 A4 pages và render đủ. | Báo cáo hiện tại chưa có chương mô hình/test, phân khúc, combo, kết luận/phụ lục. | Sau khi sửa lỗi P0, dựng bản mới trong temp, kiểm thị giác rồi thay bản bàn giao theo phê duyệt. | 45–90 phút |
| P1-07 | D9, E1 | Thiếu ảnh demo; tên thư mục trong tài liệu không thống nhất; docs/test_audit.md và notebook 06 không có. | docs/demo_script.md:8,28; docs/PROGRESS.md:48; kiểm kê docs/notebooks/slides. | Demo dự phòng và dự kiến tài liệu 4.1 chưa hoàn tất. | Chốt tên thư mục; chụp ảnh dashboard đã rà PII; xác nhận có cần notebook 06/test audit theo kế hoạch. | 60–150 phút |
| P1-08 | E2 | Chỉ có notebook 01–05; 02–05 là wrapper 2 cell; hash output không được ghi trong PROGRESS. | notebooks/*.ipynb; docs/PROGRESS.md; hashes output không có trong progress. | Tái lập/vấn đáp từng phần phụ thuộc nhiều vào code ngoài notebook. | Bổ sung giải thích cell/section; ghi hash output và nguồn metric; không chạy notebook trong audit. | 60–120 phút |
| P1-09 | E3.3 | Point estimate ROC test có thể ghép nhầm với CI: v2 ROC .702729 làm tròn .703, CI .665–.737; .702 thuộc C=10 khi làm tròn. Test report thiếu point estimate đầy đủ. | outputs/metrics/test_eval.json; docs/test_report.md:11,19. | Dễ trình bày sai model/metric dù chênh nhỏ. | Đồng bộ bảng theo tên model và chuẩn làm tròn; ghi AP .1233 và ΔAP-baseline .0774 cùng CI. | 30–60 phút |
| P1-10 | E5 | D-008 còn hash cũ; một số D thiếu người quyết định; timezone +7 ghi ở CP1 nhưng chưa có D riêng. | docs/decisions.md:76–101; docs/cp1_review.md:67–69; sidecar hiện hành. | Nhật ký có thể gây hiểu nhầm về cấu hình mở test và người quyết định. | Cập nhật register sau duyệt; giữ lịch sử D-009/D-010 và provenance. | 30–60 phút |
| P1-11 | F2, F3 | Không có lock có hash; PDF font path cố định Windows; git index có 0 tracked files và 83 .pyc caches. | requirements.txt có 130 pins nhưng không lock/hash; scripts/build_report_pdf.py:20; git ls-files count=0. | Thành viên khác khó tái tạo; rủi ro chia sẻ/version control và portable build. | Tạo lock có hash/OS note; dùng font discovery/configurable path; tạo gói chia sẻ theo phê duyệt. | 60–120 phút |
| P1-12 | G1 | Thời gian tải và test import/UI chưa xác minh; AppTest headless bị ngắt sau >45s. | streamlit.testing.v1.AppTest attempt; src/app/streamlit_app.py:77–104,126–129. | Không có bằng chứng dưới 10s; không kết luận app chậm/hỏng từ harness. | Đo ở môi trường Streamlit chuẩn hoặc thêm smoke check offline không đọc test thô. | 30–60 phút |
| P1-13 | E1, E5 | Không có manifest ngày sửa kỳ vọng, full decision transcript hay release package; bytecode/cache và customer-HMAC CSV tồn tại trong workspace. | Kiểm kê; docs/shared_release.md:32–33; git ls-files count=0. | Không thể khẳng định mtime/package completeness; cần kiểm soát trước phát hành. | Tạo release manifest và allowlist sau owner review; giữ customer-level files restricted. | 30–60 phút |

P0/P1/P2 là số finding duy nhất trong bảng này; các dòng checklist có thể cùng tham chiếu một finding gốc.

## 3. Kế hoạch sửa đề xuất — chỉ ước lượng, chưa thực hiện

1. Chốt diễn giải test và phạm vi ngày T (P0-01/02): 45–90 phút. Không rerun evaluator hoặc mở lại dữ liệu; ghi rõ thực tế [T,end) và ảnh hưởng chưa biết.
2. Sửa lỗi số liệu combo/metrics và đồng bộ báo cáo/dashboard/FAQ/demo (P0-03, P1-09): 45–90 phút; chạy PDF builder vào temp sau khi được duyệt.
3. Hoàn thiện sản phẩm nộp thiếu: slide + notes + demo captures khoảng 4–6 giờ; PDF bàn giao cần dựng/QA lại khoảng 45–90 phút.
4. Bổ sung EDA, ma trận kiến trúc, giải thích metric, notebook/docs/hashes, cohort/provenance: khoảng 4–6 giờ tùy phạm vi được duyệt.
5. Hoàn thiện release portability/manifest và smoke check dashboard: khoảng 1,5–3 giờ.

## 4. Bảng đối chiếu rubric đề mẫu và yêu cầu giảng viên

| Yêu cầu | Trạng thái | Bằng chứng hiện có | Thiếu/giải thích |
|---|---|---|---|
| EDA: tổng quan schema, thống kê/thiếu/phân loại | THIẾU | notebooks/01_day1_development_eda.ipynb; outputs/tables/day1_eda_summary.json | Summary chủ yếu đếm đơn/tháng, trung vị đơn/khách và số product; chưa có hồ sơ biến/missing/categories đầy đủ. |
| EDA: phân phối target/feature, outlier/capped, nhóm nhỏ, quan hệ target, nhận định tác động | THIẾU/MỘT PHẦN | Hình frequency/basket; day2_label_audit.json; tree depth curves | Chưa có phần EDA liền mạch theo rubric và quyết định xử lý tương ứng. Day 1 cố ý chưa nạp nhãn; cần nối với phân tích DEV. |
| EDA địa lý | THIẾU | Dashboard có doanh thu tổng hợp theo tỉnh; feature có province | Không thấy bản đồ/phân tích địa lý và nhận xét trong EDA. Không có tọa độ; bỏ DBSCAN địa lý là hợp lý. |
| Tiền xử lý/feature/chia tập không rò rỉ | PASS | src/features/day2_data.py; notebooks02–03; tests; split config | Fold transformer fit trong train; khách tách fold; cận thời gian có code/evidence. |
| Baseline, Logistic, Tree depth, Random Forest, CV, metrics và importance | PASS/MỘT PHẦN | src/models/classify.py; dev_final_models_v2.json; decision_tree_depth_curve*.csv; repurchase_feature_importance_v2.csv | Artifact tồn tại; tài liệu nộp chưa giải thích đầy đủ feature importance và có kết luận test sai protocol. |
| K-Means elbow/silhouette/chọn K/đặt tên/đối chiếu | PASS | segments_elbow.png; segments_silhouette.png; profiles/metrics | K=2 silhouette .508 và độ nhạy K=3/4 được báo cáo. |
| DBSCAN hoặc lý do bỏ; phương án thay thế | PASS/MỘT PHẦN | notebooks/04_unsupervised.ipynb; day2_segmentation.json ghi chỉ có tỉnh/thành | Lý do bỏ DBSCAN có ghi; rule segments là tham chiếu thay thế, không phải benchmark DBSCAN. |
| Kết luận/hạn chế/hướng cải tiến | MỘT PHẦN | docs/test_report.md; handover; PDF builder | Kết luận tồn tại nhưng mâu thuẫn; PDF bàn giao cũ thiếu chương cuối. |
| Kiến trúc: vai trò/bài toán/công cụ/tác dụng/chức năng; bảng và sơ đồ | MỘT PHẦN | Sơ đồ 5 tầng và Star Schema trong PDF builder; docs/qa_roles.md phân công người | Có sơ đồ; thiếu ma trận vai trò/công cụ/chức năng/tác dụng. |
| RMSE/MAE/R² có áp dụng? | THIẾU giải thích | Mô hình là classifier; báo ROC-AUC/AP/precision/recall/F1 | Ghi rõ đây là phân loại nên metric hồi quy không áp dụng; không coi absence là lỗi mô hình. |
| PDF, slide in, demo, Q&A | FAIL | QA 38 câu; demo script; PDF builder | PDF bàn giao 7 trang; slides/notes và ảnh demo không tồn tại. |

## 5. E3 — Đối chiếu số liệu và khác biệt định nghĩa

| Cặp chỉ số | Đối chiếu | Kết luận |
|---|---|---|
| Cohort 5.169 / 5.174 / 5.499 | Test/v2 dùng 5.169; DEV status-3 customer count 5.174; eligibility_preflight.csv giữ 5.499 lịch sử. | Có thể là filter/mốc/cohort khác nhau; exact decomposition chưa xác minh. Số trùng 5.169 không chứng minh identity. |
| Test positive vs DEV | 237/5.169 = 4,59%; DEV 7,41%. | Khớp. |
| Test ROC/AP/CI | C=10: ROC .702438/AP .123428; feature-v2: ROC .702729/AP .123291; v2 CI ROC .665079–.737325; ΔAP-baseline CI +.055401–+.111108. | V2 nên báo ROC .703, AP .1233; .702 thuộc C=10 khi làm tròn. Test report thiếu point estimate theo model. |
| DEV OOF v2 | ROC .496861, PR/AP .064508; 260/3.508 dương (7,41%). | Khớp khi làm tròn; là tập DEV khác test. |
| Combo test | 24 frozen; 2.174 giỏ; 21 lift>1. | Metrics/docs khớp; PDF builder ghi sai 24/24. |
| K=2 silhouette | .507541 → .508. | Khớp. |
| ARI K=3/K=4 | Seed .999718/.993364; revenue sensitivity .621359/.587616. | Khớp. |
| Giỏ Day2B vs Amendment05 | 6.031 trước; 5.684 sau bỏ dòng giá 0; 6.006 sau phân loại mọi nguồn gift line. | Hai quy tắc loại dòng khác nhau, không phải mâu thuẫn. |
| Quà 22 vs “27” | Money audit ghi 22 order gifts; 27 là count theo tháng của adjustment, không phải gift total. | Không phải mâu thuẫn quà. |
| Ngày T | Config ghi >T; code dùng >=T và <end; test_eval.json vẫn mô tả >T. | Sai khác protocol trọng yếu; ảnh hưởng chưa biết; không mở lại test. |

Tiền: day2_money_audit.json và money_diagnosis.csv cho 5.739/6.400 khớp công thức (89,67%); adjustment +651/-8/zero 5.719; gifts 22; negative revenue 2; sensitivity A +52.016.532 VND (2,019%); Spearman 0,995280. DuckDB không có tiền nên đây là đối chiếu các output đã lưu, không phải tính lại độc lập từ warehouse. total_price=0 nhưng after dương có 5 trường hợp; không bị coi là gift theo order-level rule.

## 6. E4 — Tài liệu cần đồng bộ sau phê duyệt

- Kết luận “test đạt cổng ghi trước” cần sửa theo D-010: docs/test_report.md:19; docs/qa.md:7; docs/handover.md:32,48; docs/demo_script.md:19; src/app/streamlit_app.py:261; scripts/build_report_pdf.py:322,363.
- Boundary/provenance chưa đúng: outputs/metrics/test_eval.json:10–11 vẫn mô tả >T; docs/test_report.md:5,19 chưa nói rõ ngày T nằm trong kết quả thực tế; docs/qa.md:38 nói 179 ngày sau T nhưng không giải thích ngày T được tính.
- Kết luận DEV-only cần đặt cạnh test: docs/day2_summary.md:126 là kết luận DEV hợp lệ tại thời điểm đó nhưng chưa có tóm tắt ghép với kết quả test và D-010.
- Trạng thái tiền mở đã cũ: docs/day2_walkthrough.md:59,61; docs/day3_inputs.md:13,25; docs/PROGRESS.md:17,31,40. Một phần là lịch sử nhưng chưa gắn nhãn rõ; các dòng sau trong progress lại ghi test đã mở.
- Số liệu combo: scripts/build_report_pdf.py:353 ghi mọi 24 lift>1; thực tế 21.
- Metric test: docs/test_report.md cần ghi point estimate theo model; phân biệt ROC .702438 của C=10 với .702729 của v2.

## 7. E1 — Kiểm kê file

Đã kiểm tra existence/size/định dạng trên workspace. Tất cả file hiện có dưới outputs/docs/src/scripts/tests/notebooks đều non-zero; JSON/CSV parse được; notebook là JSON hợp lệ; PNG có signature; PDF xem bằng pdfinfo và render bằng pdftoppm. Không có manifest ngày sửa mong đợi nên mtime đúng với từng phiên trước là CHƯA XÁC MINH. Joblib không được load; không OCR hình/PDF. Danh sách file dưới đây chỉ là tên tương đối, không chứa dữ liệu khách.

| Thư mục | Hiện có | Kết quả |
|---|---:|---|
| outputs/figures | 9 | PNG signature hợp lệ |
| outputs/tables | 49 trước audit (50 gồm checklist mới) | CSV/JSON parse hợp lệ; gồm file customer-HMAC/label-level, giữ restricted |
| outputs/metrics | 17 | JSON parse hợp lệ; test_eval.json aggregate; lock không sửa |
| outputs/logs | 3 | Non-zero; access log đã đếm event, không đưa ID vào báo cáo |
| outputs/models | 3 | Non-zero; không load/re-fit |
| docs | 26 trước report này | Markdown non-zero; một số stale như E4 |
| src / scripts / tests | 31 / 32 / 13 file .py | Có thêm 35/27/21 .pyc cache |
| notebooks | 5 | 01–05 có; 06 thiếu |
| report/slides/demo | 1 PDF / 0 slides / 0 demo screenshots | PDF 7 trang; slide/demo thiếu |

**Danh sách outputs:**

- figures: day1_frequency_and_basket_bands.png; day1_monthly_valid_orders.png; day1_star_schema.png; decision_tree_depth_curve.png; decision_tree_depth_curve_v2.png; segments_elbow.png; segments_silhouette.png; segments_v2_stability.png; split_timeline.png.
- tables: classifier_feature_importance.json; combos.csv; combos_v2.csv; companion_products_v2.csv; dashboard_product_orders.csv; dashboard_sales_monthly.csv; dashboard_sales_province.csv; dashboard_status_counts.csv; day1_analysis_start_profile.json; day1_basket_size_bands.csv; day1_customer_frequency_bands.csv; day1_customer_order_frequency_effective.csv; day1_development_cohort_summary.json; day1_eda_summary.json; day1_gap_2022-10_to_2024-03.csv; day1_monthly_orders_all_status.csv; day1_monthly_valid_orders.csv; day1_sensitivity_feasibility.csv; day2_features_A.csv; day2_features_B.csv; day2_features_primary.csv; day2_label_samples_A.csv; day2_label_samples_B.csv; day2_label_samples_primary.csv; decision_tree_depth_curve.csv; decision_tree_depth_curve_v2.csv; dev_quality_summary.json; dev_status_counts.csv; dq_report.csv; eligibility_preflight.csv; gift_line_audit.csv; gift_line_rates_monthly.csv; gift_line_rates_order_size.csv; money_candidate_profile_status3.csv; money_candidate_relationships_status3.csv; money_diagnosis.csv; pre_analysis_orders_by_status.csv; product_profile.csv; repurchase_feature_importance_v2.csv; rules.csv; rules_v2.csv; seasonal_pair_metrics.csv; segment_profiles.csv; segment_profiles_v2.csv; segments.csv; segments_v2.csv; status_counts.csv; test_combos_frozen.csv; test_segment_profiles.csv.
- metrics (17 files): day2_baskets.json; day2_label_audit.json; day2_money_audit.json; day2_preprocessing.json; day2_product_metadata_summary.json; day2_segmentation.json; day2b_baskets.json; day2b_cancel_model.json; day2b_segmentation.json; day3_combo_prereg.json; day3_gift_field_survey.json; day3_pretest_freeze.json; dev_final_model.json; dev_final_models_v2.json; frozen_segmenters_dev.json; test_eval.json; test_opened.lock.json.
- logs: 3 files including access/evaluation metadata; names/content not expanded here to avoid leaking sensitive execution metadata.
- models: day2_dev_final_model.joblib; repurchase_features_v2.joblib; segmenters_dev_frozen_v1.joblib.
- notebooks: 01_day1_development_eda.ipynb; 02_preprocess.ipynb; 03_supervised.ipynb; 04_unsupervised.ipynb; 05_combo.ipynb. Notebook 06 does not exist. Hashes output 01–05 were calculated but are absent from PROGRESS; no recorded baseline exists to establish historical change.
- docs currently present: api_notes.md; cp1_review.md; data_dictionary.md; data_gap_report.md; data_governance.md; data_protocol.md; day1_summary.md; day1_walkthrough.md; day2_summary.md; day2_walkthrough.md; day3_inputs.md; decisions.md; demo_script.md; glossary.md; handover.md; leakage_review_cancel.md; money_audit.md; money_definition.md; point_in_time.md; product_profile_top20.md; PROGRESS.md; qa_roles.md; qa.md; schedule.md; shared_release.md; test_report.md. Missing docs/test_audit.md.
- Source/script/test inventories: 31 src .py; 32 scripts .py; 13 tests .py. All are non-empty. Inventory includes src/app, src/features, src/ingest, src/models, src/warehouse and the planned notebooks/docs/report/slides directories. Bytecode caches are summarized above.

File lớn/rủi ro chia sẻ: outputs/tables/segments_v2.csv (~2,05 MB); segments.csv (~1,42 MB); ba day2_features_*.csv (~1,0 MB mỗi file); ba day2_label_samples_*.csv (~0,68–0,71 MB). Các file này chứa customer HMAC/label-level DEV; không đưa vào dashboard/release chung. .gitignore loại data/, .venv và env nhưng không có package để kiểm tra quarantine. Git index hiện có 0 tracked files.

**Đầu ra thiếu so với tài liệu/kế hoạch:** notebooks/06*; slides/xoaif.pptx; slides/xoaif_print.pdf; slides/speaker_notes.md; demo screenshots dưới docs/demo_screens/ hoặc docs/demo_screenshots/; docs/test_audit.md (được ghi là việc kế tiếp trong progress nhưng chưa tạo). README liệt kê slides như deliverable nhưng chưa có tệp.

## 8. E2/E5 — Notebook, decisions và provenance

- Notebook 01: 6 cells (2 markdown, 4 code); 02–05: mỗi notebook 2 cells (1 markdown, 1 code wrapper). Không chạy notebook; không cell rỗng, error/traceback hay TODO phát hiện trong JSON đã lưu.
- Output hashes đã tính nhưng không có trong docs/PROGRESS.md: 01 262d8d24a0de3a70…; 02 732f1eaf…; 03 266d3722…; 04 11639dea…; 05 ab995a8b…. Không có baseline hash trong repo để so sánh lịch sử.
- D-010 nêu chủ dự án và giới hạn đúng. D-008:83 còn hash 75358e47…; D-009:92 và sidecar hiện hành dùng 7964367a…. D-005, D-007, D-009 không có người quyết định riêng. Quyết định timezone +7 có ở CP1 review; status/money/gift/split evidence rải trong decisions/config/data dictionary. Thiếu transcript đầy đủ khiến “không bỏ sót quyết định nào trong mọi cuộc trò chuyện” là CHƯA XÁC MINH.

## 9. F/G — mã, runner, dashboard và PDF

- API client redacts URL/query values trước khi log; checker chỉ in loại exception, status/counts; không in key hoặc shop id. .env ignore rule hiện diện. Random state rõ ở estimator/bootstraps. requirements.txt có 130 pin == nhưng không có lock/hash; pip check sạch.
- Dashboard có 5 tabs; đọc outputs aggregate; không gọi API; không nạp raw/test. Tốc độ dưới 10s chưa kiểm chứng: AppTest bị ngắt vì harness treo, không phải bằng chứng app thật chậm.
- PDF builder chạy từ đầu vào aggregate vào temp; tạo 15 trang A4 và 15 trang render được; contact sheet đã xem. Bản hiện tại chỉ 7 trang. pdffonts/text extraction utility không có trong môi trường nên font được kiểm qua build/hiển thị, không xác nhận bảng font metadata. Script dùng path Windows tuyệt đối C:\Windows\Fonts\arial.ttf.
- Slides: không có PPTX/PDF/notes; python-pptx không có trong venv/requirements. Trước khi tạo cần dùng skill Presentations, pin thư viện dựng, chọn font và render/QA bản in.

## 10. Mười câu vấn đáp khó có thể gặp

| Câu hỏi | Bằng chứng hiện có / cách trả lời trung thực |
|---|---|
| 1. Vì sao test gọi là đạt cổng prereg khi config ghi >T nhưng code dùng [T,end)? | D-010 thừa nhận sai khác; ảnh hưởng chưa biết; không đọc lại test. Không khẳng định đã đạt đúng protocol. |
| 2. ROC OOF DEV ~0,497 và test ~0,703 nói gì? | Khác biệt lớn giữa DEV/test; chỉ một test window và tỷ lệ dương khác; không suy rộng/chọn model bằng test. |
| 3. 5.169, 5.174, 5.499 khác nhau do đâu? | 5.174 là DEV status-3 customers; 5.169 là model/test eligible; 5.499 là preflight lịch sử; decomposition chưa chứng minh. |
| 4. 24 combo đóng băng có phải 24 combo đều hiệu quả? | Không; 21/24 lift>1 trên 2.174 giỏ; lift là đồng xuất hiện, không phải nhân quả/lợi nhuận. |
| 5. 22 gift hay 27? | Money audit ghi 22 đơn quà; 27 trong bảng adjustment theo tháng không phải gift count. |
| 6. Revenue rule đã được kiểm độc lập với sổ kế toán chưa? | Chưa. Có rà mẫu 13 đơn và xác nhận owner; DuckDB không có trường tiền. Sensitivity/Spearman không phải đối soát độc lập. |
| 7. Vì sao 903/907 quà có độ tin cậy thấp? | Suy luận subset-sum duy nhất; cờ API đều false; rule không dùng tên/giá thấp; cần ghi giới hạn và xác nhận riêng về giảm giá thủ công. |
| 8. Vì sao không có DBSCAN? | Chỉ có tỉnh/thành; không tọa độ/mã vùng đủ chi tiết; lý do đã lưu. Không tuyên bố benchmark DBSCAN. |
| 9. Vì sao không dùng RMSE/MAE/R²? | Đây là phân loại; cần thêm giải thích vào báo cáo, hiện chưa thấy giải thích theo rubric. |
| 10. Sản phẩm nào thực sự sẵn sàng nộp? | Dashboard source, QA/demo script và 7-page PDF tồn tại; slides/screenshots/test audit thiếu; PDF hiện tại không phải bản 15 trang builder tạo. |

## 11. Kết luận và điểm dừng

Kiểm toán xác nhận nhiều nền tảng kỹ thuật/hash/runner an toàn, nhưng **chưa nên tiếp tục mục 4.2 hoặc nộp sản phẩm** trước khi chủ dự án duyệt các P0/P1. Không sửa source/tài liệu cũ trong lượt này; checklist từng mục nằm ở outputs/tables/audit_checklist.csv.

## 12. Ghi chú đóng hồ sơ — 2026-10-26

Các nhận định ở trên là ảnh chụp của cuộc kiểm toán trước khi hoàn thiện Ngày 3; danh sách thiếu, trạng thái sản phẩm và kết luận “chưa nên nộp” không còn mô tả trạng thái hiện tại. Các điểm nhất quán được xử lý trong lượt bàn giao cuối, còn giới hạn chưa giải quyết và kết quả kiểm tra mới nằm ở [nhật ký nhất quán](consistency_log.md), [báo cáo cuối](final_consistency_report.md) và `docs/PROGRESS.md`. Nội dung lịch sử được giữ nguyên để không viết lại hồ sơ audit ban đầu.

