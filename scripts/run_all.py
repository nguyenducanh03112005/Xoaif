"""Run the locked development-only analysis pipeline with installed dependencies."""

from __future__ import annotations

from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUN_ENV = os.environ.copy()
RUN_ENV["PATH"] = str(Path(sys.executable).resolve().parent) + os.pathsep + RUN_ENV.get("PATH", "")
RUN_ENV["IPYTHONDIR"] = str(Path(tempfile.gettempdir()) / "xoaif_ipython")
RUN_ENV["PYTHONPATH"] = str(PROJECT_ROOT / "scripts") + os.pathsep + RUN_ENV.get("PYTHONPATH", "")
STEP_TIMEOUT_SECONDS = 1200


def _test_result_says_opened() -> bool:
    result = PROJECT_ROOT / "outputs" / "metrics" / "test_eval.json"
    if not result.is_file():
        return False
    try:
        data = json.loads(result.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return data.get("status") == "completed_single_test_open"


def run_step(label: str, command: list[str]) -> int:
    print(f"\n=== {label} ===", flush=True)
    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            check=False,
            env=RUN_ENV,
            timeout=STEP_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        print(f"Stopped: {label} exceeded {STEP_TIMEOUT_SECONDS} seconds and was terminated.", flush=True)
        return 124
    if completed.returncode != 0:
        print(f"Stopped: {label} exited with code {completed.returncode}.", flush=True)
    return completed.returncode


def main() -> int:
    python = sys.executable
    # Opening test is irreversible. Once the exclusive lock exists, the runner
    # must only validate frozen artifacts and safe checks; it must never
    # execute notebooks, model selection, or the test evaluator again.
    lock_path = PROJECT_ROOT / "outputs" / "metrics" / "test_opened.lock.json"
    if not lock_path.exists() and _test_result_says_opened():
        # A fresh clone may miss the (git-ignored) lock file while the committed
        # result already records the one-time test opening. Never fall through to
        # the pre-test pipeline in that state.
        print(
            "Stopped: outputs/metrics/test_eval.json records a completed single test opening, "
            "but outputs/metrics/test_opened.lock.json is missing from this checkout.\n"
            "Refusing to run the pre-test pipeline. Restore the lock file from the original "
            "workspace (git add -f outputs/metrics/test_opened.lock.json) or run only: "
            "python -m pytest -q; python scripts/verify_pii.py; python scripts/verify_readonly.py",
            flush=True,
        )
        return 2
    if lock_path.exists():
        # A fresh clone ships neither data/raw nor the intermediate model/table inputs.
        # In that case only the shipped part of the seal can be verified.
        has_raw = (PROJECT_ROOT / "data" / "raw").is_dir()
        safe_steps = []
        if has_raw:
            safe_steps.append(("verify locked split and snapshot metadata", [python, "scripts/verify_split_lock.py"]))
        else:
            print("Note: data/raw is not present (clone mode); skipping raw snapshot verification.", flush=True)
        safe_steps += [
            ("verify GET-only API policy", [python, "scripts/verify_readonly.py"]),
            ("verify closed Gate B 06-HO2 revision 3 lock",
             [python, "scripts/verify_gateb_lock.py"] + ([] if has_raw else ["--shipped-only"])),
            (
                "verify Amendment 05 and single-open evidence",
                [python, "scripts/verify_day3_locks.py"] + ([] if has_raw else ["--shipped-only"]),
            ),
            ("run non-opening automated tests", [python, "-m", "pytest", "-q"]),
            ("scan current text deliverables for PII patterns", [python, "scripts/verify_pii.py"]),
            ("check dashboard aggregate inputs", [python, "scripts/dashboard_smoke.py"]),
        ]
        for label, command in safe_steps:
            if run_step(label, command) != 0:
                return 1
        print("\nPost-test safe verification completed. No development model was refit or test evaluation repeated.", flush=True)
        return 0

    preflight_steps = [
        ("verify split and snapshot lock", [python, "scripts/verify_split_lock.py"]),
        ("verify GET-only API policy", [python, "scripts/verify_readonly.py"]),
        ("scan docs, notebooks, and outputs for PII patterns", [python, "scripts/verify_pii.py"]),
        ("run pytest", [python, "-m", "pytest", "-q"]),
        (
            "profile pre-opening records and development-only money candidates",
            [python, "scripts/profile_analysis_start.py"],
        ),
        (
            "build or verify development-only DuckDB warehouse",
            [python, "scripts/build_dev_warehouse.py", "--reuse-if-current"],
        ),
        ("profile development customer frequency and sensitivity feasibility", [python, "scripts/profile_development_cohorts.py"]),
        ("refresh Day 1 tables and split timeline", [python, "scripts/build_day1_artifacts.py"]),
    ]
    for label, command in preflight_steps:
        if run_step(label, command) != 0:
            return 1

    money_gate_code = run_step(
        "audit development money and apply the owner-approved stop gate",
        [python, "scripts/audit_money.py"],
    )
    if money_gate_code == 3:
        if run_step(
            "rescan deliverables after the money audit",
            [python, "scripts/verify_pii.py"],
        ) != 0:
            return 1
        print(
            "Pipeline stopped safely at the amendment-03 negative-revenue gate; "
            "test labels and behavior were not loaded.",
            flush=True,
        )
        return 0
    if money_gate_code != 0:
        return 1

    post_money_steps = [
        ("verify Windows Jupyter kernel uses the project interpreter", [python, "scripts/verify_jupyter_kernel.py"]),
        (
            "execute Day 1 development EDA notebook",
            [
                python,
                "-m",
                "nbconvert",
                "--to",
                "notebook",
                "--execute",
                "--inplace",
                "--ExecutePreprocessor.timeout=600",
                "--ExecutePreprocessor.kernel_name=python3",
                "notebooks/01_day1_development_eda.ipynb",
            ],
        ),
        ("scan Day 1 notebook outputs for PII", [python, "scripts/verify_pii.py"]),
        (
            "execute Day 2 preprocessing and pre-registered development labels",
            [python, "-m", "nbconvert", "--to", "notebook", "--execute", "--inplace", "--ExecutePreprocessor.timeout=900", "--ExecutePreprocessor.kernel_name=python3", "notebooks/02_preprocess.ipynb"],
        ),
        (
            "execute Day 2 RFM segmentation and money sensitivities",
            [python, "-m", "nbconvert", "--to", "notebook", "--execute", "--inplace", "--ExecutePreprocessor.timeout=900", "--ExecutePreprocessor.kernel_name=python3", "notebooks/04_unsupervised.ipynb"],
        ),
        (
            "execute Day 2 supervised temporal validation and sensitivity models",
            [python, "-m", "nbconvert", "--to", "notebook", "--execute", "--inplace", "--ExecutePreprocessor.timeout=900", "--ExecutePreprocessor.kernel_name=python3", "notebooks/03_supervised.ipynb"],
        ),
        (
            "execute Day 2 product basket rules",
            [python, "-m", "nbconvert", "--to", "notebook", "--execute", "--inplace", "--ExecutePreprocessor.timeout=900", "--ExecutePreprocessor.kernel_name=python3", "notebooks/05_combo.ipynb"],
        ),
        ("build Day 2 summary, walkthrough, FAQ, and Day 3 input inventory", [python, "scripts/build_day2_docs.py"]),
        ("run the one-time preregistered Day 2B experiments", [python, "scripts/run_day2b.py"]),
        ("scan all Day 2 documents, tables, and notebook outputs for PII", [python, "scripts/verify_pii.py"]),
    ]
    for label, command in post_money_steps:
        if run_step(label, command) != 0:
            return 1
    print("\nDay 2 pipeline completed. Test labels and test behavior were not loaded; Day 3 was not started.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
