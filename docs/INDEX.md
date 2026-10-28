# Mục lục bàn giao

## Nếu có 30 phút

Đọc [README](../README.md), [PROGRESS](PROGRESS.md) và [decisions](decisions.md) theo khối 0–15 phút trong lịch handover; sau đó bắt đầu [data_dictionary](data_dictionary.md), [data_governance](data_governance.md) và [day1_summary](day1_summary.md) trong khối 15–35 phút.

## Nếu có 1 giờ

Đi hết ba khối đầu của [lịch đọc trong handover](handover.md): README/PROGRESS/decisions; từ điển dữ liệu, governance và tổng kết Ngày 1; money definition, money audit và test report. Nếu còn thời gian, bắt đầu day2_summary trong khối 55–80 phút.

## Nếu có 2 giờ

Theo toàn bộ lịch 0–120 phút trong [handover](handover.md): phạm vi và trạng thái; nguồn/schema/governance; tiền, quà và test; mô hình/phân khúc/combo; dashboard/demo/hỏi đáp; cuối cùng chạy nhánh hậu mở an toàn.

## 1. Bắt đầu đọc từ đây — thuyết trình và bảo vệ

- [../slides/speaker_notes.md](../slides/speaker_notes.md) — Ghi chú theo từng slide; đọc khi tập trình bày PDF.
- [canonical_numbers.md](canonical_numbers.md) — Sổ số aggregate kèm cohort, đơn vị và nguồn; đọc khi cần trả lời câu hỏi về số liệu.
- [qa.md](qa.md) — Câu hỏi và câu trả lời bảo vệ; đọc khi luyện hỏi đáp.
- [qa_roles.md](qa_roles.md) — Phân vai trả lời và bổ sung; đọc khi nhóm chia phần chuẩn bị.
- [demo_script.md](demo_script.md) — Kịch bản demo offline bốn phút; đọc trước khi chạy dashboard.

## 2. Kết quả và giải thích

