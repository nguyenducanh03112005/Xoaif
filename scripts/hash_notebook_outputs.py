"""Print a stable SHA-256 over cell outputs, excluding run counters and metadata."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = PROJECT_ROOT / "notebooks" / "01_day1_development_eda.ipynb"


def main() -> int:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    outputs = [
        {"cell_type": cell.get("cell_type"), "outputs": cell.get("outputs", [])}
        for cell in notebook.get("cells", [])
        if cell.get("cell_type") == "code"
    ]
    canonical = json.dumps(outputs, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    print(hashlib.sha256(canonical).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
