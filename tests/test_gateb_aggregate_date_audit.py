from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_committed_aggregate_dates import scan_csv, temporal_value  # noqa: E402


def test_temporal_parser_orders_dates_and_partials() -> None:
    assert temporal_value("2026-04")[1] == "2026-04"
    assert temporal_value("2026-04-20")[0] > temporal_value("2026-04")[0]
    assert temporal_value("2025-Q4")[1] == "2025-Q4"
    assert temporal_value("not-a-date") is None


def test_csv_audit_reads_only_temporal_column(tmp_path: Path) -> None:
    path = tmp_path / "aggregate.csv"
    path.write_text("period,private_note\n2025-01,DO_NOT_ECHO\n2026-04,ALSO_PRIVATE\n", encoding="utf-8")
    result = scan_csv(path)
    assert result["temporal_columns"] == [{"column": "period", "max_local_date_or_period": "2026-04"}]
    assert "private_note" not in str(result)