- [test_provenance_note.md](test_provenance_note.md) — Mô tả lần mở test, cách diễn giải và giới hạn; đọc trước khi nói về kết quả test.
- [test_report.md](test_report.md) — Báo cáo metric test aggregate; đọc khi cần xem kết quả đã lưu.
- [day2_summary.md](day2_summary.md) — Tóm tắt các nhóm khai phá và kết quả; đọc để nắm phần phân tích.
- [test_audit.md](test_audit.md) — Rà soát ranh giới DEV/test; đọc khi cần giải thích kiểm soát test.
- [metric_rationale.md](metric_rationale.md) — Giải thích các metric phân loại; đọc khi trình bày đánh giá mô hình.
- [analysis_plan_wp5.md](analysis_plan_wp5.md) — Giao thức WP5 đăng ký trước; đọc trước khi diễn giải khảo sát mô hình v3.
- [analysis_plan_wp5b.md](analysis_plan_wp5b.md) — Giao thức đăng ký trước cho luật, cây nông và hiệu chỉnh mua lại.
- [repurchase_wp5b_dev.md](repurchase_wp5b_dev.md) — Kết quả WP5b trên DEV, gồm các chiến lược thất bại do không có inner temporal fold.
- [analysis_plan_wp2.md](analysis_plan_wp2.md) — Giao thức A1 giữ chân và giá trị khách hàng DEV.
- [customer_value_dev.md](customer_value_dev.md) — Kết quả A1 về retention, thời gian mua lại, Pareto, CLV và RFM; chỉ DEV.
- [analysis_plan_f1.md](analysis_plan_f1.md) — Đăng ký trước kiểm tra định nghĩa sự kiện mua lại.
- [repeat_definition_f1.md](repeat_definition_f1.md) — So sánh Kaplan–Meier/retention theo định nghĩa ngày mua sau; DEV-only.
- [analysis_plan_f2.md](analysis_plan_f2.md) — Đăng ký trước dịch chuyển tỷ lệ nền DEV.
- [analysis_plan_wp3.md](analysis_plan_wp3.md) — Giao thức đăng ký trước A2 về giỏ đầu, chuỗi mua kế tiếp và 24 combo đã khóa.
- [product_journey_dev.md](product_journey_dev.md) — Kết quả A2 về sản phẩm giỏ đầu, chuỗi mua kế tiếp, vai trò sản phẩm và thước đo combo; chỉ DEV.
- [analysis_plan_wp4.md](analysis_plan_wp4.md) — Giao thức đăng ký trước A3 về mùa vụ, event window, kênh và điều chỉnh giá.
- [seasonality_business_dev.md](seasonality_business_dev.md) — Kết quả A3 và lịch hành động gợi ý từ chuỗi, sự kiện, kênh và điều chỉnh giá DEV.
- [analysis_plan_wp_olap.md](analysis_plan_wp_olap.md) — Giao thức đăng ký trước A4 về cuboid và DSS trên kho DuckDB DEV.
- [dss_design.md](dss_design.md) — Câu hỏi quyết định, KPI, chiều star schema, cuboid và phép OLAP đã chạy.
- [cohort_mismatch_analysis.md](cohort_mismatch_analysis.md) — So sánh mẫu DEV hiện tại, DEV snapshot đa mốc và test aggregate; đọc khi trình bày chênh lệch ROC.
- [course_alignment.md](course_alignment.md) — Ánh xạ khái niệm giáo trình với nơi áp dụng trong dự án.
- [data_gap_report.md](data_gap_report.md) — Ghi lại khoảng trống dữ liệu và phạm vi; đọc khi nêu hạn chế.
- [data_quality.md](data_quality.md) — Kiểm toán tỉnh/thành UNKNOWN và giới hạn ánh xạ địa chỉ; đọc trước khi diễn giải dữ liệu địa lý.
- [channel_monthly_coverage.md](channel_monthly_coverage.md) — Tổng hợp kênh đơn DEV theo tháng với ô nhỏ được ẩn; đọc khi cần căn cứ mức bao phủ nguồn/kênh.
- [holiday_time_supplement.md](holiday_time_supplement.md) — Lịch thủ công và so sánh rolling-origin DEV; khảo sát bổ sung, không thay mô hình chính.
- [cohort_reconciliation.md](cohort_reconciliation.md) — Cầu nối trực tiếp 5.499 → 5.174 → 5.169; đọc khi giải thích số cohort.
- [unknown_region_diagnostic.md](unknown_region_diagnostic.md) — Chẩn đoán aggregate UNKNOWN theo tỉnh/thành, không công bố địa chỉ.
- [leakage_review_cancel.md](leakage_review_cancel.md) — Ghi nhận rà soát bài toán hủy/hoàn; đọc khi được hỏi về nhánh này.
- [product_profile_top20.md](product_profile_top20.md) — Mô tả bảng sản phẩm theo support; đọc khi xem hồ sơ sản phẩm.

## 3. Dữ liệu và quy tắc nghiệp vụ

- [cohort_definitions.md](cohort_definitions.md) — Định nghĩa các cohort; đọc trước khi so sánh số lượng cohort.
- [data_dictionary.md](data_dictionary.md) — Từ điển trường nguồn và quyết định sử dụng; đọc khi cần tra trường dữ liệu.
- [data_governance.md](data_governance.md) — Phân loại và vị trí lưu trữ dữ liệu; đọc khi rà soát an toàn chia sẻ.
- [money_definition.md](money_definition.md) — Định nghĩa doanh thu ghi nhận hiện hành; đọc trước khi giải thích chỉ tiêu tiền.
- [money_audit.md](money_audit.md) — Kiểm toán tiền trên DEV; đọc khi cần xem căn cứ nghiệp vụ đã ghi.
- [architecture_matrix.md](architecture_matrix.md) — Thành phần và luồng dữ liệu; đọc để theo dõi kiến trúc từ nguồn tới dashboard.
- [data_protocol.md](data_protocol.md) — Protocol và nguồn sự thật đã khóa; đọc khi cần tra cấu hình/provenance.
- [point_in_time.md](point_in_time.md) — Ghi chú về tính khả thi point-in-time; đọc khi trao đổi về thời gian feature.
- [glossary.md](glossary.md) — Giải nghĩa thuật ngữ và mốc; đọc khi gặp ký hiệu trong tài liệu.
- [api_notes.md](api_notes.md) — Ghi chú API và giới hạn thu nhận; đọc khi cần biết phạm vi tích hợp nguồn.
- [pancake_endpoint_probe_20261028.json](pancake_endpoint_probe_20261028.json) — JSON aggregate của probe GET metadata; không chứa giá trị bản ghi.

