"""Hospital-course narratives from the Asclepius synthetic clinical notes.

Asclepius notes were generated from published case reports, so they read like
real discharge summaries but contain no patient data. We only keep the
"Hospital Course" section and build the rest of the discharge summary ourselves.
"""

import itertools
import re
from pathlib import Path

from datasets import load_dataset

from clinfail.utils.io import cached_jsonl

DATASET_ID = "starmpcc/Asclepius-Synthetic-Clinical-Notes"
REVISION = "52af6897eb1bf275a8937ae54bf42da381fe9421"
HEADER = r"^\s*[A-Z][A-Za-z /&]{2,40}:\s*$"  # a line like "Discharge Instructions:"


def extract_section(note: str, name: str) -> str:
    pattern = rf"^{re.escape(name)}[^\n]*:\s*\n(.*?)(?={HEADER}|\Z)"
    m = re.search(pattern, note, flags=re.M | re.S | re.I)
    return m.group(1).strip() if m else ""


def is_usable(text: str, min_words: int, banned: list[str]) -> bool:
    # skip short narratives, templated ones with [placeholders], and any narrative that
    # already mentions one of our drugs, so the inserted sentence is the only drug cue
    if len(text.split()) < min_words or "[" in text:
        return False
    low = text.lower()
    return not any(re.search(rf"\b{re.escape(b.lower())}\b", low) for b in banned)


def load_hospital_courses(cache_path: Path, n_scan: int, min_words: int, banned: list[str]):
    def build():
        ds = load_dataset(DATASET_ID, split="train", streaming=True, revision=REVISION)
        for r in itertools.islice(ds, n_scan):
            text = extract_section(r["note"], "Hospital Course")
            if is_usable(text, min_words, banned):
                yield {"patient_id": str(r["patient_id"]), "text": text}

    return cached_jsonl(cache_path, build)
