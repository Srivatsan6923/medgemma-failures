"""OpenAI-compatible chat client with an on-disk reply cache.

Both backends speak the OpenAI API: our vLLM servers (MedGemma, Gemma-3) and
OpenRouter (Llama). Every reply is stored under a hash of the model and the full
request, so rerunning a config replays the same replies without calling the model.
"""

import hashlib
import json
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from openai import OpenAI
from tqdm import tqdm

from clinfail.utils.config import ModelSpec

OPENROUTER_URL = "https://openrouter.ai/api/v1"


@dataclass(frozen=True)
class ChatRequest:
    messages: tuple[tuple[str, str], ...]  # (role, content) pairs
    temperature: float
    max_tokens: int
    seed: int
    sample_idx: int = 0
    top_logprobs: int = 0

    def key(self, model_id: str) -> str:
        blob = json.dumps({"model": model_id, **asdict(self)}, sort_keys=True).encode()
        return hashlib.sha256(blob).hexdigest()


@dataclass
class Completion:
    text: str
    finish_reason: str | None
    usage: dict[str, int] = field(default_factory=dict)
    logprobs: list[dict[str, Any]] | None = None
    cached: bool = False


class LLMClient:
    def __init__(self, spec: ModelSpec, cache_dir: Path) -> None:
        if spec.backend == "openrouter":
            base_url, api_key = OPENROUTER_URL, os.environ["OPENROUTER_API_KEY"]
        else:
            base_url, api_key = os.environ[spec.base_url_env], os.environ["VLLM_API_KEY"]
        self.spec = spec
        self.cache_dir = cache_dir / spec.alias
        self.client = OpenAI(base_url=base_url, api_key=api_key, max_retries=6, timeout=60)

    def complete(self, req: ChatRequest) -> Completion:
        key = req.key(self.spec.model_id)
        path = self.cache_dir / key[:2] / f"{key}.json"
        if path.exists():
            return Completion(**json.loads(path.read_text(encoding="utf-8")), cached=True)
        comp = self._call(req)
        payload = asdict(comp)
        del payload["cached"]
        path.parent.mkdir(parents=True, exist_ok=True)
        # write to a temp file first so parallel workers never see a half-written cache entry
        tmp = path.with_suffix(f".{os.getpid()}.{threading.get_ident()}.tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, path)
        return comp

    def _call(self, req: ChatRequest) -> Completion:
        logprobs = {"logprobs": True, "top_logprobs": req.top_logprobs} if req.top_logprobs else {}
        resp = self.client.chat.completions.create(
            model=self.spec.model_id,
            messages=[{"role": r, "content": c} for r, c in req.messages],
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            seed=req.seed + req.sample_idx,
            # long reasoning replies (MedGemma on exam questions) need more than 60 s
            timeout=60 + req.max_tokens / 10,
            **logprobs,
        )
        choice = resp.choices[0]
        lp = None
        if choice.logprobs and choice.logprobs.content:
            lp = [t.model_dump() for t in choice.logprobs.content]
        usage = resp.usage.model_dump() if resp.usage else {}
        return Completion(
            text=choice.message.content or "",
            finish_reason=choice.finish_reason,
            usage={k: v for k, v in usage.items() if isinstance(v, int)},
            logprobs=lp,
        )

    def complete_many(self, reqs: list[ChatRequest], concurrency: int) -> list[Completion]:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            return list(tqdm(pool.map(self.complete, reqs), total=len(reqs), desc=self.spec.alias))
