"""Experiment and model configs, loaded from the YAML files in configs/."""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ModelSpec:
    alias: str
    backend: str  # "vllm" (our own server) or "openrouter"
    model_id: str
    base_url_env: str = "VLLM_BASE_URL"  # env var holding the vLLM server URL


@dataclass
class ExperimentConfig:
    run_name: str
    probe: str
    models: list[str]
    n_cases: int  # number of base notes or exam items; each gets one case per condition
    samples_per_case: int = 1
    temperature: float = 0.0
    max_tokens: int = 1024
    seed: int = 0
    concurrency: int = 8
    probe_params: dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def hash(self) -> str:
        blob = json.dumps(asdict(self), sort_keys=True).encode()
        return hashlib.sha256(blob).hexdigest()[:12]

    def dump(self, path: Path) -> None:
        path.write_text(yaml.safe_dump(asdict(self), sort_keys=False))


def load_experiment(path: Path, **overrides: Any) -> ExperimentConfig:
    raw = yaml.safe_load(path.read_text())
    return ExperimentConfig(**{**raw, **overrides})


def load_models(path: Path) -> dict[str, ModelSpec]:
    raw = yaml.safe_load(path.read_text())
    return {alias: ModelSpec(alias=alias, **spec) for alias, spec in raw.items()}
