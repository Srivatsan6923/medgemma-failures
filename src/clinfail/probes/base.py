from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Case:
    """One prompt. Cases built from the same note or item share a pair_id and
    differ only in their condition, which is what makes the comparisons paired."""

    case_id: str
    pair_id: str
    condition: str
    messages: tuple[tuple[str, str], ...]
    gold: dict[str, Any]
    meta: dict[str, Any] = field(default_factory=dict)


class Probe:
    """A probe builds the cases for one experiment and scores the replies."""

    def __init__(self, params: dict[str, Any]) -> None:
        self.params = params

    def build_cases(self, n: int, rng: np.random.Generator) -> list[Case]:
        raise NotImplementedError

    def score(self, case: Case, output: str) -> dict[str, Any]:
        raise NotImplementedError

    def summarize(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError


def read_ids(path: str | None) -> set[str]:
    """IDs listed in a split file, e.g. the development items to exclude."""
    return set(Path(path).read_text().split()) if path else set()
