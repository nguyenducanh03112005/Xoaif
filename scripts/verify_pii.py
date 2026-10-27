"""Regex tripwire for direct contact details and address-like values in outputs."""

from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".csv", ".md", ".txt", ".json", ".ipynb", ".html", ".xml", ".yaml", ".yml"}
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
VIETNAMESE_PHONE = re.compile(r"(?<!\d)(?:\+?84|0(?![.,]\d))(?:[ \t().-]?\d){8,10}(?!\d)")
HASH_DIGEST = re.compile(r"(?<![0-9A-Fa-f])[0-9A-Fa-f]{64}(?![0-9A-Fa-f])")
ADDRESS_LIKE = re.compile(
    r"\b(?:số\s*)?\d{1,5}(?:/\d{1,5})?\s+"
    r"[\wÀ-ỹĐđ]+(?:\s+[\wÀ-ỹĐđ]+){0,4},?\s+"
    r"(?:phường|xã|quận|huyện|thành phố|tỉnh)\b",
    re.IGNORECASE,
)
FIELD_VALUE = re.compile(
    r"\b(?:full[_ ]?name|phone(?:_number)?|email|shipping[_ ]?address|customer[_ ]?id|order[_ ]?id)\s*[:=]\s*[^,\n]+",
    re.IGNORECASE,
)
PATTERNS = {
    "email": EMAIL,
    "phone": VIETNAMESE_PHONE,
    "address_like": ADDRESS_LIKE,
    "sensitive_field_value": FIELD_VALUE,
}


def _code_and_output_text(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() != ".ipynb":
        return HASH_DIGEST.sub("[digest omitted]", raw)
    try:
        notebook = json.loads(raw)
    except json.JSONDecodeError:
        return raw
    chunks: list[str] = []
    for cell in notebook.get("cells", []):
        source = cell.get("source", "")
        chunks.append("".join(source) if isinstance(source, list) else str(source))
        chunks.append(json.dumps(cell.get("outputs", []), ensure_ascii=False))
    return HASH_DIGEST.sub("[digest omitted]", "\n".join(chunks))


def _scan_files(paths: Iterable[Path]) -> list[tuple[str, str, int]]:
    findings: list[tuple[str, str, int]] = []
    for path in paths:
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = _code_and_output_text(path)
        except OSError:
            findings.append((str(path), "unreadable", 1))
            continue
        for category, pattern in PATTERNS.items():
            count = sum(1 for _ in pattern.finditer(text))
            if count:
                findings.append((str(path.relative_to(PROJECT_ROOT)), category, count))
    return findings


def main() -> int:
    candidates: set[Path] = set()
    for folder in (PROJECT_ROOT / "outputs", PROJECT_ROOT / "notebooks", PROJECT_ROOT / "docs"):
        if folder.exists():
            candidates.update(folder.rglob("*"))
    findings = _scan_files(sorted(candidates))
    if findings:
        print("Potential PII patterns found (matched values suppressed):")
        for file_name, category, count in findings:
            print(f"- {file_name}: {category} matches={count}")
        return 1
    print("PII regex scan passed for docs/, notebooks/, and outputs/; raw/restricted data were not scanned or copied.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
