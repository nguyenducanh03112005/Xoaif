# Nhật ký thay đổi 06-HO2 Gate B revision 3

Căn cứ so sánh file: commit Gate B revision 1 `f67b4b2`; ghi nhận thêm các sửa đổi sau Gate B rev2 `19293fa`. Tất cả thay đổi đều trước khi mở HO2; không đọc outcome HO2. Hash cũ lấy từ Git blob, hash mới lấy trực tiếp từ byte file hiện hành. Lý do từng hàng được ánh xạ cụ thể trong script sinh log.

| File | SHA-256 cũ (f67b4b2) | SHA-256 mới | Lý do | Ngày |
|---|---|---|---|---|
| `.gitattributes` | `95565d921701721d188c72f3854355ac62476fc141aac1ac570567784b0f6228` | `212a00554256871982af5d63aa79b09184fc68c0dc476ade8ba3195a31bffd0e` | Thêm quy tắc giữ nguyên byte cho lock 06; tác động cách Git lưu EOL, không đổi nội dung phân tích. | 2026-10-29 |
| `.gitignore` | `54526752ffdf20abf6c26fbd28ebd248ecb08182d970fbd3dc04a6b8094a0e81` | `d09f804eae7a8600ee6b8a6b04d70be1f9f1fdabae6f50259d11a88955007e60` | Cho phép commit aggregate Gate B đã rà soát và tiếp tục loại model/dry-run local; tác động phạm vi file được track. | 2026-10-29 |
| `config/amendment_06_ho2.lock.json` | `a6c751a50625d8d98ffb2a8c10573d61cac9158e21dd3e16493715a3c413e94d` | `42e044da1bda300f1fa521fcaf9530b08acc9864ef0be303ae26250c7db4abde` | Thay lock rev2 bằng rev3, băm 85 nguồn và giữ test_opened=false; không mở HO2. | 2026-10-29 |
| `config/amendment_06_ho2.yaml` | `e850af1e85179ebb2c3598fb7f78adb5fd1051e53a80b4473bc0c8300ad97b4c` | `51713add5f3b09a0340e2b87ba2639567cd2567faf7c8d4ab1242bacd3c44342` | Cập nhật từ rev2 lên rev3: đặt supersedes, dung sai H4 1e-9, giữ ngưỡng/số nhóm và trạng thái đóng; ảnh hưởng cấu hình giao thức. | 2026-10-29 |
| `docs/amendment_06_gate_b.md` | `d115234b71524bdcaa07f92ae34b12bc24268738016e5904f925a15e6588382c` | `f04be7d7464ba7b4720e209606e3417c928624da483f23839cbb6a716dd1b122` | Sinh báo cáo Gate B từ lock/hash; tài liệu tổng hợp, không có outcome HO2. | 2026-10-29 |
| `docs/amendment_log.md` | `2722c4fd00cd4b31f7b5c4b33b399bd745a0853b90f9529351f914cda6851327` | `f6753dfee3c06562cce4ca96858e2477f7f2a3d680c3a6a59ef328eeb01f3b49` | Ghi lịch sử amendment và ranh giới chưa mở HO2. | 2026-10-29 |
| `docs/analysis_plan_amendment06_ho2.md` | `cd9197008d6b41f07df51f117886dfd883e7234b514bafefddbd3182b31584a8` | `59d277b42dc355ff0a193c359b230fa69d64a0d922aa8b56fe68dcfc9567a9ab` | Giữ protocol rev2 và bổ sung quy tắc dung sai H4 rev3; ngưỡng/nhóm và các giả thuyết không đổi. | 2026-10-29 |
| `docs/analysis_plan_gateb_r2.md` | `ABSENT` | `ff8c823e1989e536f75b8ed09a3fc399e3c10af041d678c4672e254ec198be8e` | Đăng ký quy tắc RR/power trước kết quả DEV; ảnh hưởng quyết định phân loại H2. | 2026-10-29 |
| `docs/analysis_plan_gateb_r4.md` | `ABSENT` | `b6dac1cd2efd64dcd11f92a93d5570a6e7c2330d7d1db0d9f34c0a23c252e85c` | Đăng ký nhóm/metric và tiêu chí H4/H5 trước hiệu chuẩn DEV; không dùng HO2. | 2026-10-29 |
| `docs/analysis_plan_gateb_r5.md` | `ABSENT` | `e9195f75d76a1326c816b7ebb67e4051771d0b77d9883b42404ced0c3861a6e9` | Đăng ký quần thể fit/định nghĩa chiến lược trước khi tạo artifact R5. | 2026-10-29 |
| `docs/analysis_plan_gateb_r6_fix.md` | `ABSENT` | `bb1de6adf63dd0bfa31211d44e307bc1d57652c5a0e97221ffc93d32c5308675` | Đăng ký dung sai H4 trước commit mã; giữ nguyên ngưỡng và tối thiểu 4 nhóm. | 2026-10-29 |
| `docs/canonical_numbers.md` | `dc64371456d58696b6d9387621c60ed6af256eb1ff0fe02f2299f65b9b4fb660` | `6af06bc7e3f2083dcac01c2f0553965b9b9fc2133b9026bc39e32395bd193bc8` | Đồng bộ số nguồn R2/R4/R5 và provenance; không thêm outcome HO2. | 2026-10-29 |
| `docs/decisions.md` | `6e0a4638978de37cf0cd0afcca7cc948d897028692d914e920850646d1492886` | `0f8e29eba0f8c89cea7ff7453686bc93cd69fd2cd3e4025e8bac76236cb95fa3` | Ghi quyết định/phạm vi Gate B và các lần sửa đã duyệt; không thay split/test lock. | 2026-10-29 |
| `docs/gateb_r2_results.md` | `ABSENT` | `f5cc8c5a0dffe52381be7ed9bbfcba75852de9d25ff29e2df49f4b881b4460e2` | Báo cáo RR snapshot và đầy đủ bảng power H1/H2 sau đăng ký; chỉ DEV/aggregate tham chiếu, không có HO2 outcome. | 2026-10-29 |
| `docs/gateb_r4_results.md` | `ABSENT` | `d8ee4e2972a8b54e80099382f8ec72a912bbfa1d91cd647efa4cbcaa5f6831ce` | Ghi ngưỡng ổn định nhóm DEV và k_DEV; đầu ra hiệu chuẩn, không chọn nhóm bằng outcome HO2. | 2026-10-29 |
| `docs/gateb_r5_results.md` | `ABSENT` | `1f8a4949ef4157cfe6fc518630adfd41bede67fac635cec687f8ed0a00406803` | Báo cáo quần thể fit và hash chiến lược; không trình bày metric in-sample như xác nhận. | 2026-10-29 |
| `docs/ho2_access_audit.md` | `ABSENT` | `c97ea3640061fd1c9b551fa6bd5fcc1866e32bb3bead77afe74b444f18624d16` | Liệt kê đường nạp, metadata ngày và giới hạn pháp y trước Gate B. | 2026-10-29 |
| `outputs/metrics/gateb_r2_power.json` | `ABSENT` | `8a8113db17c6bc59b53c806f4790f727905c0d663807059fbab141ba2d54031f` | Lưu power grid đã đăng ký cho hai mức prevalence và các effect size; thiết kế, không phải kết quả HO2. | 2026-10-29 |
| `outputs/metrics/gateb_r2_rr_dev.json` | `ABSENT` | `ac0572eb47fe43d9768a8ae0b7bd783839d573a852b7f05f3127b82fda474d37` | Lưu RR và bootstrap CI theo khách từ snapshot DEV; đầu ra aggregate phục vụ quyết định H2. | 2026-10-29 |
| `outputs/metrics/gateb_r4_dev_calibration.json` | `ABSENT` | `60617a9c181d0cd583687d69f84adeba5203c967095d152308d904cd00f127b5` | Lưu thống kê tham chiếu S6/RFM và k_DEV từ DEV; aggregate dùng đóng băng tiêu chí. | 2026-10-29 |
| `outputs/metrics/gateb_r5_strategy_freeze.json` | `ABSENT` | `bfac6b9d057189d9655693248532a673e0d2c4c85721a0214a0f7fc9a668cbee` | Ghi metadata, quần thể fit và hash artifact DEV; bản sau 94a1fae thêm mean/scale cho hai baseline mô tả. | 2026-10-29 |
| `outputs/models/gateb_r5/s3_final_dev.joblib` | `ABSENT` | `63e47afbe0a1ef73c01d0be2974c354d753a7299f3d1952146b91bd8b2d1706b` | Artifact cây final-fit DEV được hash để chấm cố định; không fit trên HO2. | 2026-10-29 |
| `outputs/models/gateb_r5/s6_final_dev.json` | `ABSENT` | `17af23fa3a84a40c357856271489badd6a1061fd15cac62ace1573627b64d048` | Map nhóm-rate final DEV được hash để chấm cố định; không fit trên HO2. | 2026-10-29 |
| `outputs/models/gateb_r5/v3_final_dev.joblib` | `ABSENT` | `fc04ee70693da1a1e16350b99acf80b335705000dac35ba67bde63ef9c5d348b` | Artifact Logistic Regression final-fit DEV được hash; không chọn trên HO2. | 2026-10-29 |
| `scripts/analyze_gateb_r2_dev.py` | `ABSENT` | `a10e17b41abab68209a439d3f0e7a3589c114139563c7244e227234233cede5f` | Tính RR DEV theo snapshot và bootstrap cụm khách; đường phân tích DEV-only. | 2026-10-29 |
| `scripts/audit_committed_aggregate_dates.py` | `ABSENT` | `3e758ce088e573bc9883fbbd8bf253798636accb97f8973828ef677e69dc82ed` | Đọc riêng trường thời gian của aggregate đã commit để kiểm tra phạm vi ngày; không đọc raw. | 2026-10-29 |
| `scripts/build_amendment06_gateb_report.py` | `ABSENT` | `7ec1459857947140cb069eb37507775900cc99d4742a4921ff9cc819c52cb92a` | Sinh báo cáo và bảng hash từ lock/file thật; thay thế hash báo cáo chép tay. | 2026-10-29 |
| `scripts/build_amendment06_lock.py` | `ABSENT` | `49f00f4966be492bf53f4fa083e5e07428c947f94f7f9669565ffc582313722a` | Sinh lock trực tiếp từ byte file/config/aggregate DEV; không chép hash tay. | 2026-10-29 |
| `scripts/build_amendment06_revision_log.py` | `ABSENT` | `fa77520d2753330faa8fcb9e78a19c370476d8d4c84b988d58a9d980545d8e28` | Sinh nhật ký từ Git blob và byte hiện hành; đồng thời kiểm toán khác biệt JSON R5. | 2026-10-29 |
| `scripts/calibrate_gateb_r4_dev.py` | `ABSENT` | `9c65803bce23c294b689110b96e5fa6051aff1dd13a44dad98deb76073a01282` | Tạo tham chiếu H4/H5 trên các nửa DEV đã đăng ký; không đọc HO2. | 2026-10-29 |
| `scripts/evaluate_holdout2_once.py` | `ABSENT` | `08ae2147ab7704d0f758a548d95a083e1bb6b577ab3395e3ff5cad631dab2ed0` | Chuyển validator/open-lock sang rev3 và dùng helper H4 dung sai; không gọi evaluator hoặc mở HO2 trong lượt này. | 2026-10-29 |
| `scripts/fix_sealed_eol.py` | `8fe7f0b7e4b79987456ef5b8765443ab942d16823015a917e01ed00bdf20e920` | `8c9ae853370e33f0d089843e6799a24b861db7665805f5214d5d063815c65e06` | Tạo quy tắc -text và giữ byte của file hash-sealed; không đổi nội dung số liệu. | 2026-10-29 |
| `scripts/freeze_gateb_strategies_dev.py` | `ABSENT` | `984740129ebc9abe5ad7ba727f40950d5413fd3658823caa94f66b118ee6719d` | Fit/chốt S3/S6/v3 trên DEV và ghi metadata; ở 94a1fae bổ sung scaler mean/scale để dựng score baseline. | 2026-10-29 |
| `scripts/run_all.py` | `ea908800c999a84aa8c9bc0467d84a26c386a7019026fa774b8463c94e82c852` | `c28c211413329602834f890be345ed141e396b34ea0a9a87c908fa7972b86b3c` | Đổi bước verify lock từ revision 2 sang revision 3 trước test/PII/dashboard smoke; vẫn không gọi evaluator HO2. | 2026-10-29 |
| `scripts/summarize_gateb_r2_power.py` | `ABSENT` | `15913f5a2b67a8d8bb61be405f9207a470905ca741c2f597356f6475299a64c0` | Tính power grid R2 theo n tiền T2 và prevalence tham chiếu; không nạp outcome. | 2026-10-29 |
| `scripts/verify_gateb_lock.py` | `ABSENT` | `967e71f8f9522145b101db11b430cea2022204841ed2d167bfc9c44e2c9cf76d` | Kiểm tra hash, EOL, giả thuyết và trạng thái khóa; được run_all gọi trước test suite. | 2026-10-29 |
| `src/features/holdout2_access.py` | `ABSENT` | `93afe62323ab10ddb5e90889486b6acc018adcc83a8931b22bd4f1590651359c` | Yêu cầu lock mở revision 3 khớp hash config/protocol/evaluator; tiếp tục chặn mọi nạp trước lock. | 2026-10-29 |
| `src/features/holdout2_features.py` | `ABSENT` | `826c5085a2b3fe0315a4f8501b13155e5f6b4ed6eb6db3e07f5639f1a72f8eac` | Tách feature trước T2 và outcome sau T2 theo ngày địa phương; ranh giới thời gian cho evaluator. | 2026-10-29 |
| `src/features/holdout2_metrics.py` | `ABSENT` | `b2f4b36423171315838beef110ca32c2ee0bf2a3809effea3157278ea60d0c1c` | Thêm helper H4 dùng dung sai 1e-9 và ngưỡng tối thiểu 4 nhóm; giữ metric/bootstrap/Holm còn lại. | 2026-10-29 |
| `tests/test_gateb_aggregate_date_audit.py` | `ABSENT` | `f751fe5090024620e4db41e059fa66a5b3303939a34e6e56d6f40fc5982c8041` | Kiểm tra parser và date-only scan của aggregate; không đọc nội dung ngoài cột ngày. | 2026-10-29 |
| `tests/test_gateb_lock_verification.py` | `ABSENT` | `582bd4b276598c01343581332290efdfbfcc8afd99a6d023026d2878e6c202c4` | Đổi fixture/expectation sang lock rev3; kiểm tra hash sai và output HO2 tồn tại bị từ chối. | 2026-10-29 |
| `tests/test_gateb_r4_calibration.py` | `ABSENT` | `dec6c98324f26920588db30aeedc158ab7b182349446892ebf665165a5e754c4` | Khóa số nhóm/điều kiện H4/H5 từ hiệu chuẩn DEV. | 2026-10-29 |
| `tests/test_gateb_r5_freeze.py` | `ABSENT` | `79843a63f32bdc279d059effd4da9890bf71f2fbdefd26eda76f0a13de9d76e0` | Khóa dấu/chiều baseline và metadata final-fit từ DEV. | 2026-10-29 |
| `tests/test_gateb_report_hashes.py` | `ABSENT` | `16197f7b6fb1c43796485e2ffb276624102d401c7c52e1bb5a025dfa71bda6ff` | Đối chiếu hash/report hypothesis và có mặt bảng G1, ghi chú prevalence G2, đề xuất G3. | 2026-10-29 |
| `tests/test_ho2_eligibility_gate.py` | `48acab60c8bb5ccae40ca5aee1b65c24fbdacab97ea37b5dced2c3751b0aa8b9` | `c7d380abbf58a389414074503aa33e0dfd0491c621a1a202ee8dc9aec40d1633` | Thêm/sửa kiểm thử `test_ho2_eligibility_gate.py` để khóa hành vi tương ứng; chỉ fixture tổng hợp, không đọc HO2. | 2026-10-29 |
| `tests/test_holdout2_feature_boundary.py` | `ABSENT` | `3ea31c9975fc597e5176f19fa119112e9687bec3d275063f4bdcb6a287cc14cd` | Kiểm tra feature <T2, outcome boundary và loader gating bằng dữ liệu tổng hợp. | 2026-10-29 |
| `tests/test_holdout2_metrics.py` | `ABSENT` | `34d9cbe5a403c871bd82dc132617232dec37743b15b76df741e3b4f80dbf0811` | Thêm ca rho tổng hợp: 1/2 swap n=8, identity/near-1 và swap n=6, dưới 4 nhóm. | 2026-10-29 |

