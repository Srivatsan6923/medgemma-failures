"""Download the pinned datasets and build the caches in data/processed/.

    python scripts/get_data.py

Only needed for fresh runs, scripts/bundle.py and tests/test_bundled_runs.py;
reproduce.py works without it. The probes also build these caches on first use.
"""

from pathlib import Path

from clinfail.data.mcq import load_mcq
from clinfail.probes.notes import load_courses

if __name__ == "__main__":
    courses, sha = load_courses({})
    print(f"Asclepius hospital courses: {len(courses)} (sha256 {sha[:12]})")
    for source in ("medqa_train", "medqa"):
        items, sha = load_mcq(source, Path(f"data/processed/{source}_v1.jsonl"))
        print(f"MedQA {source}: {len(items)} items (sha256 {sha[:12]})")
