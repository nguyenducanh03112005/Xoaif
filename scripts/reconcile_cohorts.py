"""Compatibility entry point for the verified pre-T aggregate reconciliation."""

from pathlib import Path
import runpy

if __name__ == "__main__":
    target = Path(__file__).with_name("build_pretest_evidence.py")
    runpy.run_path(str(target), run_name="__main__")
