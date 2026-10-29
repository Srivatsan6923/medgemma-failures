from pathlib import Path

import pytest

from clinfail.models.llm import ChatRequest, LLMClient
from clinfail.utils.config import ExperimentConfig, ModelSpec, load_models

SPEC = ModelSpec(alias="m", backend="openrouter", model_id="x/y")


def req(**kw):
    return ChatRequest(
        messages=(("user", "What is 2 + 3?"),), temperature=0, max_tokens=4, seed=0, **kw
    )


def test_config_hash():
    a = ExperimentConfig(run_name="x", probe="anchoring", models=["m"], n_cases=1)
    b = ExperimentConfig(run_name="x", probe="anchoring", models=["m"], n_cases=2)
    assert (
        a.hash()
        == ExperimentConfig(run_name="x", probe="anchoring", models=["m"], n_cases=1).hash()
    )
    assert a.hash() != b.hash()


def test_unknown_config_key():
    with pytest.raises(TypeError):
        ExperimentConfig(run_name="x", probe="anchoring", models=["m"], n_cases=1, typo=3)


def test_model_registry():
    models = load_models(Path(__file__).parents[1] / "configs" / "models.yaml")
    assert models["llama33-70b"].backend == "openrouter"
    assert models["medgemma-27b"].base_url_env == "VLLM_URL_MEDGEMMA_27B"


def test_cache_hit_skips_network(tmp_path, fake_backend):
    client = LLMClient(SPEC, tmp_path)
    first, second = client.complete(req()), client.complete(req())
    assert (first.text, first.cached) == ("A", False)
    assert (second.text, second.cached) == ("A", True)
    assert len(fake_backend) == 1


def test_sample_idx_changes_key():
    assert req().key("m") != req(sample_idx=1).key("m")


def test_vllm_reads_its_own_url(tmp_path, monkeypatch):
    spec = ModelSpec(alias="m", backend="vllm", model_id="x/y", base_url_env="VLLM_URL_M")
    monkeypatch.setenv("VLLM_API_KEY", "k")
    monkeypatch.setenv("VLLM_URL_M", "http://localhost:8001/v1")
    assert str(LLMClient(spec, tmp_path).client.base_url).startswith("http://localhost:8001")
