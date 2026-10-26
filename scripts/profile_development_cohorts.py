"""Summarize effective-dev repeat frequency and calendar-only N/W feasibility."""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
import csv
import json
from pathlib import Path
import sys

import duckdb
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ingest.analysis_amendment import load_analysis_amendment


def main() -> int:
    try:
        split = yaml.safe_load((PROJECT_ROOT / "config/split.yaml").read_bytes())
        amendment, amendment_hash, _ = load_analysis_amendment(PROJECT_ROOT)
        analysis_start = date.fromisoformat(str(amendment["analysis_start"]))
        test_start = date.fromisoformat(str(split["test_start"]))
        n_candidates = sorted(set(int(n) for n in split["n_candidates_days"]))
        w_candidates = sorted(set(int(w) for w in [*split["sensitivity_window_days"], int(split["window_days"])]))
        l_days = int(split["l_candidates_days"][0])
        minimum = int(split["min_test_eligible_customers"])
        db_path = PROJECT_ROOT / "data/restricted/xoaif_dev.duckdb"
        con = duckdb.connect(str(db_path), read_only=True)
        db_min, db_max, db_count = con.execute("SELECT MIN(local_date), MAX(local_date), COUNT(*) FROM fact_orders").fetchone()
        if db_min is None or db_min < analysis_start or db_max >= test_start:
            raise ValueError("development warehouse violates the amended date bounds")

        freq_rows = con.execute("""
            SELECT order_count, COUNT(*) AS customers
            FROM (
              SELECT customer_key, COUNT(*) AS order_count
              FROM fact_orders
              WHERE status_code=3 AND customer_key IS NOT NULL
              GROUP BY customer_key
            )
            GROUP BY order_count ORDER BY order_count
        """).fetchall()
        customer_count = sum(int(customers) for _, customers in freq_rows)
        repeat_customers = sum(int(customers) for orders, customers in freq_rows if int(orders) >= 2)
        frequency_path = PROJECT_ROOT / "outputs/tables/day1_customer_order_frequency_effective.csv"
        frequency_path.parent.mkdir(parents=True, exist_ok=True)
        with frequency_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["valid_status3_orders_per_customer", "customers"])
            writer.writerows(freq_rows)

        cohort_rows = []
        for n_days in n_candidates:
            for w_days in w_candidates:
                end_exclusive = test_start - timedelta(days=n_days + l_days)
                window_start = end_exclusive - timedelta(days=w_days)
                if window_start < analysis_start:
                    eligible = 0
                    calendar_feasible = False
                else:
                    eligible = int(con.execute(
                        """SELECT COUNT(DISTINCT customer_key) FROM fact_orders
                           WHERE status_code=3 AND customer_key IS NOT NULL
                             AND local_date>=? AND local_date<?""",
                        [analysis_start, window_start],
                    ).fetchone()[0])
                    calendar_feasible = True
                cohort_rows.append({
                    "N_days": n_days,
                    "W_days": w_days,
                    "T_window_start": window_start.isoformat(),
                    "T_window_end_exclusive": end_exclusive.isoformat(),
                    "eligible_customers_before_first_T": eligible,
                    "operational_floor": minimum,
                    "calendar_feasible": calendar_feasible,
                    "passes_operational_floor": eligible >= minimum,
                    "feasibility_status": "not_feasible_before_analysis_start" if not calendar_feasible else ("passes_floor_only" if eligible >= minimum else "below_operational_floor"),
                })
        con.close()

        cohort_path = PROJECT_ROOT / "outputs/tables/day1_sensitivity_feasibility.csv"
        with cohort_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(cohort_rows[0]))
            writer.writeheader()
            writer.writerows(cohort_rows)

        summary = {
            "analysis_start": analysis_start.isoformat(),
            "development_exclusive_end": test_start.isoformat(),
            "development_order_count": int(db_count),
            "development_customer_count_status3_nonmissing": customer_count,
            "customers_with_2plus_status3_orders": repeat_customers,
            "customers_with_2plus_rate": repeat_customers / customer_count if customer_count else None,
            "repeat_frequency_distribution": {str(n): int(c) for n, c in freq_rows},
            "sensitivity_feasibility": cohort_rows,
            "test_labels_loaded": False,
            "analysis_amendment_sha256": amendment_hash,
        }
        summary_path = PROJECT_ROOT / "outputs/tables/day1_development_cohort_summary.json"
        summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(f"Effective-dev customer frequency: {repeat_customers}/{customer_count} have 2+ status-3 orders; test labels not used.")
        for row in cohort_rows:
            print(f"N={row['N_days']}, W={row['W_days']}: eligible={row['eligible_customers_before_first_T']}; {row['feasibility_status']}")
        return 0
    except (OSError, UnicodeError, ValueError, KeyError, TypeError, duckdb.Error, yaml.YAMLError) as exc:
        print(f"Development cohort profile stopped ({type(exc).__name__}).")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
