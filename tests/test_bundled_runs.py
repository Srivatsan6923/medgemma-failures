"""The code in this repository regenerates exactly what was run.

For every bundled run: rebuilding its cases from the pinned datasets gives the same
prompts (same sha256 as recorded in meta.json at run time), and re-scoring the stored
replies gives the same verdicts. Needs the processed datasets in data/processed/,
which the loaders download on first use; skipped otherwise.
"""

import gzip
import json
import tempfile
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pytest

from clinfail.probes import PROBES
from clinfail.utils.config import load_experiment
from clinfail.utils.io import write_jsonl

ROOT = Path(__file__).resolve().parents[1]
RUNS = sorted(p for p in (ROOT / "results").iterdir() if (p / "meta.json").exists())
DATA = ["asclepius_courses_v2.jsonl", "medqa_train_v1.jsonl"]

pytestmark = pytest.mark.skipif(
    not all((ROOT / "data" / "processed" / f).exists() for f in DATA),
    reason="processed datasets not downloaded",
)


@pytest.mark.parametrize("run_dir", RUNS, ids=[p.name for p in RUNS])
def test_prompts_and_scores_match_the_run(run_dir, monkeypatch):
    monkeypatch.chdir(ROOT)  # config paths (split files, data cache) are relative to the repo
    cfg = load_experiment(run_dir / "config.yaml")
    probe = PROBES[cfg.probe](cfg.probe_params)
    cases = probe.build_cases(cfg.n_cases, np.random.default_rng(cfg.seed))

    with tempfile.TemporaryDirectory() as tmp:
        sha = write_jsonl(Path(tmp) / "cases.jsonl", (asdict(c) for c in cases))
    assert sha == json.loads((run_dir / "meta.json").read_text())["cases_sha256"]

    by_id = {c.case_id: c for c in cases}
    rows = gzip.decompress((run_dir / "results.jsonl.gz").read_bytes()).decode("utf-8")
    for line in rows.splitlines():
        row = json.loads(line)
        for key, value in probe.score(by_id[row["case_id"]], row["output"]).items():
            assert row[key] == value, (row["case_id"], key)
