"""Run one experiment config and write a self-contained run directory.

<OUTPUT_ROOT>/runs/<utc time>_<run name>_<config hash>/
    config.yaml    the config as run
    cases.jsonl    every prompt, with its gold answer
    results.jsonl  every reply with its scores (one row per model and case)
    summary.csv    failure rate per model and condition
    meta.json      git commit, hashes of cases and results, model endpoints, timing
"""

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from clinfail.models.llm import ChatRequest, LLMClient
from clinfail.probes import PROBES
from clinfail.utils.config import ExperimentConfig, ModelSpec
from clinfail.utils.io import git_hash, make_run_dir, write_jsonl


def run_experiment(
    cfg: ExperimentConfig, models: dict[str, ModelSpec], output_root: Path, cache_dir: Path
) -> Path:
    probe = PROBES[cfg.probe](cfg.probe_params)
    # the seed fixes which notes or items are drawn, so every model sees the same cases
    cases = probe.build_cases(cfg.n_cases, np.random.default_rng(cfg.seed))

    run_dir = make_run_dir(output_root, cfg.run_name, cfg.hash())
    cfg.dump(run_dir / "config.yaml")
    cases_hash = write_jsonl(run_dir / "cases.jsonl", (asdict(c) for c in cases))
    started = datetime.now(UTC).isoformat()

    pairs = [
        (case, ChatRequest(case.messages, cfg.temperature, cfg.max_tokens, cfg.seed, s))
        for case in cases
        for s in range(cfg.samples_per_case)
    ]
    rows = []
    for alias in cfg.models:
        comps = LLMClient(models[alias], cache_dir).complete_many(
            [req for _, req in pairs], cfg.concurrency
        )
        for (case, req), comp in zip(pairs, comps, strict=True):
            rows.append(
                {
                    "model": alias,
                    "case_id": case.case_id,
                    "pair_id": case.pair_id,
                    "condition": case.condition,
                    "sample_idx": req.sample_idx,
                    "output": comp.text,
                    "finish_reason": comp.finish_reason,
                    "cached": comp.cached,
                    **case.meta,
                    **probe.score(case, comp.text),
                }
            )

    results_hash = write_jsonl(run_dir / "results.jsonl", rows)
    probe.summarize(pd.DataFrame(rows)).to_csv(run_dir / "summary.csv", index=False)
    meta = {
        "git": git_hash(),
        "config_hash": cfg.hash(),
        "cases_sha256": cases_hash,
        "results_sha256": results_hash,
        "n_cases": len(cases),
        "n_rows": len(rows),
        "models": {a: asdict(models[a]) for a in cfg.models},
        "started": started,
        "finished": datetime.now(UTC).isoformat(),
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    return run_dir
