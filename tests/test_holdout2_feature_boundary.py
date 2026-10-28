from __future__ import annotations

from datetime import date
from decimal import Decimal
import hashlib
import json
import sys

import pandas as pd
import pytest
import yaml

from features.day2_data import build_label_samples, make_customer_features
from features.holdout2_access import require_open_lock
from features.holdout2_features import (attach_holdout2_labels, build_customer_features_at_t,
                                        feature_eligible, outcome_eligible)
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1] / "scripts"))
from evaluate_holdout2_once import create_open_lock, validate_dry_run_t  # noqa: E402


def _order(day: date, customer: str = "c1") -> dict:
    return {"date": day, "customer_key": customer, "is_gift": False, "status": 3,
            "order_sequence": day.toordinal(), "monetary_contribution": Decimal("100"),
            "monetary_A_contribution": Decimal("100"), "revenue_recognized": Decimal("100"),
            "total_price_at_snapshot": Decimal("100"), "total_discount_at_snapshot": Decimal("0"),
            "quantity_total": Decimal("1"), "product_keys": ["p1"], "items": [{"product_key": "p1", "category": "c"}],
            "province": "UNKNOWN", "order_channel": None, "price_adjustment": None,
            "adj_unexplained": False}


def test_yaml_date_conditions_and_boundary_rows() -> None:
    cfg = yaml.safe_load(open("config/amendment_06_ho2.yaml", encoding="utf-8"))
    t2 = date.fromisoformat(cfg["T2"])
    assert cfg["feature_history"]["access_rule"].startswith("inspect inserted_at first")
    assert cfg["label_window"]["evaluator_equivalent_rule"] == "local_date > T2 and local_date <= T2 + 180 days"
    assert not feature_eligible(t2, t2)
    assert feature_eligible(t2 - pd.Timedelta(days=1), t2)
    assert not outcome_eligible(t2, t2)
    assert outcome_eligible(t2 + pd.Timedelta(days=1), t2)
    assert outcome_eligible(t2 + pd.Timedelta(days=180), t2)
    assert not outcome_eligible(t2 + pd.Timedelta(days=181), t2)


def test_feature_builder_matches_existing_fixed_t_features_and_excludes_t_or_later() -> None:
    t = date(2025, 4, 20)
    orders = [_order(date(2025, 1, 1)), _order(date(2025, 4, 19)), _order(t),
              _order(date(2025, 5, 1))]
    samples, _ = build_label_samples(orders, test_start=date(2025, 10, 22), n_days=180, l_days=0, candidates=(t,))
    expected = make_customer_features(orders, as_of=t, customer_keys={"c1"}, analysis_start=date(2024, 4, 1))[0]
    frame = build_customer_features_at_t(orders, t, analysis_start=date(2024, 4, 1))
    row = frame.iloc[0]
    assert row.recency_days == expected["recency_days"]
    assert row.frequency == expected["frequency"]
    assert row.monetary == expected["monetary"]
    assert row.latest_feature_date == date(2025, 4, 19)
    assert (t + pd.Timedelta(days=180)) <= date(2025, 10, 22)
    labeled = attach_holdout2_labels(frame, orders, t, 180)
    assert labeled.label_returned.iloc[0] == 1
    assert samples[0]["label_returned"] == 1


def test_holdout2_loader_refuses_to_run_without_open_lock(tmp_path) -> None:
    with pytest.raises(PermissionError, match="HO2 is closed"):
        require_open_lock(tmp_path)


def test_dry_run_gate_accepts_only_full_dev_horizon_and_rejects_t2() -> None:
    cfg = yaml.safe_load(open("config/amendment_06_ho2.yaml", encoding="utf-8"))
    assert validate_dry_run_t("2025-04-20", cfg) == date(2025, 4, 20)
    with pytest.raises(ValueError, match="T2 or later"):
        validate_dry_run_t("2026-04-20", cfg)
    with pytest.raises(ValueError, match="full label horizon"):
        validate_dry_run_t("2025-04-26", cfg)


def test_open_lock_is_created_once_after_exact_owner_phrase(tmp_path) -> None:
    (tmp_path / "config").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "outputs/metrics").mkdir(parents=True)
    (tmp_path / "config/amendment_06_ho2.yaml").write_text(
        "status: prepared_gate_b_not_open\ntest_opened: false\nT2: '2026-04-20'\n", encoding="utf-8")
    protocol = tmp_path / "docs/analysis_plan_amendment06_ho2.md"
    protocol.write_text("frozen protocol", encoding="utf-8")
    evaluator = tmp_path / "scripts/evaluate_holdout2_once.py"
    evaluator.write_text("frozen evaluator", encoding="utf-8")
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    frozen = {p.relative_to(tmp_path).as_posix(): digest(p) for p in (tmp_path / "config/amendment_06_ho2.yaml", protocol, evaluator)}
    (tmp_path / "config/amendment_06_ho2.lock.json").write_text(json.dumps({
        "amendment_id": "06-HO2", "revision": 2, "status": "prepared_gate_b_not_open",
        "test_opened": False, "frozen_source_sha256": frozen,
    }), encoding="utf-8")
    with pytest.raises(PermissionError, match="did not match"):
        create_open_lock(tmp_path, "wrong")
    opened = create_open_lock(tmp_path, "DUYỆT MỞ HO2")
    assert opened["test_open_count"] == 1
    assert require_open_lock(tmp_path)["status"] == "opened_once"
    with pytest.raises(FileExistsError, match="retry is forbidden"):
        create_open_lock(tmp_path, "DUYỆT MỞ HO2")
