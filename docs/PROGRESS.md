# Project progress

Updated: 2026-10-28

## Trạng thái chốt hiện tại — 2026-10-27

- Hồ sơ nộp gồm dashboard offline 5 tab, báo cáo A4 15 trang, slide PDF in 15 trang, speaker notes, sổ số chuẩn, nhật ký nhất quán và báo cáo chốt. Dashboard smoke kiểm tra 10 CSV và 6 JSON aggregate. Hạn nộp là 2026-10-27; thời lượng và rubric chính thức chưa có trong hồ sơ.
- Test đã mở đúng một lần. Logistic Regression C=10 — mô hình chính theo D-005; Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính. ROC-AUC DEV OOF C=10 là 0,5096, gần ngẫu nhiên; ROC-AUC test khoảng 0,70 là tín hiệu yếu chưa được DEV xác nhận, không đủ để kết luận mô hình hoạt động tốt. Không dùng test để tinh chỉnh. Cấu hình ghi >T, evaluator dùng [T,end) (gồm ngày T); ảnh hưởng chưa xác định; không khẳng định tuân thủ đầy đủ giao thức.
- Cohort đã đếm trực tiếp: 5.499 − 325 khách chỉ có status 3 trước `analysis_start` = 5.174; − 5 khách chỉ có đơn quà = 5.169; phần dư chưa giải thích: 0. Combo chính là 24 cặp theo quy tắc ít nhất 4/6; 21/24 có lift > 1 trên 2.174 giỏ test. Dashboard UNKNOWN là 91,92% trên DEV+test; DEV-only 91,56% đơn và 90,73% doanh thu. Bài phân loại phản hồi bị bỏ qua do thiếu dữ liệu có nhãn. K=2 là phân đoạn mô tả theo tần suất mua (một lần / lặp lại), chưa xác nhận ý nghĩa kinh doanh.
- D-022 giữ chẩn đoán anchor ở trạng thái chưa làm: không mở Amendment 06, không fit mới. Hai thành viên cần tự chạy kiểm tra hậu mở an toàn, thử dashboard, tập demo 4 phút và trả lời ít nhất 10 câu chéo.
- Hậu kiểm trước cập nhật artifact: `run_all.py` pass (74 pytest, split/GET-only/locks/PII); dashboard smoke pass (5 tab, 11 CSV, 6 JSON); 17 hash bảo vệ khớp baseline; test-open lock giữ count=1; access log giữ đúng một `label_load` và một `behavior_load`. Sau cập nhật dashboard, smoke được chạy lại với 10 CSV.
- Đóng gói bàn giao theo D-023: thêm dữ liệu mẫu tổng hợp tại `data/sample/`, mục lục `docs/INDEX.md` và nhật ký `docs/cleanup_log.md`; không đổi kết luận và không di chuyển tài liệu trong `docs/`.
- Hoàn tất rà soát phát hành aggregate: dòng của 20 địa phương có dưới 10 đơn mỗi nơi được gộp (38 đơn; 16.674.000 VND), bảo toàn tổng orders/doanh thu; giữ UNKNOWN và giữ count dòng gift-line. Báo cáo A4 và slide PDF được dựng lại, mỗi file 15 trang; kiểm tra hiển thị và test tập trung (16 passed).
- Kiểm tra clone sạch tại `ef82631`: `run_all.py` clone mode pass, 107 passed và 1 skipped do thiếu DuckDB DEV restricted; PII scan và dashboard smoke pass. Test đơn vị trên checkout gốc có dữ liệu: 108 passed.

## Locked scope and active decisions

- Snapshot `20261024T052943Z`, 12.011 orders; `split.yaml` and `split.lock.json` remain unchanged: N=180, L=7, W=180, test `[2025-10-22,2026-04-20)`, `DATA_CUTOFF=2026-10-24` exclusive. Amendment 01 remains `analysis_start=2024-04-01`; `N=365,W=365` remains infeasible; `H_obs=[analysis_start,T)`.
- Amendment 02 remains immutable history. Amendment 03 is active and hash-verified. The owner replaced the old 5% gate after observing 701/6.400 (10,95%), based on business knowledge that status 3 is recognized revenue and price differences can be fees/promotions. This was not based on labels/test behavior. Evidence is 13-order manual review plus verbal owner confirmation; `dash_*` remains blank.
- New money audit: 6.400 status-3 DEV orders; 22 gifts; 2 negative recognized-revenue orders (0,03%); 1% stop gate passed. `price_adjustment` is retained; payment fields do not filter orders.

