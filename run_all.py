"""Rebuild the clinic database and regenerate every evidence file."""

import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [
    ROOT / "portfolio-1-database-design" / "seed.py",
    ROOT / "portfolio-2-query-optimisation" / "run_queries.py",
    ROOT / "portfolio-3-transactions-concurrency" / "transactions.py",
    ROOT / "portfolio-4-nosql" / "encounter_notes.py",
    ROOT / "portfolio-5-distributed-cloud" / "simulate_cluster.py",
]

if __name__ == "__main__":
    for step in STEPS:
        print(f"\n=== {step.relative_to(ROOT)} ===")
        runpy.run_path(str(step), run_name="__main__")
    print("\nPortfolio evidence regenerated.")
