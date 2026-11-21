"""Rebuild every result and figure from data/raw/.

Usage (from the repository root):
    python analysis/run_all.py
"""
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
for script in ("01_rent_trend_tests.py", "02_compare_sources.py", "03_asked_vs_paid.py"):
    print(f"\n== {script}")
    runpy.run_path(str(HERE / script), run_name="__main__")
print("\nDone. Results are in results/, figures in figures/ (copies in docs/assets/).")
