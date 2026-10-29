import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_reproduce_matches_committed_tables_and_figures():
    """scripts/reproduce.py must regenerate exactly the committed tables and figures."""
    env = {**os.environ, "HF_HUB_OFFLINE": "1", "OPENROUTER_API_KEY": ""}
    subprocess.run(
        [sys.executable, "scripts/reproduce.py"], cwd=ROOT, env=env, check=True, capture_output=True
    )
    diff = subprocess.run(
        ["git", "status", "--porcelain", "--", "results/tables", "figures"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert diff.stdout == ""