## Kiểm toán `gateb_r5_strategy_freeze.json` — a052bae so với hiện tại

| Phiên bản | SHA-256 byte gốc | SHA-256 chuẩn LF | SHA-256 chuẩn CRLF | CRLF trong byte gốc |
|---|---|---|---|---:|
| a052bae | `642f29877b7b39ea44494101b519d90154d56a899a220173995258d2bdbfab68` | `642f29877b7b39ea44494101b519d90154d56a899a220173995258d2bdbfab68` | `92f04a2e6e9ffa3fbd193b5e3cbbbfb4fe5c5e4dc63a31a3963af60691ead845` | 0 |
| hiện tại | `bfac6b9d057189d9655693248532a673e0d2c4c85721a0214a0f7fc9a668cbee` | `b262db2180634a55cd00714167c93da60f4026c0465dd1ec2b5f1cfaa64d58e6` | `bfac6b9d057189d9655693248532a673e0d2c4c85721a0214a0f7fc9a668cbee` | 125 |

Diff cấu trúc JSON chỉ thêm `standardizer_mean` và `standardizer_scale` cho `recency_only` và `frequency_only`; bỏ bốn trường này ra thì toàn bộ JSON còn lại bằng nhau. Các giá trị được thêm để ghi rõ phép chuẩn hóa baseline mô tả.
Dấu hệ số không đổi: `True`. Recipe, đặc trưng, ngưỡng, quần thể/outcome, lựa chọn mô hình và các artifact hash còn lại không đổi theo so sánh JSON: `True`. Không dùng nhãn HO2.

