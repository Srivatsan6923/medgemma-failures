"""Copy finished runs from outputs/ into results/ and write the small derived files
that the analysis needs (so reproduce.py works without downloading any dataset).

    python scripts/bundle.py
"""

import gzip
import json
import re
import shutil
from pathlib import Path

from analyze import RUNS, load, run_dirs
from clinfail.probes.notes import load_courses

RUN_NAMES = [
    "p1_med_status_explore",
    "p1_med_status_explore_medgemma",
    "p1o_override_explore",
    "p1o_age45",
    "p1o_age85",
    "a_confirm_override",
    "a_mech_noflags",
    "a_mech_mitigation",
    "a_mech_paraphrase_1",
    "a_mech_paraphrase_2",
    "p3_anchoring_explore",
    "p3_anchoring_explore_medgemma",
    "b_confirm_anchoring",
    "b_mech_authority",
    "b_mech_authority2x2",
    "b_mech_cot",
    "b_posthoc_certainty",
]
DEATH = re.compile(r"\b(died|expired|passed away|death|deceased|succumbed)\b", re.I)
DIAGNOSIS_Q = re.compile(r"most likely diagnosis\?\s*$", re.I)
# exam stems like "A photograph of the lesion is shown." refer to an image the model can't see
SHOWS_IMAGE = re.compile(r"\b(photograph|photomicrograph|image|is shown|are shown)\b", re.I)
OUT = Path("results")


def copy_runs() -> None:
    # one record per RunPod server: model revision, image, start and end times
    (OUT / "pods").mkdir(parents=True, exist_ok=True)
    for f in (RUNS.parent / "pods").glob("*.json"):
        record = json.loads(f.read_text(encoding="utf-8"))
        if record.get("ready"):
            (OUT / "pods" / f.name).write_text(
                json.dumps(record, indent=2) + "\n", encoding="utf-8"
            )
    for name in RUN_NAMES:
        for d in run_dirs(name).values():
            dest = OUT / d.name
            if dest.exists():
                continue
            dest.mkdir(parents=True)
            for f in ("config.yaml", "meta.json"):
                shutil.copy(d / f, dest / f)
            # mtime=0 keeps the gzip bytes the same each time
            (dest / "results.jsonl.gz").write_bytes(
                gzip.compress((d / "results.jsonl").read_bytes(), mtime=0)
            )
            print(dest)


def data_counts() -> None:
    counts = {}
    for split, src in [("train", "medqa_train"), ("test", "medqa")]:
        lines = Path(f"data/processed/{src}_v1.jsonl").read_text(encoding="utf-8").splitlines()
        counts[f"medqa_{split}_dx"] = sum(
            bool(DIAGNOSIS_Q.search(json.loads(line)["question"])) for line in lines
        )
    counts["dev_a_patients"] = len(
        Path("configs/splits/p1_dev_patient_ids.txt").read_text().split()
    )
    counts["dev_b_items"] = len(Path("configs/splits/p3_dev_item_ids.txt").read_text().split())
    (OUT / "data_counts.json").write_text(json.dumps(counts, indent=2) + "\n", encoding="utf-8")


def death_narratives() -> None:
    """Patient ids of confirmation notes whose hospital course mentions a death."""
    courses, _ = load_courses({})
    used = {r["course_patient_id"] for r in load("a_confirm_override")["medgemma-27b"].values()}
    died = sorted(
        c["patient_id"] for c in courses if c["patient_id"] in used and DEATH.search(c["text"])
    )
    (OUT / "narratives_death.json").write_text(json.dumps(died) + "\n", encoding="utf-8")


def image_items() -> None:
    """Ids of MedQA diagnosis items whose question refers to an image."""
    lines = Path("data/processed/medqa_train_v1.jsonl").read_text(encoding="utf-8").splitlines()
    items = [json.loads(line) for line in lines]
    ids = sorted(
        x["item_id"]
        for x in items
        if DIAGNOSIS_Q.search(x["question"]) and SHOWS_IMAGE.search(x["question"])
    )
    (OUT / "image_items.json").write_text(json.dumps(ids) + "\n", encoding="utf-8")


if __name__ == "__main__":
    copy_runs()
    data_counts()
    death_narratives()
    image_items()