## [LỊCH SỬ — trước khi mở test] Day 2 completed

- Preprocess: 286 missing-customer orders excluded from customer-level features; 22 gifts excluded from customer behavior; 5 no-line orders excluded from baskets. DEV labels across multiple historical T: 3.508 samples, 260 positive (7,41%); at that historical point, test labels and behavior were not loaded.
- Segmentation: K=2, silhouette=0,508. Single-order counts are reported by cohort: DEV status 3 4.526/5.174 (87,5%); scoring 4.530/5.169 (87,6%). Profiles and A/B sensitivity are in `outputs/metrics/day2_segmentation.json`.
- Classifier: best=logistic_regression, PR-AUC=0,0699, ROC-AUC=0,5096; temporal folds are customer-disjoint and all preprocessing fit inside train folds. Model is development-only.
- Baskets: 6.031 product baskets eligible, 68 rules and 23 combos. No cost/profit calculation was made.
- **[LỊCH SỬ — Day 2 trước khi mở test]** Summary, walkthrough, FAQ and Day3 input inventory were present. At that point Day 3 had not started and test was unopened.

## [LỊCH SỬ — runner trước khi mở test] Audit / runner

- Trước khi có test-open lock, `scripts/run_all.py` từng profile/reuse kho DEV, kiểm tra cổng tiền và chạy notebook Ngày 1/2. Không dùng mô tả này cho runner hiện tại: sau mở test, nhánh hậu kiểm chỉ xác minh khóa/split, GET-only, chạy pytest và quét PII.
- Pre-label evidence sealed in amendment 03 records two `eligibility_count` entries, zero test-label and test-behavior reads, and Day 1 artifacts with `test_labels_loaded=false`. Day 2 uses dev labels only.

## [LỊCH SỬ — trước khi mở test] Day 2B bounded follow-up

- Amendment 04 sealed before new experiments: `e76ee390e227a569a39ab5f4fe7c7489572a06323d6d2f1bc6c8b72fa52ea6f8`. Original LR remains SHA `0ac767d24c641f50bdc19634e590dc45a92d9e4cd5513d02871fac50b109cd4a`; no post-result reselection.
- Combo clean: 6.031 eligible baskets before and 5.684 after dropping zero-price item lines; one registered run. Companion proposals await owner confirmation.
- Segmentation: K=2 retained; K=3/4 compared with five fixed seeds; rule-based groups and large-value proxy stay separate from claims about customer departure.
- Repurchase feature-v2 trial: one run, signal_supported=False; conclusion: không đủ bằng chứng để dự đoán mua lại từ dữ liệu hiện có.
- Cancel/refund trial: skipped_preregistered_positive_support_gate; positive counts per validation fold `F1: 30 / 1330, F2: 13 / 801, F3: 6 / 920, F4: 1 / 726, F5: 18 / 1007`; attempts=0.
- **[LỊCH SỬ — kết thúc Day 2B trước khi mở test]** Test labels/behavior remained false and Day 3 had not started. See `docs/day2_summary.md`, `docs/day2_walkthrough.md`, `docs/leakage_review_cancel.md`.

## Day 3 pre-open freeze (historical)

