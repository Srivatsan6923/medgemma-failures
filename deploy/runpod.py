"""Serve MedGemma-27B or Gemma-3-27B with vLLM on a RunPod GPU, run configs, shut down.

    python deploy/runpod.py medgemma-27b configs/experiments/a_confirm_override.yaml [more configs]

Both models are served the same way: vllm/vllm-openai:v0.11.0, bf16, pinned model
revisions, the model's own generation config disabled (--generation-config vllm) so
only our sampling settings apply. The pod gets a random API key, and it is always
terminated, even if a run fails. Needs RUNPOD_API_KEY, RUNPOD_VOLUME_ID (a network
volume that caches the weights) and HF_TOKEN in .env.
"""

import argparse
import json
import os
import secrets
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from dotenv import dotenv_values

IMAGE = "vllm/vllm-openai:v0.11.0"
GPUS = ["NVIDIA A100-SXM4-80GB", "NVIDIA A100 80GB PCIe", "NVIDIA H100 NVL"]
# alias: (Hugging Face repo, pinned revision, env var the client reads the server URL from)
MODELS = {
    "medgemma-27b": (
        "google/medgemma-27b-text-it",
        "5b667cf2ddcf064085bc90952edb35a0edbfb79c",
        "VLLM_URL_MEDGEMMA_27B",
    ),
    "gemma3-27b-vllm": (
        "google/gemma-3-27b-it",
        "005ad3404e59d6023443cb575daa05336842228a",
        "VLLM_URL_GEMMA3_27B",
    ),
}
ENV = dotenv_values(".env")


def gql(query: str) -> dict:
    req = urllib.request.Request(
        "https://api.runpod.io/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ENV['RUNPOD_API_KEY']}",
            "User-Agent": "clinfail",
        },
    )
    out = json.load(urllib.request.urlopen(req, timeout=30))
    if "errors" in out:
        raise RuntimeError(out["errors"])
    return out["data"]


def server_args(repo: str, revision: str, key: str) -> str:
    return (
        f"--model {repo} --revision {revision} --served-model-name {repo} --dtype bfloat16 "
        "--max-model-len 16384 --gpu-memory-utilization 0.92 --generation-config vllm "
        f"--max-logprobs 20 --seed 0 --port 8000 --api-key {key}"
    )


def create_pod(alias: str, key: str, gpus: list[str]) -> dict:
    """Ask for each GPU type in turn until one is free."""
    repo, revision, _ = MODELS[alias]
    env = f'[{{key: "HF_TOKEN", value: "{ENV["HF_TOKEN"]}"}}, {{key: "HF_HOME", value: "/workspace/hf"}}]'
    for gpu in gpus:
        try:
            pod = gql(
                f"""mutation {{ podFindAndDeployOnDemand(input: {{
                    cloudType: SECURE, gpuCount: 1, gpuTypeId: "{gpu}", name: "clinfail-{alias}",
                    imageName: "{IMAGE}", dockerArgs: "{server_args(repo, revision, key)}",
                    ports: "8000/tcp", volumeMountPath: "/workspace",
                    networkVolumeId: "{ENV["RUNPOD_VOLUME_ID"]}", containerDiskInGb: 30, env: {env}
                }}) {{ id costPerHr machine {{ gpuDisplayName }} }} }}"""
            )["podFindAndDeployOnDemand"]
        except RuntimeError as e:
            print(f"{gpu}: {e}")
            continue
        if pod:
            return {**pod, "gpu": gpu, "repo": repo, "revision": revision}
    raise RuntimeError("no GPU available in the volume's datacenter")


def status(url: str, key: str | None = None) -> int:
    headers = {"User-Agent": "clinfail"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    try:
        return urllib.request.urlopen(
            urllib.request.Request(url, headers=headers), timeout=20
        ).status
    except urllib.error.HTTPError as e:
        return e.code
    except (urllib.error.URLError, TimeoutError):
        return 0


def terminate(pod_id: str) -> None:
    for _ in range(10):
        try:
            gql(f'mutation {{ podTerminate(input: {{podId: "{pod_id}"}}) }}')
            return
        except (OSError, RuntimeError) as e:
            print(f"terminate failed ({e}); retrying")
            time.sleep(10)
    raise RuntimeError(f"could not terminate pod {pod_id}; terminate it in the RunPod console")


def runtime_info(pod_id: str) -> tuple[str | None, int]:
    """The pod's public URL for port 8000 (None until mapped) and its uptime."""
    query = (
        f'{{ pod(input: {{podId: "{pod_id}"}}) {{ runtime {{ uptimeInSeconds '
        "ports { ip isIpPublic privatePort publicPort } } } }"
    )
    runtime = gql(query)["pod"]["runtime"] or {}
    base = None
    for port in runtime.get("ports") or []:
        if port["privatePort"] == 8000 and port["isIpPublic"]:
            base = f"http://{port['ip']}:{port['publicPort']}"
    return base, runtime.get("uptimeInSeconds") or 0


def wait_ready(pod_id: str, key: str, timeout_min: int = 40) -> str:
    deadline = time.time() + timeout_min * 60
    last_uptime, restarts = 0, 0
    while time.time() < deadline:
        try:
            base, uptime = runtime_info(pod_id)
        except OSError:
            base, uptime = None, last_uptime
        # uptime going backwards means the container restarted (usually out of memory)
        if uptime < last_uptime:
            restarts += 1
            if restarts >= 3:
                raise RuntimeError("container keeps restarting; giving up on this host")
        last_uptime = uptime
        if base and status(f"{base}/v1/models", key) == 200:
            # the server is on a public port, so make sure it rejects requests without the key
            if status(f"{base}/v1/models") != 401:
                raise RuntimeError("server accepts requests without the API key")
            return base
        time.sleep(20)
    raise TimeoutError(f"server not ready after {timeout_min} min")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("alias", choices=MODELS)
    parser.add_argument("configs", nargs="+")
    parser.add_argument("--gpu", action="append", choices=GPUS)
    args = parser.parse_args()
    key = secrets.token_urlsafe(24)
    pod = create_pod(args.alias, key, args.gpu or GPUS)
    record = {
        **pod,
        "alias": args.alias,
        "image": IMAGE,
        "configs": args.configs,
    }
    try:
        print(f"pod {pod['id']} on {pod['gpu']} at ${pod['costPerHr']}/h")
        base = wait_ready(pod["id"], key)
        record["ready"] = True
        print(f"ready: {base}")
        env = {**os.environ, MODELS[args.alias][2]: f"{base}/v1", "VLLM_API_KEY": key}
        for cfg in args.configs:
            subprocess.run(
                [sys.executable, "-m", "clinfail.cli", cfg, "--use", args.alias],
                env=env,
                check=True,
            )
    finally:
        terminate(pod["id"])
        out = Path(ENV.get("OUTPUT_ROOT") or "outputs") / "pods" / f"{pod['id']}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(record, indent=2))
        print(f"pod {pod['id']} terminated; record at {out}")


if __name__ == "__main__":
    main()