Commit `94a1fae` còn sửa các file sau:
- `docs/canonical_numbers.md` — thêm mean/scale vào số chuẩn baseline.
- `docs/gateb_r5_results.md` — bổ sung mean/scale vào mô tả hai baseline.
- `outputs/metrics/gateb_r5_strategy_freeze.json` — ghi bốn trường standardizer nêu trên vào metadata freeze.
- `scripts/freeze_gateb_strategies_dev.py` — serialize mean/scale từ scaler đã fit DEV.

## Ghi chú quyết định

- Lock revision 2 bị supersede bằng SHA-256 `193998064725a5d71b07b49edc5c4fb046e08b5292a86dd4649cf23f47c60880`; lock mới có `revision: 3`.
- Chọn phương án A cho S3, S6 và v3: final-fit từ toàn bộ DEV multi-snapshot theo recipe đã đăng ký; lý do là tạo artifact chấm cố định trước Gate B. Không dùng metric in-sample để đánh giá tổng quát.
- H2 trở lại giả thuyết chính theo quy tắc R2 đã đăng ký; H1/H2 được xử lý bằng Holm hai kiểm định.
- G1 đăng ký dung sai H4 `1e-9`, không đổi ngưỡng hoặc số nhóm tối thiểu; G3 chỉ nêu đề xuất, không đổi tiêu chí.
- Dòng nhật ký không băm chính nó vì tự tham chiếu; SHA-256 byte thực của file sẽ được báo riêng trong báo cáo Gate B.
- Không sửa test lock, config split, Amendment 01–05 hoặc artifact test; không chạy evaluator test cũ.
