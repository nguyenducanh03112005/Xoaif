"""Generate the transparent revision-2 file/hash change log from f67b4b2."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = "f67b4b2"
OUTPUT = ROOT / "docs/amendment_06_revision_log.md"


def _reason(path: str) -> str:
    if path.startswith("docs/analysis_plan_gateb_r2") or path.startswith("outputs/metrics/gateb_r2") or "gateb_r2" in path:
        return "Đăng ký trước và quyết định H2 bằng công suất/RR DEV theo R2."
    if "gateb_r4" in path or path.endswith("analysis_plan_gateb_r4.md"):
        return "Đăng ký/hiệu chuẩn trước H4–H5 trên DEV; không đọc HO2."
    if "gateb_r5" in path or "freeze_gateb_strategies" in path or path.endswith("analysis_plan_gateb_r5.md"):
        return "Chọn/đóng băng tập chiến lược R5 từ DEV; hash artifact, không fit trên HO2."
    if "holdout2" in path or "gateb_lock" in path or "amendment06" in path:
        return "Cổng evaluator, helper, khóa revision 2, hash report hoặc kiểm thử bảo vệ."
    if "ho2_access_audit" in path or "aggregate_date" in path:
        return "R6 audit đường nạp và metadata aggregate trước mở."
    if "canonical_numbers" in path or "gateb_r" in path or "amendment_06" in path:
        return "Đồng bộ số chuẩn và tài liệu Gate B revision 2."
    if path.startswith("tests/"):
        return "Kiểm tra hồi quy cho quy tắc đã đăng ký và ranh giới không mở HO2."
    if path == ".gitignore":
        return "Cho phép đúng aggregate R2/R4/R5 đã review; giữ model/dry-run local ignored."
    return "Thành phần hỗ trợ Gate B revision 2; chỉ DEV/code/metadata, không chứa outcome HO2."


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
    for rel in _changed_paths():
        path = ROOT / rel
        new = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "DELETED"
        rows.append(f"| `{rel}` | `{_old_hash(rel)}` | `{new}` | {_reason(rel)} | 2026-10-28 |")
    return "\n".join([
        "# Nhật ký thay đổi 06-HO2 Gate B revision 2",
        "",
        "Căn cứ so sánh: commit Gate B revision 1 `f67b4b2`. Tất cả sửa đổi đã được thực hiện trước khi mở HO2; không đọc outcome HO2. Hash được tính trực tiếp từ Git blob cũ và byte file hiện hành.",
        "",
        "| File | SHA-256 cũ (f67b4b2) | SHA-256 mới | Lý do | Ngày |",
        "|---|---|---|---|---|",
        *rows,
        "",
        "## Ghi chú quyết định",
        "",
        f"- Lock revision 1 bị supersede bởi SHA-256 `{_old_hash('config/amendment_06_ho2.lock.json')}`; lock mới có `revision: 2`.",
        "- Chọn phương án A cho S3, S6 và v3: final-fit từ toàn bộ DEV multi-snapshot theo recipe đã đăng ký; lý do là tạo artifact chấm cố định trước Gate B. Không dùng metric in-sample để đánh giá tổng quát.",
        "- H2 trở lại giả thuyết chính theo quy tắc R2 đã đăng ký; H1/H2 được xử lý bằng Holm hai kiểm định.",
        "- Không sửa test lock, config split, Amendment 01–05 hoặc artifact test; không chạy evaluator test cũ.",
        "",
    ])


def main() -> int:
    OUTPUT.write_text(build_text(), encoding="utf-8", newline="\n")
    print(f"Wrote revision log with {len(_changed_paths())} paths.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
