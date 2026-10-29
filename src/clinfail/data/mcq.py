"""MedQA-USMLE four-option exam questions."""

from pathlib import Path

from datasets import load_dataset

from clinfail.utils.io import cached_jsonl

LETTERS = ("A", "B", "C", "D")
DATASET_ID = "GBaker/MedQA-USMLE-4-options"
REVISION = "0fb93dd23a7339b6dcd27e241cb9b5eca62d4d18"
SPLITS = {"medqa": "test", "medqa_train": "train"}


def normalize_medqa(rows):
    return [
        {
            "item_id": f"medqa-{i}",
            "source": "medqa",
            "question": r["question"].strip(),
            "options": {k: r["options"][k].strip() for k in LETTERS},
            "answer": r["answer_idx"],
            "subject": r.get("meta_info", ""),
        }
        for i, r in enumerate(rows)
    ]


def load_mcq(source: str, cache_path: Path):
    split = SPLITS[source]
    return cached_jsonl(
        cache_path,
        lambda: normalize_medqa(load_dataset(DATASET_ID, split=split, revision=REVISION)),
    )
