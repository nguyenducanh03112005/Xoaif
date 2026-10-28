"""Generate the Gate B revision-3 file/hash log and R5 JSON audit from Git and file bytes."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "f67b4b2"
OUTPUT = ROOT / "docs/amendment_06_revision_log.md"


REASONS = {
    ".gitattributes": "Thêm quy tắc giữ nguyên byte cho lock 06; tác động cách Git lưu EOL, không đổi nội dung phân tích.",
    ".gitignore": "Cho phép commit aggregate Gate B đã rà soát và tiếp tục loại model/dry-run local; tác động phạm vi file được track.",
    "config/amendment_06_ho2.yaml": "Cập nhật từ rev2 lên rev3: đặt supersedes, dung sai H4 1e-9, giữ ngưỡng/số nhóm và trạng thái đóng; ảnh hưởng cấu hình giao thức.",
    "config/amendment_06_ho2.lock.json": "Thay lock rev2 bằng rev3, băm 85 nguồn và giữ test_opened=false; không mở HO2.",
    "docs/analysis_plan_amendment06_ho2.md": "Giữ protocol rev2 và bổ sung quy tắc dung sai H4 rev3; ngưỡng/nhóm và các giả thuyết không đổi.",
    "docs/analysis_plan_gateb_r2.md": "Đăng ký quy tắc RR/power trước kết quả DEV; ảnh hưởng quyết định phân loại H2.",
    "docs/gateb_r2_results.md": "Báo cáo RR snapshot và đầy đủ bảng power H1/H2 sau đăng ký; chỉ DEV/aggregate tham chiếu, không có HO2 outcome.",
    "outputs/metrics/gateb_r2_rr_dev.json": "Lưu RR và bootstrap CI theo khách từ snapshot DEV; đầu ra aggregate phục vụ quyết định H2.",
    "outputs/metrics/gateb_r2_power.json": "Lưu power grid đã đăng ký cho hai mức prevalence và các effect size; thiết kế, không phải kết quả HO2.",
    "scripts/analyze_gateb_r2_dev.py": "Tính RR DEV theo snapshot và bootstrap cụm khách; đường phân tích DEV-only.",
    "scripts/summarize_gateb_r2_power.py": "Tính power grid R2 theo n tiền T2 và prevalence tham chiếu; không nạp outcome.",
    "docs/analysis_plan_gateb_r4.md": "Đăng ký nhóm/metric và tiêu chí H4/H5 trước hiệu chuẩn DEV; không dùng HO2.",
    "docs/gateb_r4_results.md": "Ghi ngưỡng ổn định nhóm DEV và k_DEV; đầu ra hiệu chuẩn, không chọn nhóm bằng outcome HO2.",
    "outputs/metrics/gateb_r4_dev_calibration.json": "Lưu thống kê tham chiếu S6/RFM và k_DEV từ DEV; aggregate dùng đóng băng tiêu chí.",
    "scripts/calibrate_gateb_r4_dev.py": "Tạo tham chiếu H4/H5 trên các nửa DEV đã đăng ký; không đọc HO2.",
    "docs/analysis_plan_gateb_r5.md": "Đăng ký quần thể fit/định nghĩa chiến lược trước khi tạo artifact R5.",
    "docs/gateb_r5_results.md": "Báo cáo quần thể fit và hash chiến lược; không trình bày metric in-sample như xác nhận.",
    "outputs/metrics/gateb_r5_strategy_freeze.json": "Ghi metadata, quần thể fit và hash artifact DEV; bản sau 94a1fae thêm mean/scale cho hai baseline mô tả.",
    "scripts/freeze_gateb_strategies_dev.py": "Fit/chốt S3/S6/v3 trên DEV và ghi metadata; ở 94a1fae bổ sung scaler mean/scale để dựng score baseline.",
    "outputs/models/gateb_r5/s3_final_dev.joblib": "Artifact cây final-fit DEV được hash để chấm cố định; không fit trên HO2.",
    "outputs/models/gateb_r5/s6_final_dev.json": "Map nhóm-rate final DEV được hash để chấm cố định; không fit trên HO2.",
    "outputs/models/gateb_r5/v3_final_dev.joblib": "Artifact Logistic Regression final-fit DEV được hash; không chọn trên HO2.",
    "scripts/evaluate_holdout2_once.py": "Chuyển validator/open-lock sang rev3 và dùng helper H4 dung sai; không gọi evaluator hoặc mở HO2 trong lượt này.",
    "src/features/holdout2_access.py": "Yêu cầu lock mở revision 3 khớp hash config/protocol/evaluator; tiếp tục chặn mọi nạp trước lock.",
    "src/features/holdout2_features.py": "Tách feature trước T2 và outcome sau T2 theo ngày địa phương; ranh giới thời gian cho evaluator.",
    "src/features/holdout2_metrics.py": "Thêm helper H4 dùng dung sai 1e-9 và ngưỡng tối thiểu 4 nhóm; giữ metric/bootstrap/Holm còn lại.",
    "scripts/verify_gateb_lock.py": "Kiểm tra hash, EOL, giả thuyết và trạng thái khóa; được run_all gọi trước test suite.",
    "scripts/build_amendment06_lock.py": "Sinh lock trực tiếp từ byte file/config/aggregate DEV; không chép hash tay.",
    "scripts/build_amendment06_gateb_report.py": "Sinh báo cáo và bảng hash từ lock/file thật; thay thế hash báo cáo chép tay.",
    "scripts/build_amendment06_revision_log.py": "Sinh nhật ký từ Git blob và byte hiện hành; đồng thời kiểm toán khác biệt JSON R5.",
    "scripts/audit_committed_aggregate_dates.py": "Đọc riêng trường thời gian của aggregate đã commit để kiểm tra phạm vi ngày; không đọc raw.",
    "scripts/run_all.py": "Đổi bước verify lock từ revision 2 sang revision 3 trước test/PII/dashboard smoke; vẫn không gọi evaluator HO2.",
    "scripts/fix_sealed_eol.py": "Tạo quy tắc -text và giữ byte của file hash-sealed; không đổi nội dung số liệu.",
    "tests/test_holdout2_feature_boundary.py": "Kiểm tra feature <T2, outcome boundary và loader gating bằng dữ liệu tổng hợp.",
    "tests/test_holdout2_metrics.py": "Thêm ca rho tổng hợp: 1/2 swap n=8, identity/near-1 và swap n=6, dưới 4 nhóm.",
    "tests/test_gateb_lock_verification.py": "Đổi fixture/expectation sang lock rev3; kiểm tra hash sai và output HO2 tồn tại bị từ chối.",
    "tests/test_gateb_report_hashes.py": "Đối chiếu hash/report hypothesis và có mặt bảng G1, ghi chú prevalence G2, đề xuất G3.",
    "tests/test_gateb_r4_calibration.py": "Khóa số nhóm/điều kiện H4/H5 từ hiệu chuẩn DEV.",
    "tests/test_gateb_r5_freeze.py": "Khóa dấu/chiều baseline và metadata final-fit từ DEV.",
    "tests/test_gateb_aggregate_date_audit.py": "Kiểm tra parser và date-only scan của aggregate; không đọc nội dung ngoài cột ngày.",
    "docs/ho2_access_audit.md": "Liệt kê đường nạp, metadata ngày và giới hạn pháp y trước Gate B.",
    "docs/decisions.md": "Ghi quyết định/phạm vi Gate B và các lần sửa đã duyệt; không thay split/test lock.",
    "docs/amendment_log.md": "Ghi lịch sử amendment và ranh giới chưa mở HO2.",
    "docs/canonical_numbers.md": "Đồng bộ số nguồn R2/R4/R5 và provenance; không thêm outcome HO2.",
    "docs/cohort_definitions.md": "Làm rõ cohort/anchor và định nghĩa dùng trong R2/R5.",
    "docs/test_provenance_note.md": "Ghi nguồn, mở test cũ và phạm vi kết quả đã có; không nạp lại test.",
    "docs/analysis_plan_wp5.md": "Ghi recipe DEV đa mốc được dùng để đóng băng ứng viên R5.",
    "docs/analysis_plan_wp5b.md": "Ghi recipe WP5b/outer folds liên quan lựa chọn chiến lược DEV.",
    "docs/analysis_plan_wp5c.md": "Ghi recipe S6/fold để phân biệt mapping theo fold và final-fit.",
    "outputs/metrics/repurchase_v3_dev.json": "Aggregate metric DEV-only của v3; không dùng kết quả HO2.",
    "outputs/metrics/repurchase_wp5b_dev.json": "Aggregate so sánh chiến lược WP5b trên temporal validation DEV.",
    "outputs/metrics/repurchase_wp5c_dev.json": "Aggregate DEV cho S6/WP5c; mapping fold tách khỏi final-fit.",
    "outputs/metrics/dev_final_model.json": "Metadata/metric DEV của mô hình chính; không thay artifact test.",
    "outputs/metrics/dev_final_models_v2.json": "Metadata/metric DEV cho biến thể v2; giữ ngoài đánh giá HO2.",
    "outputs/metrics/frozen_segmenters_dev.json": "Metadata phân khúc đóng băng trên DEV, không fit bằng HO2.",
    "outputs/tables/repurchase_wp5c_train_rates.csv": "Bảng aggregate rate theo fold-train WP5c; không dùng nhầm làm map final-fit.",
    "outputs/tables/combos_v2.csv": "Aggregate combo đã đóng băng, nguồn mô tả H5.",
    "outputs/tables/combo_recommendation_screen_f3.csv": "Aggregate sàng lọc combo DEV đã commit; không thêm discovery từ HO2.",
    "docs/amendment_06_revision_log.md": "Tạo bảng hash revision từ Git và file hiện hành; bản thân log không liệt kê hash tự quy chiếu.",
    "docs/amendment_06_gate_b.md": "Sinh báo cáo Gate B từ lock/hash; tài liệu tổng hợp, không có outcome HO2.",
    "docs/analysis_plan_gateb_r6_fix.md": "Đăng ký dung sai H4 trước commit mã; giữ nguyên ngưỡng và tối thiểu 4 nhóm.",
}


def _reason(path: str) -> str:
    if path in REASONS:
        return REASONS[path]
    if path.startswith("outputs/models/"):
        return "Artifact model DEV local được hash để nhận dạng file chấm đã đóng băng; không commit binary và không refit bằng HO2."
    if path.startswith("tests/"):
        return f"Thêm/sửa kiểm thử `{Path(path).name}` để khóa hành vi tương ứng; chỉ fixture tổng hợp, không đọc HO2."
    if path.startswith("outputs/metrics/"):
        return f"Aggregate `{Path(path).name}` ghi số DEV/metadata đã đăng ký; không chứa outcome HO2 mới."
    raise KeyError(f"Add a path-specific reason before generating the revision log: {path}")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _r5_json_audit() -> list[str]:
    rel = "outputs/metrics/gateb_r5_strategy_freeze.json"
    old = subprocess.check_output(["git", "show", f"a052bae:{rel}"], cwd=ROOT)
    current = (ROOT / rel).read_bytes()
    old_json, current_json = json.loads(old), json.loads(current)
    differences = []
    for strategy in sorted(current_json["strategy_population_and_fit"]):
        before = old_json["strategy_population_and_fit"][strategy]
        after = current_json["strategy_population_and_fit"][strategy]
        for field in sorted(set(before) | set(after)):
            if before.get(field) != after.get(field):
                differences.append((strategy, field, before.get(field), after.get(field)))
    allowed = {("recency_only", "standardizer_mean"), ("recency_only", "standardizer_scale"),
               ("frequency_only", "standardizer_mean"), ("frequency_only", "standardizer_scale")}
    if {(strategy, field) for strategy, field, _, _ in differences} != allowed:
        raise ValueError(f"Unexpected R5 JSON field changes between a052bae and current: {differences}")
    before_stripped = json.loads(json.dumps(old_json))
    after_stripped = json.loads(json.dumps(current_json))
    for obj in (before_stripped, after_stripped):
        for strategy in ("recency_only", "frequency_only"):
            obj["strategy_population_and_fit"][strategy].pop("standardizer_mean", None)
            obj["strategy_population_and_fit"][strategy].pop("standardizer_scale", None)
    if before_stripped != after_stripped:
        raise ValueError("R5 JSON fields other than the four registered scaler fields changed")
    def hashes(data: bytes) -> tuple[str, str, str, int]:
        lf = data.replace(b"\r\n", b"\n")
        crlf = lf.replace(b"\n", b"\r\n")
        return _sha(data), _sha(lf), _sha(crlf), data.count(b"\r\n")
    old_hashes, new_hashes = hashes(old), hashes(current)
    other_files = subprocess.check_output(
        ["git", "show", "--format=", "--name-only", "94a1fae"], cwd=ROOT
    ).decode().splitlines()
    coefficient_signs_unchanged = all(
        old_json["strategy_population_and_fit"][name]["direction"]
        == current_json["strategy_population_and_fit"][name]["direction"]
        for name in ("recency_only", "frequency_only")
    )
    return [
        "## Kiểm toán `gateb_r5_strategy_freeze.json` — a052bae so với hiện tại",
        "",
        "| Phiên bản | SHA-256 byte gốc | SHA-256 chuẩn LF | SHA-256 chuẩn CRLF | CRLF trong byte gốc |",
        "|---|---|---|---|---:|",
        f"| a052bae | `{old_hashes[0]}` | `{old_hashes[1]}` | `{old_hashes[2]}` | {old_hashes[3]} |",
        f"| hiện tại | `{new_hashes[0]}` | `{new_hashes[1]}` | `{new_hashes[2]}` | {new_hashes[3]} |",
        "",
        "Diff cấu trúc JSON chỉ thêm `standardizer_mean` và `standardizer_scale` cho `recency_only` và `frequency_only`; bỏ bốn trường này ra thì toàn bộ JSON còn lại bằng nhau. Các giá trị được thêm để ghi rõ phép chuẩn hóa baseline mô tả.",
        f"Dấu hệ số không đổi: `{coefficient_signs_unchanged}`. Recipe, đặc trưng, ngưỡng, quần thể/outcome, lựa chọn mô hình và các artifact hash còn lại không đổi theo so sánh JSON: `True`. Không dùng nhãn HO2.",
        "",
        "Commit `94a1fae` còn sửa các file sau:",
        *[f"- `{path}` — " + {
            "docs/canonical_numbers.md": "thêm mean/scale vào số chuẩn baseline.",
            "docs/gateb_r5_results.md": "bổ sung mean/scale vào mô tả hai baseline.",
            "scripts/freeze_gateb_strategies_dev.py": "serialize mean/scale từ scaler đã fit DEV.",
            rel: "ghi bốn trường standardizer nêu trên vào metadata freeze.",
        }[path] for path in other_files],
        "",
    ]


def _changed_paths() -> list[str]:
    committed = subprocess.check_output(["git", "diff", "--name-only", f"{BASE}..HEAD"], cwd=ROOT).decode().splitlines()
    freeze_path = ROOT / "outputs/metrics/gateb_r5_strategy_freeze.json"
    local_artifacts = []
    if freeze_path.is_file():
        freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
        for item in freeze["strategy_population_and_fit"].values():
            rel = item.get("artifact", item.get("path", ""))
            if rel.startswith("outputs/models/gateb_r5/") and (ROOT / rel).is_file():
                local_artifacts.append(rel)
    status = subprocess.check_output(["git", "status", "--porcelain=v1", "-z"], cwd=ROOT)
    extra = []
    chunks = status.split(b"\0")
    for item in chunks:
        if not item:
            continue
        path = item[3:].decode("utf-8", errors="replace")
        if path and path != OUTPUT.relative_to(ROOT).as_posix() and not path.startswith(".tmp_test/"):
            extra.append(path.replace("\\", "/"))
    paths = (set(committed) | set(extra) | set(local_artifacts)) - {OUTPUT.relative_to(ROOT).as_posix()}
    return sorted(paths)


def _old_hash(rel: str) -> str:
    probe = subprocess.run(["git", "cat-file", "-e", f"{BASE}:{rel}"], cwd=ROOT,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if probe.returncode:
        return "ABSENT"
    data = subprocess.check_output(["git", "show", f"{BASE}:{rel}"], cwd=ROOT)
    return hashlib.sha256(data).hexdigest()


def build_text() -> str:
    rows = []
    today = str(date.today())
    for rel in _changed_paths():
        path = ROOT / rel
        new = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "DELETED"
        rows.append(f"| `{rel}` | `{_old_hash(rel)}` | `{new}` | {_reason(rel)} | {today} |")
    return "\n".join([
        "# Nhật ký thay đổi 06-HO2 Gate B revision 3",
        "",
        "Căn cứ so sánh file: commit Gate B revision 1 `f67b4b2`; ghi nhận thêm các sửa đổi sau Gate B rev2 `19293fa`. Tất cả thay đổi đều trước khi mở HO2; không đọc outcome HO2. Hash cũ lấy từ Git blob, hash mới lấy trực tiếp từ byte file hiện hành. Lý do từng hàng được ánh xạ cụ thể trong script sinh log.",
        "",
        "| File | SHA-256 cũ (f67b4b2) | SHA-256 mới | Lý do | Ngày |",
        "|---|---|---|---|---|",
        *rows,
        "",
        *_r5_json_audit(),
        "## Ghi chú quyết định",
        "",
        "- Lock revision 2 bị supersede bằng SHA-256 `193998064725a5d71b07b49edc5c4fb046e08b5292a86dd4649cf23f47c60880`; lock mới có `revision: 3`.",
        "- Chọn phương án A cho S3, S6 và v3: final-fit từ toàn bộ DEV multi-snapshot theo recipe đã đăng ký; lý do là tạo artifact chấm cố định trước Gate B. Không dùng metric in-sample để đánh giá tổng quát.",
        "- H2 trở lại giả thuyết chính theo quy tắc R2 đã đăng ký; H1/H2 được xử lý bằng Holm hai kiểm định.",
        "- G1 đăng ký dung sai H4 `1e-9`, không đổi ngưỡng hoặc số nhóm tối thiểu; G3 chỉ nêu đề xuất, không đổi tiêu chí.",
        "- Dòng nhật ký không băm chính nó vì tự tham chiếu; SHA-256 byte thực của file sẽ được báo riêng trong báo cáo Gate B.",
        "- Không sửa test lock, config split, Amendment 01–05 hoặc artifact test; không chạy evaluator test cũ.",
        "",
    ])


def main() -> int:
    OUTPUT.write_text(build_text(), encoding="utf-8", newline="\n")
    print(f"Wrote revision log with {len(_changed_paths())} paths.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
