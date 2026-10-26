"""Execute the one-time amendment-04 development experiments and refresh review docs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from verify_split_lock import verify
from features.basket_v2 import run_baskets_v2
from models.segment_v2 import run_segmentation_v2
from models.classify_v2 import run_repurchase_v2
from models.cancel_refund_v2 import run_cancel_refund_v2

STATE_PATH = ROOT / "outputs" / "logs" / "day2b_experiment_state.json"
TASKS = ("combo_v2", "segmentation_v2", "repurchase_features_v2", "cancel_return_optional")
OUTPUTS = (
    "outputs/tables/companion_products_v2.csv",
    "outputs/tables/rules_v2.csv",
    "outputs/tables/combos_v2.csv",
    "outputs/tables/segments_v2.csv",
    "outputs/tables/segment_profiles_v2.csv",
    "outputs/metrics/day2b_baskets.json",
    "outputs/metrics/day2b_segmentation.json",
    "outputs/metrics/dev_final_models_v2.json",
    "outputs/metrics/day2b_cancel_model.json",
    "docs/leakage_review_cancel.md",
)


def _write_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _run_once(state: dict, name: str, function):
    status = state["tasks"][name]
    if status == "complete":
        return None
    if status == "started":
        raise RuntimeError(f"Registered experiment {name} was interrupted after starting; amendment 04 forbids rerunning it.")
    state["tasks"][name] = "started"
    _write_state(state)
    result = function()
    state["tasks"][name] = "complete"
    _write_state(state)
    return result


def main() -> int:
    try:
        _, _, _, _, amendment_hash = verify()
        if amendment_hash == "not registered":
            raise ValueError("Amendment 04 is not sealed")
        if STATE_PATH.exists():
            state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            if state.get("amendment_04_sha256") != amendment_hash:
                raise ValueError("Day 2B experiment state is bound to another amendment hash")
            if state.get("status") == "complete":
                missing = [path for path in OUTPUTS if not (ROOT / path).is_file()]
                if missing:
                    raise ValueError("Completed Day 2B outputs are missing; refusing a second experiment run")
                from build_day2b_docs import main as build_docs
                if build_docs() != 0:
                    raise RuntimeError("Day 2B documentation refresh failed")
                print("Amendment-04 experiments already complete; refreshed docs from frozen metrics and skipped all reruns.")
                return 0
            if any(value == "started" for value in state.get("tasks", {}).values()):
                raise ValueError("A Day 2B experiment was interrupted; refusing to retry under the one-run limit")
        else:
            state = {
                "status": "started",
                "amendment_04_sha256": amendment_hash,
                "test_labels_loaded": False,
                "test_behavior_loaded": False,
                "day3_started": False,
                "tasks": {name: "pending" for name in TASKS},
            }
            _write_state(state)

        _run_once(state, "combo_v2", run_baskets_v2)
        _run_once(state, "segmentation_v2", run_segmentation_v2)
        _run_once(state, "repurchase_features_v2", run_repurchase_v2)
        _run_once(state, "cancel_return_optional", run_cancel_refund_v2)

        # The documentation builder reads the registered metrics and writes the leakage review.
        from build_day2b_docs import main as build_docs
        if build_docs() != 0:
            raise RuntimeError("Day 2B documentation generation failed")
        missing = [path for path in OUTPUTS if not (ROOT / path).is_file()]
        if missing:
            raise ValueError(f"Day 2B output missing: {missing}")
        state["status"] = "complete"
        state["docs_refreshed"] = True
        state["test_labels_loaded"] = False
        state["test_behavior_loaded"] = False
        state["day3_started"] = False
        _write_state(state)
        print(f"Day 2B completed once under amendment 04 ({amendment_hash}); test remains closed; Day 3 not started.")
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError, RuntimeError) as exc:
        print(f"Day 2B stopped ({type(exc).__name__}); no order identifiers or PII were printed.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
