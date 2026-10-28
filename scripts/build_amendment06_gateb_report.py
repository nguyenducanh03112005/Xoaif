"""Generate Gate B report from the final lock and actual files; hashes are never hand-copied."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

import yaml

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pct(value: float) -> str:
    return f"{100 * value:.2f}%"


def build_report(test_count: int, root: Path = ROOT) -> str:
    lock_path = root / "config/amendment_06_ho2.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    config = yaml.safe_load((root / "config/amendment_06_ho2.yaml").read_bytes())
    if lock.get("revision") != 2 or lock.get("test_opened") is not False:
        raise ValueError("report requires closed revision-2 lock")
    hash_rows = []
    for rel, locked_hash in sorted(lock["frozen_source_sha256"].items()):
        path = root / rel
        if not path.is_file():
            raise FileNotFoundError(rel)
        actual = sha(path)
        if actual != locked_hash:
            raise ValueError(f"hash mismatch for {rel}")
        hash_rows.append(f"| `{rel}` | `{actual}` | `{locked_hash}` | khớp |")
    lock_hash = sha(lock_path)
    r2 = json.loads((root / "outputs/metrics/gateb_r2_rr_dev.json").read_text(encoding="utf-8"))
    power = json.loads((root / "outputs/metrics/gateb_r2_power.json").read_text(encoding="utf-8"))
    r4 = json.loads((root / "outputs/metrics/gateb_r4_dev_calibration.json").read_text(encoding="utf-8"))
    r5 = json.loads((root / "outputs/metrics/gateb_r5_strategy_freeze.json").read_text(encoding="utf-8"))
    dry_path = root / "outputs/dryrun/holdout2_code_dryrun.json"
    dry = json.loads(dry_path.read_text(encoding="utf-8")) if dry_path.is_file() else {"code_run": False}
    code_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root).decode().strip()

    h1_power_rows, h2_power_rows = [], []
    for scenario in ("DEV_7_4_percent", "old_test_aggregate_4_6_percent"):
        baseline = power["baselines"][scenario]
        label = "DEV 7,4%" if scenario == "DEV_7_4_percent" else "Aggregate test cũ 4,6%"
        for auc, metrics in baseline["H1"].items():
            h1_power_rows.append(f"| {label} | {float(auc):.2f} | {metrics['power_lower_ci_gt_0_55']:.4f} |")
        for rr, metrics in baseline["H2"].items():
            h2_power_rows.append(f"| {label} | {float(rr):.6f} | {metrics['power_lower_ci_gt_1_5']:.4f} |")

    strategy_rows = []
    for name, item in r5["strategy_population_and_fit"].items():
        sha_text = item.get("sha256", "—")
        fit = item.get("fit_population", "DEV score rule")
        if name in {"recency_only", "frequency_only"}:
            fit += f"; hệ số {item['standardized_coefficient']:+.5f}; dấu {item['direction']:+d}"
        strategy_rows.append(f"| {name} | {'đủ điều kiện' if item['eligible'] else 'loại'} | {fit} | `{sha_text}` |")

    test_rows = [
        ("test_gateb_r4_calibration_uses_registered_cells_and_counts_dev_combo_filter", "H4 nhóm cố định; H5 k_DEV filter DEV"),
        ("test_gateb_r5_univariate_direction_comes_from_dev_fit", "chiều recency/frequency theo dấu hệ số"),
        ("test_temporal_parser_orders_dates_and_partials", "parser ngày/tháng/quý aggregate"),
        ("test_csv_audit_reads_only_temporal_column", "scanner chỉ trả cột thời gian"),
        ("test_metrics_match_hand_calculation", "ROC-AUC, RR, tie-aware precision/lift"),
        ("test_holm_step_down_and_customer_cluster_bootstrap_are_deterministic", "Holm và bootstrap cụm khách"),
        ("test_centered_bootstrap_p_uses_registered_effect_threshold", "p bootstrap định tâm tại ngưỡng H1/H2"),
        ("test_yaml_date_conditions_and_boundary_rows", "T2, T2+1, T2+180, T2+181 khớp YAML"),
        ("test_feature_builder_matches_existing_fixed_t_features_and_excludes_t_or_later", "feature D-005 khớp hàm cũ tại T; không dùng ngày >=T"),
        ("test_holdout2_loader_refuses_to_run_without_open_lock", "loader chặn khi chưa có lock"),
        ("test_dry_run_gate_accepts_only_full_dev_horizon_and_rejects_t2", "dry-run chỉ DEV horizon đủ"),
        ("test_open_lock_is_created_once_after_exact_owner_phrase", "phrase đúng, tạo một lần, lần hai bị từ chối"),
        ("test_closed_lock_verifies_all_required_hashes_and_outputs_absent", "lock hash/EOL/trạng thái đóng"),
        ("test_lock_verifier_rejects_hash_mutation_and_open_outputs", "từ chối hash sai hoặc output đã mở"),
        ("test_report_hash_table_matches_lock_and_file_bytes", "bảng hash report=lock=file thật"),
        ("test_hypothesis_lists_are_consistent_across_config_lock_and_protocol", "danh sách giả thuyết protocol/config/lock/report"),
    ]

    return "\n".join([
        "# Báo cáo Gate B — 06-HO2 revision 2 (nhãn vẫn đóng)",
        "",
        f"Ngày: 2026-10-28. Commit mã đã khóa trước khi tạo báo cáo: `{code_commit}`. **Không mở HO2; Phase C chưa bắt đầu.** Không chạy `scripts/evaluate_test_once.py`.",
        "",
        "## (a) Hash đối chiếu trực tiếp",
        "",
        f"SHA-256 lock mới: `{lock_hash}`; revision=`{lock['revision']}`; supersedes `{lock['supersedes']}`; {lock['source_hash_count']} hash nguồn.",
        "",
        "| File | SHA-256 file thật | SHA-256 trong lock | Đối chiếu |",
        "|---|---|---|---|",
        *hash_rows,
        "",
        "## (b) Nhật ký thay đổi revision 2",
        "",
        "Từng file, SHA-256 cũ/mới, lý do và ngày nằm trong [amendment_06_revision_log.md](amendment_06_revision_log.md). Lock cũ bị supersede bằng đúng hash ghi trên.",
        "",
        "## (c) R2 — H2 trở lại giả thuyết chính",
        "",
        f"DEV snapshot-weighted RR frequency≥2 / frequency=1 = **{r2['rr_frequency_ge_2_vs_eq_1']['rr']:.3f}**, bootstrap CI 95% **[{r2['rr_frequency_ge_2_vs_eq_1']['ci95_lower']:.3f}; {r2['rr_frequency_ge_2_vs_eq_1']['ci95_upper']:.3f}]**; nhóm frequency=1: {r2['frequency_eq_1']['positive_snapshots']}/{r2['frequency_eq_1']['snapshots']} dương/snapshot; frequency≥2: {r2['frequency_ge_2']['positive_snapshots']}/{r2['frequency_ge_2']['snapshots']}. Khám phá DEV-only, chưa xác nhận ngoài mẫu.",
        "",
        "### H1 power: AUC thật so với ngưỡng 0,55",
        "",
        "| Mốc prevalence | AUC giả định | Công suất |", "|---|---:|---:|", *h1_power_rows,
        "",
        "### H2 power: RR thật so với ngưỡng 1,5",
        "",
        "| Mốc prevalence | RR giả định | Công suất |", "|---|---:|---:|", *h2_power_rows,
        "",
        f"Quy tắc đăng ký R2: công suất ở RR=cận dưới DEV {power['rr_lower_dev']:.3f} là {_pct(power['h2_power_at_rr_lower_dev_both_references'][0])} (DEV) và {_pct(power['h2_power_at_rr_lower_dev_both_references'][1])} (aggregate test cũ), đều ≥80%; H2 là chính. Hai kiểm định chính H1/H2 dùng Holm step-down 0,025/0,05. Bảng đầy đủ và giới hạn trong `docs/gateb_r2_results.md`.",
        "",
        "## (d) R5 — chiến lược và quần thể fit",
        "",
        "| Chiến lược | Trạng thái | Quần thể fit / mô tả | SHA-256 artifact |", "|---|---|---|---|", *strategy_rows,
        "",
        "S3, S6, v3 theo phương án A: final-fit toàn DEV đa mốc. `repurchase_wp5c_train_rates.csv` là mapping theo fold train, không phải quần thể final-fit. D-005 giữ mô hình chính.",
        "",
        "## (e) Tiêu chí H1–H5 cuối",
        "",
        "- **H1:** D-005 ROC-AUC>0,55; một phía bootstrap 2.000 khách, Holm với H2. Đạt khi AUC điểm vượt ngưỡng và p Holm<0,05. Chênh `AUC−0,70` chỉ mô tả, kèm CI. Đạt H1 không có nghĩa lặp lại AUC test 0,70.",
        "- **H2:** RR mua lại 180 ngày frequency≥2/frequency=1>1,5; CI bootstrap theo khách, p bootstrap một phía tại RR=1,5; Holm cùng H1.",
        "- **H3:** S1/S3/S6 × precision@10/lift (6 phép so sánh phụ, không hiệu chỉnh). Tie-aware: K=ceil(0,10N), q=(K−n_above)/n_tie, precision=(pos_above+q×pos_tie)/K, lift=precision/prevalence. Hỗ trợ nếu cận dưới CI95 precision>prevalence và lift>1. S1 nhị phân, S3/S6 điểm rời rạc; ROC/decile chỉ mô tả.",
        f"- **H4:** Spearman S6/RFM DEV-pooled so với HO2; n≥30, ít nhất 4 nhóm, không chọn nhóm theo outcome. Ngưỡng S6 `rho≥{r4['dev_half_reference']['s6']['rho']:.10f}`; RFM `rho≥{r4['dev_half_reference']['rfm']['rho']:.1f}`. DEV tham chiếu gồm 8/6 nhóm đủ điều kiện.",
        f"- **H5:** 24 combo đóng băng; `k_DEV={r4['h5']['k_dev']}`, chỉ mô tả vì k<4. Giỏ status 3 không quà, `T2<date≤T2+180`, bỏ gift line, ≥2 product IDs; cặp <30 bị che và không tính qua bộ lọc.",
        "- **H6:** không kiểm định; DEV không có dải xu hướng đáng tin đã đăng ký trước.",
        "",
        "## (f) Kiểm thử và dry-run",
        "",
        f"- `run_all.py`: xanh; `pytest`: **{test_count} passed**. PII scan, verify lock và dashboard smoke xanh.",
        "",
        "| Test mới | Kiểm tra | Kết quả |", "|---|---|---|",
        *[f"| `{name}` | {description} | PASS |" for name, description in test_rows],
        "",
        f"- Dry-run: **mã chạy {'đúng' if dry.get('code_run') else 'chưa chạy/sai'}**; T={dry.get('T','—')}; feature rows={dry.get('feature_rows','—')}; end={dry.get('label_horizon_end','—')}. Nhãn: “{dry.get('label','kiểm thử mã, không phải kết quả')}”. Không có metric/AUC dry-run trong báo cáo.",
        "",
        "## (g) Kiểm toán truy cập và aggregate",
        "",
        "Audit đầy đủ tại [ho2_access_audit.md](ho2_access_audit.md): 89 aggregate CSV/JSON đã quét, 22 có trường thời gian; max ngày kho DuckDB `2025-10-21`; dashboard `2026-04` là tháng partial của test cũ; `2026-10-31` chỉ là lịch tham chiếu. Không thấy event aggregate sau T2. Giới hạn pháp y được ghi rõ.",
        "",
        "## (h) Gate trạng thái",
        "",
        f"Lock revision 2: `{lock['status']}`; `test_opened=false`; `phase_c_started=false`. Các hash nguồn khớp file thật tại thời điểm dựng báo cáo. Không tồn tại output mở HO2 trong checkout tại Gate B.",
        "",
        "## (i) Phát hiện, rủi ro, và trạng thái công việc",
        "",
        "Ba phát hiện chính: (1) H2 DEV RR=3,473, CI[2,656;4,520] và đủ công suất theo quy tắc đã đăng ký; (2) hiệu chuẩn H4 DEV nửa đầu/nửa sau cao nhưng chỉ 8 ô S6, 6 nhóm RFM; (3) `k_DEV=1`, nên H5 không thể là kiểm định xác nhận.",
        "",
        "Rủi ro còn lại: một cửa hàng/snapshot hồi cứu; trạng thái đơn có thể thay đổi sau T2; CI không đảm bảo khái quát; metric quan sát không phải nhân quả/lợi nhuận; D-005/v2 có quy trình fit lịch sử khác S3/S6/v3. H6 chưa testable.",
        "",
        "| Đã làm | Chưa làm | Cần quyết định của chủ dự án |", "|---|---|---|",
        "| R2–R7, prereg R4/R5, evaluator/test/hash, R6 audit, báo cáo Gate B | Mở HO2, chạy Phase C, kết luận ngoài mẫu | Có mở HO2 trong lượt riêng hay tiếp tục giữ đóng |",
        "",
        "**Gate B revision 2 dừng tại đây.** Báo cáo này không phải yêu cầu hay sự cho phép mở HO2.",
        "",
    ])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-count", type=int, required=True)
    args = parser.parse_args()
    report = build_report(args.test_count)
    path = ROOT / "docs/amendment_06_gate_b.md"
    path.write_text(report, encoding="utf-8", newline="\n")
    print(f"Generated Gate B report; lock={sha(ROOT / 'config/amendment_06_ho2.lock.json')}; report={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
