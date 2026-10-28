"""Freeze preregistered Gate B scoring artifacts using DEV labels only."""

from __future__ import annotations

from datetime import date
import hashlib
import json
from pathlib import Path
import sys

import joblib
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from features.day2_data import LABEL_T_CANDIDATES, load_dev_orders  # noqa: E402
from features.repurchase_v3 import build_multisnapshot_samples  # noqa: E402
from evaluate_repurchase_wp5c_dev import _train_mapping  # noqa: E402
from models.classify import NUMERIC_COLUMNS as D005_NUMERIC, CATEGORICAL_COLUMNS as D005_CATEGORICAL  # noqa: E402
from models.repurchase_v3 import MODEL_FEATURES, _new_model  # noqa: E402

SEED = 20261028
DEV_END = date(2025, 10, 22)
ARTIFACT_DIR = ROOT / "outputs/models/gateb_r5"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dump(name: str, obj: object) -> dict:
    path = ARTIFACT_DIR / name
    joblib.dump(obj, path)
    return {"path": path.relative_to(ROOT).as_posix(), "sha256": _sha(path), "bytes": path.stat().st_size}


def _sign_fit(frame, column: str) -> dict:
    x = frame[[column]].astype(float).to_numpy()
    y = frame.label_returned.astype(int).to_numpy()
    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(C=10, class_weight="balanced", solver="lbfgs",
                                           max_iter=2000, random_state=SEED)),
    ])
    model.fit(x, y)
    coef = float(model.named_steps["classifier"].coef_[0, 0])
    if not np.isfinite(coef) or coef == 0:
        raise ValueError(f"Non-finite/zero registered baseline coefficient for {column}")
    return {"feature": column, "standardized_coefficient": coef,
            "direction": 1 if coef > 0 else -1,
            "scoring_rule": f"standardize({column}) * sign(coef)"}


def freeze(frame, d005_path: Path, v2_path: Path, output_path: Path) -> dict:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    y = frame.label_returned.astype(int).to_numpy()
    features = frame[MODEL_FEATURES]
    s3 = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("classifier", DecisionTreeClassifier(max_depth=3, min_samples_leaf=50, random_state=SEED)),
    ]).fit(features, y)
    v3 = _new_model().fit(features, y)
    s3_info = _dump("s3_final_dev.joblib", s3)
    v3_info = _dump("v3_final_dev.joblib", v3)
    s6_mapping, s6_audit = _train_mapping(frame)
    s6_json = ARTIFACT_DIR / "s6_final_dev.json"
    s6_json.write_text(json.dumps({"mapping": s6_mapping, "audit": s6_audit,
                                   "frequency_bins": ["1", "2", ">=3"],
                                   "recency_bins": ["<=30", "31-90", "91-180", ">180"]},
                                  ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    signs = [_sign_fit(frame, "recency_days"), _sign_fit(frame, "frequency")]
    result = {
        "status": "exploratory_dev_only_not_confirmed_out_of_sample",
        "test_raw_or_labels_read": False,
        "preregistration": "docs/analysis_plan_gateb_r5.md",
        "cohort": "DEV multi-snapshot; 12 anchors; N=180; L=7",
        "snapshots": int(len(frame)), "customers": int(frame.customer_key.nunique()),
        "positive_snapshots": int(y.sum()), "seed": SEED,
        "strategy_population_and_fit": {
            "S1": {"eligible": True, "fit_population": "fixed rule, no fit"},
            "S3": {"eligible": True, "fit_population": "all DEV multi-snapshot", "features": MODEL_FEATURES,
                   "parameters": {"max_depth": 3, "min_samples_leaf": 50, "random_state": SEED}, **s3_info},
            "S6": {"eligible": True, "fit_population": "all DEV multi-snapshot", "minimum_train_cell_n": 100,
                   "groups": len(s6_audit), "artifact": s6_json.relative_to(ROOT).as_posix(),
                   "sha256": _sha(s6_json), "bytes": s6_json.stat().st_size},
            "D-005": {"eligible": True, "fit_population": "pre-existing frozen DEV artifact; not refit",
                      "feature_columns": D005_NUMERIC + D005_CATEGORICAL,
                      "path": d005_path.relative_to(ROOT).as_posix(), "sha256": _sha(d005_path)},
            "v2": {"eligible": True, "fit_population": "pre-existing frozen DEV artifact; not refit",
                   "path": v2_path.relative_to(ROOT).as_posix(), "sha256": _sha(v2_path)},
            "v3": {"eligible": True, "fit_population": "all DEV multi-snapshot", "features": MODEL_FEATURES,
                   "parameters": {"C": 10, "class_weight": "balanced", "solver": "lbfgs",
                                  "max_iter": 2000, "random_state": SEED}, **v3_info},
            "recency_only": {"eligible": True, "baseline_only": True, **signs[0]},
            "frequency_only": {"eligible": True, "baseline_only": True, **signs[1]},
        },
        "metrics_on_holdout2": None,
        "artifact_hashes_cover": ["scripts/freeze_gateb_strategies_dev.py", "src/features/repurchase_v3.py",
                                  "scripts/evaluate_repurchase_wp5c_dev.py"],
    }
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> int:
    orders, scope, _ = load_dev_orders()
    if scope.get("test_labels_loaded") or scope.get("test_behavior_loaded"):
        raise RuntimeError("DEV loader reported test access")
    frame = build_multisnapshot_samples(orders, test_start=DEV_END, candidates=LABEL_T_CANDIDATES)
    result = freeze(frame, ROOT / "outputs/models/day2_dev_final_model.joblib",
                    ROOT / "outputs/models/repurchase_features_v2.joblib",
                    ROOT / "outputs/metrics/gateb_r5_strategy_freeze.json")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
