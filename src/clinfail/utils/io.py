import hashlib
import json
import subprocess
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def git_hash() -> str:
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    # mark runs made from uncommitted code so they can't be mistaken for a clean commit
    dirty = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no"], text=True
    ).strip()
    return f"{sha}-dirty" if dirty else sha


def make_run_dir(root: Path, run_name: str, cfg_hash: str) -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    path = root / f"{stamp}_{run_name}_{cfg_hash}"
    path.mkdir(parents=True)
    return path


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> str:
    """Write rows as JSON lines and return the sha256 of the file."""
    text = "".join(
        json.dumps(r, ensure_ascii=False, sort_keys=True, default=str) + "\n" for r in rows
    )
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode()).hexdigest()


def cached_jsonl(
    path: Path, build: Callable[[], Iterable[dict[str, Any]]]
) -> tuple[list[dict[str, Any]], str]:
    """Load rows from a JSONL cache, building it first if it doesn't exist yet.

    The sha256 of the file is stored with every case. The runs were made on Windows, so
    the cache is always written with CRLF line endings to give the same file, and the
    same hash, on every OS.
    """
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in build()),
            encoding="utf-8",
            newline="\r\n",
        )
    raw = path.read_bytes()
    rows = [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
    return rows, hashlib.sha256(raw).hexdigest()