- Chủ dự án đã ra lệnh mở test một lần và tiếp tục Day 3. Amendment 05 khảo sát 30.049 dòng DEV; API bonus flag đủ phủ nhưng không bật lần nào; không có giá bán thực riêng hay tên danh mục lịch sử. Dòng quà được phân loại theo flag/giảm 100%/subset sum chính xác duy nhất tối đa 6 dòng; subset suy luận có độ tin cậy thấp.
- Phân loại DEV: 907/30.049 dòng gift (4 direct zero-price, 903 inferred-subset); 24 combo đáp ứng quy tắc xuất hiện ít nhất 4/6 ô nhạy cảm và có trong ô chính `all_gift_sources`/support 0,05; 6.006 giỏ đủ điều kiện sau loại mọi nguồn quà. Nguồn: `outputs/metrics/day3_combo_prereg.json`. Product profile tính trên toàn bộ dòng status-3 DEV; không lọc theo tên sản phẩm.
- Đã khóa danh sách chính xác mô hình, 24 combo, segmenter, ngưỡng, độ đo và quy tắc diễn giải trong `config/amendment_05_test_open.yaml`, SHA `7964367ae28aa10d31e4c573772b7c3bc22b3f8b3d340c3292d0593bf6f30272`. Trước mở, log vẫn chỉ có hai bản ghi eligibility; chưa có nhãn/hành vi test.
- Tiền kiểm chỉ DEV xác nhận 5.169 khách đủ điều kiện, scoring v1/v2 và gán phân khúc K=2/3/4 chạy được; 6 test focused pass. `scripts/run_all.py` đã có nhánh hậu kiểm không fit/rerun sau khi tạo test lock.
- Lần gọi evaluator đầu dừng trước khi tạo test lock do YAML ngày ở dạng date; không có test field nào được đọc. D-009 ghi sự cố và cách sửa; cấu hình được khóa lại với hash mới, không đổi phương pháp.
- **[LỊCH SỬ — freeze trước mở test]** Tại thời điểm đóng băng, test chưa mở; bước kế tiếp khi đó là chạy evaluator đúng một lần. Kết quả và sai khác protocol sau đó: `docs/test_provenance_note.md`.

## Tiếp tục bàn giao — hậu mở test và mục 4,1

- Khóa `outputs/metrics/test_opened.lock.json` còn nguyên (`test_open_count=1`); `outputs/logs/test_eval_access.jsonl` vẫn có đúng một `label_load` và một `behavior_load`. Không chạy lại evaluator, không nạp dữ liệu test.
- Ghi D-010 vào `docs/decisions.md`: kết quả được báo theo cách chạy thực tế `[T,end)`; khác biệt với quy tắc ghi trước `>T` được công khai và ảnh hưởng chưa xác định.
- Sửa các lời gọi `add_table` sai dạng đối số trong `scripts/build_report_pdf.py`; trình biên dịch Python xác nhận cú pháp hợp lệ.
- `scripts/verify_day3_locks.py` xác nhận các nguồn hash đã khóa, kết quả và access log còn nguyên. `scripts/run_all.py` chạy đúng nhánh hậu kiểm sau mở test; 73 pytest đạt, chính sách API GET-only đạt, quét PII đạt. Không notebook, evaluator hay bước fit mô hình nào được chạy.
- Việc kế tiếp: viết `docs/test_audit.md`, đồng bộ tài liệu kết luận DEV/test rồi hoàn thiện dashboard, PDF, slides, FAQ và kiểm tra cuối.

## Giai đoạn 1 — đồng bộ provenance và diễn giải test

- Tạo `docs/test_provenance_note.md`; D-010 và tài liệu test/QA/bàn giao/demo/dashboard/PDF builder trỏ tới ghi chú. Ghi rõ cấu hình `>T`, thực tế `[T,end)`, ảnh hưởng chưa xác định, không rerun.
- Đồng bộ hai Logistic Regression: C=10 là mô hình chính được giữ theo D-005; feature-v2 C=0,1 là khảo sát bổ sung. Bổ sung point estimates và CI; sửa PDF builder từ câu khẳng định mọi cặp đều có lift > 1 thành 21/24 cặp.
- Gắn nhãn lịch sử các trạng thái chưa mở test trong walkthrough, Day3 inputs và progress; nối kết luận DEV với kết quả test. D-008 có đính chính hash giữ lịch sử; ghi D-011–D-018 về quà thủ công, timezone, status, mốc cửa hàng, đơn 0 đồng, diễn giải tiền, khóa HMAC và N=180.
- Cập nhật handover với danh sách file không chia sẻ: raw/restricted/quarantine, customer-HMAC/label-level/predictions, model artifacts và env credentials.
- Kiểm tra an toàn: `scripts/run_all.py` hậu mở đạt; verify split/GET-only/Day3 locks/PII pass; pytest 73 passed (run_all: 11,94 giây; lần pytest riêng: 9,79 giây). Không chạy evaluator, notebook hoặc refit; khóa và access log giữ nguyên.
- Tiếp theo: cohort definitions, EDA DEV, ma trận kiến trúc, giải thích metric, notebook markdown, test audit tổng hợp; xem kế hoạch đã duyệt trong handoff.

