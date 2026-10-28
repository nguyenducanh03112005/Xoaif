# Nhật ký thay đổi 06-HO2 Gate B revision 2

Căn cứ so sánh: commit Gate B revision 1 `f67b4b2`. Tất cả sửa đổi đã được thực hiện trước khi mở HO2; không đọc outcome HO2. Hash được tính trực tiếp từ Git blob cũ và byte file hiện hành.

| File | SHA-256 cũ (f67b4b2) | SHA-256 mới | Lý do | Ngày |
|---|---|---|---|---|
| `.gitattributes` | `95565d921701721d188c72f3854355ac62476fc141aac1ac570567784b0f6228` | `1b7a46bb5c6b3769dd02b798dc6a0c211b73d35118fa9d40b04b8b3a096de6b0` | Thành phần hỗ trợ Gate B revision 2; chỉ DEV/code/metadata, không chứa outcome HO2. | 2026-10-28 |
| `.gitignore` | `54526752ffdf20abf6c26fbd28ebd248ecb08182d970fbd3dc04a6b8094a0e81` | `d09f804eae7a8600ee6b8a6b04d70be1f9f1fdabae6f50259d11a88955007e60` | Cho phép đúng aggregate R2/R4/R5 đã review; giữ model/dry-run local ignored. | 2026-10-28 |
| `config/amendment_06_ho2.lock.json` | `a6c751a50625d8d98ffb2a8c10573d61cac9158e21dd3e16493715a3c413e94d` | `193998064725a5d71b07b49edc5c4fb046e08b5292a86dd4649cf23f47c60880` | Đồng bộ số chuẩn và tài liệu Gate B revision 2. | 2026-10-28 |
| `config/amendment_06_ho2.yaml` | `e850af1e85179ebb2c3598fb7f78adb5fd1051e53a80b4473bc0c8300ad97b4c` | `3061105504b3a9b4ec1966a36060418494d2b4d05b7b8b65cdc933e5d6181a9e` | Đồng bộ số chuẩn và tài liệu Gate B revision 2. | 2026-10-28 |
| `docs/amendment_06_gate_b.md` | `d115234b71524bdcaa07f92ae34b12bc24268738016e5904f925a15e6588382c` | `e9fea51ee272d2b422543fe82135532a7a21b421de4c0248f08deb7905e11ff1` | Đồng bộ số chuẩn và tài liệu Gate B revision 2. | 2026-10-28 |
| `docs/amendment_log.md` | `2722c4fd00cd4b31f7b5c4b33b399bd745a0853b90f9529351f914cda6851327` | `db00c98f162fc922ed7fdffd957a45d8f4c07a55114391f274d3ef7b4e3e4ff4` | Thành phần hỗ trợ Gate B revision 2; chỉ DEV/code/metadata, không chứa outcome HO2. | 2026-10-28 |
| `docs/analysis_plan_amendment06_ho2.md` | `cd9197008d6b41f07df51f117886dfd883e7234b514bafefddbd3182b31584a8` | `f1e5d0104390bbdabe7038f03c509e8df4b8831ff337a918ff2e4b10f0a316a6` | Cổng evaluator, helper, khóa revision 2, hash report hoặc kiểm thử bảo vệ. | 2026-10-28 |
| `docs/analysis_plan_gateb_r2.md` | `ABSENT` | `ff8c823e1989e536f75b8ed09a3fc399e3c10af041d678c4672e254ec198be8e` | Đăng ký trước và quyết định H2 bằng công suất/RR DEV theo R2. | 2026-10-28 |
| `docs/analysis_plan_gateb_r4.md` | `ABSENT` | `b6dac1cd2efd64dcd11f92a93d5570a6e7c2330d7d1db0d9f34c0a23c252e85c` | Đăng ký/hiệu chuẩn trước H4–H5 trên DEV; không đọc HO2. | 2026-10-28 |
| `docs/analysis_plan_gateb_r5.md` | `ABSENT` | `e9195f75d76a1326c816b7ebb67e4051771d0b77d9883b42404ced0c3861a6e9` | Chọn/đóng băng tập chiến lược R5 từ DEV; hash artifact, không fit trên HO2. | 2026-10-28 |
| `docs/canonical_numbers.md` | `dc64371456d58696b6d9387621c60ed6af256eb1ff0fe02f2299f65b9b4fb660` | `48a07449e9d5096c905dcb7c1fa2416d35ad728e154641662cee377ab2b1ff83` | Đồng bộ số chuẩn và tài liệu Gate B revision 2. | 2026-10-28 |
| `docs/decisions.md` | `6e0a4638978de37cf0cd0afcca7cc948d897028692d914e920850646d1492886` | `a26ad4da5b0e036fb3773544f56f4d1de484a1b701edecb565f40a38c5f3e3be` | Thành phần hỗ trợ Gate B revision 2; chỉ DEV/code/metadata, không chứa outcome HO2. | 2026-10-28 |
| `docs/gateb_r2_results.md` | `ABSENT` | `f5cc8c5a0dffe52381be7ed9bbfcba75852de9d25ff29e2df49f4b881b4460e2` | Đăng ký trước và quyết định H2 bằng công suất/RR DEV theo R2. | 2026-10-28 |
| `docs/gateb_r4_results.md` | `ABSENT` | `d8ee4e2972a8b54e80099382f8ec72a912bbfa1d91cd647efa4cbcaa5f6831ce` | Đăng ký/hiệu chuẩn trước H4–H5 trên DEV; không đọc HO2. | 2026-10-28 |
| `docs/gateb_r5_results.md` | `ABSENT` | `1f8a4949ef4157cfe6fc518630adfd41bede67fac635cec687f8ed0a00406803` | Chọn/đóng băng tập chiến lược R5 từ DEV; hash artifact, không fit trên HO2. | 2026-10-28 |
| `docs/ho2_access_audit.md` | `ABSENT` | `c97ea3640061fd1c9b551fa6bd5fcc1866e32bb3bead77afe74b444f18624d16` | R6 audit đường nạp và metadata aggregate trước mở. | 2026-10-28 |
| `outputs/metrics/gateb_r2_power.json` | `ABSENT` | `8a8113db17c6bc59b53c806f4790f727905c0d663807059fbab141ba2d54031f` | Đăng ký trước và quyết định H2 bằng công suất/RR DEV theo R2. | 2026-10-28 |
| `outputs/metrics/gateb_r2_rr_dev.json` | `ABSENT` | `ac0572eb47fe43d9768a8ae0b7bd783839d573a852b7f05f3127b82fda474d37` | Đăng ký trước và quyết định H2 bằng công suất/RR DEV theo R2. | 2026-10-28 |
| `outputs/metrics/gateb_r4_dev_calibration.json` | `ABSENT` | `60617a9c181d0cd583687d69f84adeba5203c967095d152308d904cd00f127b5` | Đăng ký/hiệu chuẩn trước H4–H5 trên DEV; không đọc HO2. | 2026-10-28 |
| `outputs/metrics/gateb_r5_strategy_freeze.json` | `ABSENT` | `bfac6b9d057189d9655693248532a673e0d2c4c85721a0214a0f7fc9a668cbee` | Chọn/đóng băng tập chiến lược R5 từ DEV; hash artifact, không fit trên HO2. | 2026-10-28 |
| `outputs/models/gateb_r5/s3_final_dev.joblib` | `ABSENT` | `63e47afbe0a1ef73c01d0be2974c354d753a7299f3d1952146b91bd8b2d1706b` | Chọn/đóng băng tập chiến lược R5 từ DEV; hash artifact, không fit trên HO2. | 2026-10-28 |
| `outputs/models/gateb_r5/s6_final_dev.json` | `ABSENT` | `17af23fa3a84a40c357856271489badd6a1061fd15cac62ace1573627b64d048` | Chọn/đóng băng tập chiến lược R5 từ DEV; hash artifact, không fit trên HO2. | 2026-10-28 |
| `outputs/models/gateb_r5/v3_final_dev.joblib` | `ABSENT` | `fc04ee70693da1a1e16350b99acf80b335705000dac35ba67bde63ef9c5d348b` | Chọn/đóng băng tập chiến lược R5 từ DEV; hash artifact, không fit trên HO2. | 2026-10-28 |
| `scripts/analyze_gateb_r2_dev.py` | `ABSENT` | `a10e17b41abab68209a439d3f0e7a3589c114139563c7244e227234233cede5f` | Đăng ký trước và quyết định H2 bằng công suất/RR DEV theo R2. | 2026-10-28 |
| `scripts/audit_committed_aggregate_dates.py` | `ABSENT` | `3e758ce088e573bc9883fbbd8bf253798636accb97f8973828ef677e69dc82ed` | R6 audit đường nạp và metadata aggregate trước mở. | 2026-10-28 |
| `scripts/build_amendment06_gateb_report.py` | `ABSENT` | `eea162a3515006a31f7af59fc8f897cdc433798b5aeae0251d3a7f482d160355` | Cổng evaluator, helper, khóa revision 2, hash report hoặc kiểm thử bảo vệ. | 2026-10-28 |
| `scripts/build_amendment06_lock.py` | `ABSENT` | `e4c8a47fc0bea4a1b768615928346309e30b0341e849b735c8f28b380e7056cd` | Cổng evaluator, helper, khóa revision 2, hash report hoặc kiểm thử bảo vệ. | 2026-10-28 |
| `scripts/build_amendment06_revision_log.py` | `ABSENT` | `332c558b751590fcbc39e6828fc1f19febd067bd6a6613a420c7eeabf4c1dab3` | Cổng evaluator, helper, khóa revision 2, hash report hoặc kiểm thử bảo vệ. | 2026-10-28 |
| `scripts/calibrate_gateb_r4_dev.py` | `ABSENT` | `9c65803bce23c294b689110b96e5fa6051aff1dd13a44dad98deb76073a01282` | Đăng ký/hiệu chuẩn trước H4–H5 trên DEV; không đọc HO2. | 2026-10-28 |
| `scripts/evaluate_holdout2_once.py` | `ABSENT` | `35cdf0c9b97d7b44829817e357129cfc9cae6666829be1b2f76ce81ba3ba2d5d` | Cổng evaluator, helper, khóa revision 2, hash report hoặc kiểm thử bảo vệ. | 2026-10-28 |
| `scripts/fix_sealed_eol.py` | `8fe7f0b7e4b79987456ef5b8765443ab942d16823015a917e01ed00bdf20e920` | `8c9ae853370e33f0d089843e6799a24b861db7665805f5214d5d063815c65e06` | Thành phần hỗ trợ Gate B revision 2; chỉ DEV/code/metadata, không chứa outcome HO2. | 2026-10-28 |
| `scripts/freeze_gateb_strategies_dev.py` | `ABSENT` | `984740129ebc9abe5ad7ba727f40950d5413fd3658823caa94f66b118ee6719d` | Chọn/đóng băng tập chiến lược R5 từ DEV; hash artifact, không fit trên HO2. | 2026-10-28 |
| `scripts/run_all.py` | `ea908800c999a84aa8c9bc0467d84a26c386a7019026fa774b8463c94e82c852` | `10dfed97a84038a81ee616cb3262643ecc7feb96e5fb9373c96be5256ce1f192` | Thành phần hỗ trợ Gate B revision 2; chỉ DEV/code/metadata, không chứa outcome HO2. | 2026-10-28 |
| `scripts/summarize_gateb_r2_power.py` | `ABSENT` | `15913f5a2b67a8d8bb61be405f9207a470905ca741c2f597356f6475299a64c0` | Đăng ký trước và quyết định H2 bằng công suất/RR DEV theo R2. | 2026-10-28 |
| `scripts/verify_gateb_lock.py` | `ABSENT` | `90180f86d41d0656b83877fe1538b4b7cfc74fadc23bf36a89fef831539b2fe7` | Cổng evaluator, helper, khóa revision 2, hash report hoặc kiểm thử bảo vệ. | 2026-10-28 |
| `src/features/holdout2_access.py` | `ABSENT` | `de3c75d875823c3c6027fba82896b61bb360027f1ad6e646239c6158288938ea` | Cổng evaluator, helper, khóa revision 2, hash report hoặc kiểm thử bảo vệ. | 2026-10-28 |
| `src/features/holdout2_features.py` | `ABSENT` | `826c5085a2b3fe0315a4f8501b13155e5f6b4ed6eb6db3e07f5639f1a72f8eac` | Cổng evaluator, helper, khóa revision 2, hash report hoặc kiểm thử bảo vệ. | 2026-10-28 |
| `src/features/holdout2_metrics.py` | `ABSENT` | `9920eebfa62075ecaccfa3713d54a3ac11fe3c7e4abf249b308ae350be276a8e` | Cổng evaluator, helper, khóa revision 2, hash report hoặc kiểm thử bảo vệ. | 2026-10-28 |
| `tests/test_gateb_aggregate_date_audit.py` | `ABSENT` | `f751fe5090024620e4db41e059fa66a5b3303939a34e6e56d6f40fc5982c8041` | R6 audit đường nạp và metadata aggregate trước mở. | 2026-10-28 |
| `tests/test_gateb_lock_verification.py` | `ABSENT` | `6a1941b4b06c26594549249ccdfbb95be2415c051da93d064cac46c06fc5d3ee` | Cổng evaluator, helper, khóa revision 2, hash report hoặc kiểm thử bảo vệ. | 2026-10-28 |
| `tests/test_gateb_r4_calibration.py` | `ABSENT` | `dec6c98324f26920588db30aeedc158ab7b182349446892ebf665165a5e754c4` | Đăng ký/hiệu chuẩn trước H4–H5 trên DEV; không đọc HO2. | 2026-10-28 |
| `tests/test_gateb_r5_freeze.py` | `ABSENT` | `79843a63f32bdc279d059effd4da9890bf71f2fbdefd26eda76f0a13de9d76e0` | Chọn/đóng băng tập chiến lược R5 từ DEV; hash artifact, không fit trên HO2. | 2026-10-28 |
| `tests/test_gateb_report_hashes.py` | `ABSENT` | `edfacfd5211afbdc5e9107add47309b8e31749e3ab94140745e1b645c63773ef` | Đồng bộ số chuẩn và tài liệu Gate B revision 2. | 2026-10-28 |
| `tests/test_ho2_eligibility_gate.py` | `48acab60c8bb5ccae40ca5aee1b65c24fbdacab97ea37b5dced2c3751b0aa8b9` | `c7d380abbf58a389414074503aa33e0dfd0491c621a1a202ee8dc9aec40d1633` | Kiểm tra hồi quy cho quy tắc đã đăng ký và ranh giới không mở HO2. | 2026-10-28 |
| `tests/test_holdout2_feature_boundary.py` | `ABSENT` | `657c085056eead45aa427fd55fcb93f73ceb277c9c9a8933f3512a4a93d136bd` | Cổng evaluator, helper, khóa revision 2, hash report hoặc kiểm thử bảo vệ. | 2026-10-28 |
| `tests/test_holdout2_metrics.py` | `ABSENT` | `ecf9c4c9492e7a5534c65a019924de537ac419fd43a3976d4ca153af737bac7b` | Cổng evaluator, helper, khóa revision 2, hash report hoặc kiểm thử bảo vệ. | 2026-10-28 |

## Ghi chú quyết định

- Lock revision 1 bị supersede bởi SHA-256 `a6c751a50625d8d98ffb2a8c10573d61cac9158e21dd3e16493715a3c413e94d`; lock mới có `revision: 2`.
- Chọn phương án A cho S3, S6 và v3: final-fit từ toàn bộ DEV multi-snapshot theo recipe đã đăng ký; lý do là tạo artifact chấm cố định trước Gate B. Không dùng metric in-sample để đánh giá tổng quát.
- H2 trở lại giả thuyết chính theo quy tắc R2 đã đăng ký; H1/H2 được xử lý bằng Holm hai kiểm định.
- Không sửa test lock, config split, Amendment 01–05 hoặc artifact test; không chạy evaluator test cũ.
