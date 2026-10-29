import json

import pandas as pd

from clinfail.runner import run_experiment
from clinfail.utils.config import ExperimentConfig, ModelSpec


def test_run_writes_a_complete_run_directory(mcq_dir, fake_backend, monkeypatch):
    monkeypatch.setattr("clinfail.runner.git_hash", lambda: "test")  # tmp dir is not a repo
    cfg = ExperimentConfig(run_name="t", probe="anchoring", models=["m"], n_cases=5)
    models = {"m": ModelSpec(alias="m", backend="openrouter", model_id="x/y")}
    run_dir = run_experiment(cfg, models, mcq_dir / "runs", mcq_dir / "cache")

    for f in ("config.yaml", "cases.jsonl", "results.jsonl", "summary.csv", "meta.json"):
        assert (run_dir / f).exists()
    # the fake model always answers "A", which is correct for every item
    summary = pd.read_csv(run_dir / "summary.csv")
    assert (summary["error"] == 0).all()
    assert json.loads((run_dir / "meta.json").read_text())["n_rows"] == 5 * 4

    # a second run replays every reply from the cache
    run_experiment(cfg, models, mcq_dir / "runs", mcq_dir / "cache")
    assert len(fake_backend) == 5 * 4