## Giai đoạn 2 — cohort, EDA DEV, kiến trúc và ranh giới test

- Tạo `docs/cohort_definitions.md`: định nghĩa riêng snapshot 12.011, 476 pre-analysis, 6.517 DEV, 6.400 status 3, 5.174 khách DEV status 3, 5.499 preflight N=180, 5.169 scoring đã freeze, và 3.508 mẫu nhãn DEV qua nhiều mốc T/260 dương. Tại thời điểm ghi lịch sử, quan hệ cohort 5.499/5.174/5.169 chưa xác minh; cầu trực tiếp được bổ sung sau đó ở phần trạng thái hiện hành.
- Tạo script chỉ đọc `scripts/build_eda_dev_artifacts.py`, JSON aggregate và 5 hình `outputs/figures/eda_dev_*.png`; tạo `notebooks/01b_eda_dev.ipynb` chỉ trình bày JSON/hình đã lưu, chưa chạy notebook. EDA dùng `[2024-04-01, 2025-10-22)`, mẫu nhãn historical DEV, không đọc feature scoring của cohort 5.169, raw snapshot hay dữ liệu test. Output không chứa khóa/định danh hoặc dữ liệu từng dòng.
- Notebook 01b ghi 10 quan sát có số lượng/cỡ mẫu và giới hạn diễn giải. Tạo `docs/architecture_matrix.md` với năm tầng, câu hỏi nghiệp vụ và Mermaid; `docs/metric_rationale.md` giải thích metric phân loại; `docs/test_audit.md` ghi rà soát tĩnh và khác biệt ngày T.
- Notebook 02–05 có ghi chú lịch sử và guard đầu cell trước import project/model. Canonical SHA-256 của code-cell outputs trước sửa và sau sửa trùng nhau; notebooks 01–05 chưa bị chạy. Hash baseline: 01 `d151ae1616828fd03842e91abde39960f92235102bfee7b219a44026c64a4300`; 02 `1ee8273bee80d3e2f4a5143c8e6f67a75d27a3114e2b20079b6fa27e62b6de4d`; 03 `366332e0ed4948bad8ec3ea13cf50d5937bbf04a9a3ca3638d5dc4fb73d93baf`; 04 `2793eeb1afacb26ae5c9eee1344187bfb65aa901ca9f0a0b051ccb4e56237d2c`; 05 `a06536c5391b6d6b6bb5cf3ea61d7f3c146203db89acd1660c8cd5dd7c04c28f`.
- Test tổng hợp xác nhận `make_customer_features` chỉ giữ đơn trước T (1 passed); `scripts/run_all.py` đạt 74 pytest, split/snapshot/amendment/test-open locks, GET-only và PII scan. PII tripwire ban đầu bắt nhầm đuôi float của quantile VND; làm tròn thống kê VND đến đồng và lần scan cuối đạt. Không thay config/lock/metric test; không chạy evaluator, notebook hoặc refit.
- Ghi D-019 về cohort chưa đối soát và D-020 về DEV-only EDA/guard notebook. Bước kế tiếp: hoàn thiện dashboard smoke, báo cáo PDF và bộ slide theo phương án PDF fallback nếu không có runtime PPTX được hỗ trợ.

## Giai đoạn 3 — dashboard, báo cáo và trình bày

- Lần smoke ban đầu có 11 CSV; sau đó bỏ tỉnh/thành khỏi dashboard và gỡ ảnh tổng quan cũ. Trạng thái hiện hành: 5 tab, 10 CSV và 6 JSON aggregate, được smoke kiểm tra; không AppTest/API. Còn 4 ảnh tab trong `docs/demo_screens/` cùng PDF in làm phương án demo offline.
- Tạo lại `report/xoaif_report.pdf`: 15 trang A4, đã render và rà tiêu đề, bảng, chân trang cùng các trang về OOF, test một lần và quyết định. Trang test nêu đúng C=10 chính, v2 khảo sát bổ sung, và khác biệt `>T`/`[T,end)` chưa rõ ảnh hưởng.
- Tạo `slides/xoaif_print.pdf` gồm 14 trang ngang và `slides/speaker_notes.md` với lời dẫn, nguồn repo, phân vai A/B và việc cần tập trước bảo vệ. Bản in đã render/rà trực quan. `python-pptx` không có trong môi trường; không cài gói mới và không tạo PPTX. README nêu rõ PDF fallback.
- `scripts/run_all.py` hậu mở đạt lần cuối: split/GET-only/Day 3 lock pass, 74 pytest pass, PII scan pass. Một helper chụp ảnh CDP dùng một lần bị quét nhầm như HTTP ngoài client; helper đã được gỡ sau khi chụp đủ ảnh và lần hậu kiểm cuối đạt.
- Không chạy lại evaluator, không đọc thêm dữ liệu test, không chạy notebook/refit; không đổi cấu hình/khóa/kết quả test. Hạn nộp là 2026-10-27; thời lượng thuyết trình và rubric chính thức chưa có trong hồ sơ.