## 4. Quyết định và nhật ký

- [INDEX.md](INDEX.md) — Mục lục các tài liệu bàn giao; mở khi cần tìm đúng file.
- [decisions.md](decisions.md) — Nhật ký quyết định theo thứ tự; đọc khi cần căn cứ cho lựa chọn dự án.
- [amendment_log.md](amendment_log.md) — Phạm vi Amendments 06–10 hậu mở và ranh giới an toàn.
- [PROGRESS.md](PROGRESS.md) — Trạng thái hiện hành và các mốc đã hoàn thành; đọc để cập nhật nhanh tình trạng.
- [consistency_log.md](consistency_log.md) — Nhật ký các vòng rà soát nhất quán; đọc khi cần truy vết hiệu chỉnh tài liệu.
- [final_consistency_report.md](final_consistency_report.md) — Báo cáo rà soát cuối; đọc trước khi nộp gói.
- [full_audit.md](full_audit.md) — Audit rộng và các điểm cần lưu ý; đọc khi cần lịch sử kiểm tra chi tiết.
- [cleanup_log.md](cleanup_log.md) — Baseline, danh sách dọn và kết quả đóng gói; đọc để xem thay đổi trong lượt này.

## 5. Bàn giao và vận hành

- [handover.md](handover.md) — Lịch đọc 1–2 giờ, luồng và bài tự kiểm; đọc khi bắt đầu bàn giao cho thành viên thứ hai.
- [schedule.md](schedule.md) — Mốc và phạm vi lịch; đọc khi chuẩn bị tiến độ nộp.
- [shared_release.md](shared_release.md) — Hợp đồng release dashboard shared; đọc khi cần kiểm tra giao diện chia sẻ.
- [submission_artifacts.md](submission_artifacts.md) — Danh sách PDF và aggregate đã commit; đọc khi xác nhận file nộp.
- [../README.md](../README.md) — Điểm vào repo và lệnh an toàn; đọc đầu tiên khi clone dự án.
- [demo_screens/02-segments.png](demo_screens/02-segments.png) — Ảnh minh họa tab phân khúc; xem khi chuẩn bị demo.
- [demo_screens/03-combos.png](demo_screens/03-combos.png) — Ảnh minh họa tab combo; xem khi chuẩn bị demo.
- [demo_screens/04-quality.png](demo_screens/04-quality.png) — Ảnh minh họa tab chất lượng; xem khi chuẩn bị demo.
- [demo_screens/05-model.png](demo_screens/05-model.png) — Ảnh minh họa tab mô hình; xem khi chuẩn bị demo.

## 6. Lịch sử — không dùng làm trạng thái hiện hành khi trình bày

- [cp1_review.md](cp1_review.md) — Rà soát thiết kế trước khi mở test; chỉ đọc khi cần lịch sử CP1.
- [day1_summary.md](day1_summary.md) — Tổng kết tại Ngày 1; đọc để hiểu bối cảnh ban đầu.
- [day1_walkthrough.md](day1_walkthrough.md) — Hướng dẫn Ngày 1 có nhãn lịch sử; không chạy lại các lệnh trong đó.
- [day2_walkthrough.md](day2_walkthrough.md) — Hướng dẫn cũ trước khi mở test; đọc chỉ để tra lịch sử quy trình.
- [day3_inputs.md](day3_inputs.md) — Danh sách đầu vào dự kiến trước khi hoàn tất dashboard; đọc chỉ để tra lịch sử.
