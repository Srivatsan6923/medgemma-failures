"""Run an experiment config against one or more models.

    python -m clinfail.cli configs/experiments/b_confirm_anchoring.yaml --use llama33-70b

The run directory goes under $OUTPUT_ROOT/runs (default outputs/runs).
"""

import argparse
import logging
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from clinfail.runner import run_experiment
from clinfail.utils.config import load_experiment, load_models


def main() -> None:
    parser = argparse.ArgumentParser(prog="clinfail")
    parser.add_argument("config", type=Path)
    parser.add_argument("--models", type=Path, default=Path("configs/models.yaml"))
    parser.add_argument("--n-cases", type=int, help="override n_cases, e.g. for a quick test")
    parser.add_argument("--use", nargs="+", help="model aliases to run instead of the config's")
    args = parser.parse_args()

    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)

    overrides = {}
    if args.n_cases:
        overrides["n_cases"] = args.n_cases
    if args.use:
        overrides["models"] = args.use
    cfg = load_experiment(args.config, **overrides)
    out = Path(os.environ.get("OUTPUT_ROOT", "outputs"))
    run_dir = run_experiment(cfg, load_models(args.models), out / "runs", out / "cache")
    print(pd.read_csv(run_dir / "summary.csv").to_string(index=False))
    print(f"run written to {run_dir}")


if __name__ == "__main__":
    main()