## Giai đoạn 4 — rà soát nhất quán cuối

- Tên mô hình thống nhất: Logistic Regression C=10 — mô hình chính theo D-005; Logistic Regression feature-v2 C=0,1 — khảo sát bổ sung theo Amendment 04; không thay mô hình chính.
- Công bố CI ROC-AUC, CI AP và paired ΔAP point/CI cho cả hai mô hình ở test; threshold ghi trước được mô tả theo từng classifier và luôn kèm caveat sai khác ngày T. D-001–D-020 và khóa test giữ nguyên; diễn giải mới được ghi từ D-021.
- Bảng combo nêu 24 cặp chính theo quy tắc ít nhất 4/6 ô và có mặt ở ô chính; kết quả test là 21/24 trên 2.174 giỏ. Bảng phân khúc ghi cohort scoring 5.169 và tách tỷ lệ DEV 4.526/5.174 với tỷ lệ scoring 4.530/5.169.
- Deadline 2026-10-27; thời lượng/rubric chưa có trong hồ sơ. Mỗi thành viên cần luyện 10 câu chéo. Chưa chạy chẩn đoán anchor DEV do cần rolling-origin và fit mới; ghi tại D-022.
- Đã dựng lại báo cáo 15 trang và slide in 14 trang; rà trực quan các trang báo cáo 7–15 và slide 6–14, gồm caveat, metric, combo và checklist trình bày. Ảnh tổng quan/mô hình trong `docs/demo_screens/` đã được cập nhật và kiểm tra. Consistency scan ban đầu tìm 5 thiếu sót về caveat/tên chuẩn ở `qa_roles.md` và nhật ký; đã sửa, đồng thời smoke test phát hiện và sửa kỳ vọng JSON 5→6 để khớp sáu file dashboard thực đọc. Hai lượt consistency scan cuối không còn findings. Không chạy evaluator, notebook hoặc fit/refit.
# Cập nhật bàn giao — 2026-10-27

## Giai đoạn 2 — Pha A, A5

- WP5b đã đăng ký trước (commit riêng `a2a46d5`) và chạy trên cùng DEV snapshots/folds WP5. S1/S3/S5 hoàn tất; S2/S4 thất bại do không có inner temporal folds hợp lệ ở cả 5 outer fold. Không chọn ứng viên; không thay D-005. Báo cáo: `docs/repurchase_wp5b_dev.md`.
- Chưa mở Pha B/HO2. Không chạy evaluator test hay đọc test raw.

- Cohort (trạng thái trước đếm raw pre-T ngày 2026-10-27): script reconcile chỉ so sánh aggregate warehouse; chưa có cầu nối theo điều kiện. Đã được supersede bởi đếm trực tiếp tại `docs/cohort_reconciliation.md` và `outputs/tables/cohort_bridge_verified.json`.
- Sai khác ngày T: không tìm thấy artifact prediction đã lưu trong `outputs/`; theo phạm vi Amendment 06, không tái tạo prediction và dừng tiểu mục. Không có metric sensitivity mới.
- UNKNOWN (ghi chú trước chẩn đoán raw pre-T ngày 2026-10-27): warehouse khi đó không chứa các trường source/address; đã được supersede bởi đếm DEV-only trong `docs/unknown_region_diagnostic.md`.
- Handover/refesh: ghi phân vai theo `docs/qa_roles.md` và quy trình refresh theo lô, không chạy extractor.
