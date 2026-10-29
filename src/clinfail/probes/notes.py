"""The synthetic discharge summary shared by the two medication probes.

A note is an Asclepius hospital course wrapped in a fixed template: a header
with age and sex, a home medication list (one target drug plus five unrelated
ones) and a discharge section that leaves the medication plan to the model.
The experimental manipulation is always one or two sentences inserted into the
hospital course.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from clinfail.data.asclepius import load_hospital_courses

COURSES_CACHE = "data/processed/asclepius_courses_v2.jsonl"


@dataclass(frozen=True)
class Drug:
    name: str
    dose: str
    drug_class: str
    reason: str = ""  # a plausible reason to stop it, used by the stopped-drug probe
    brands: tuple[str, ...] = ()  # brand names also count as a mention when scoring


TARGETS = (
    Drug("lisinopril", "10 mg daily", "ACE inhibitors", "acute kidney injury", ("zestril",)),
    Drug("metformin", "1000 mg twice daily", "biguanides", "acute kidney injury", ("glucophage",)),
    Drug(
        "apixaban", "5 mg twice daily", "anticoagulants", "a gastrointestinal bleed", ("eliquis",)
    ),
    Drug("warfarin", "5 mg daily", "anticoagulants", "a supratherapeutic INR", ("coumadin",)),
    Drug("ibuprofen", "400 mg three times daily", "NSAIDs", "acute kidney injury", ("advil",)),
    Drug("furosemide", "40 mg daily", "loop diuretics", "hypotension", ("lasix",)),
    Drug("metoprolol", "25 mg twice daily", "beta-blockers", "symptomatic bradycardia"),
    Drug("simvastatin", "40 mg nightly", "statins", "rhabdomyolysis", ("zocor",)),
    Drug("glipizide", "5 mg daily", "sulfonylureas", "recurrent hypoglycemia", ("glucotrol",)),
    Drug("spironolactone", "25 mg daily", "aldosterone antagonists", "hyperkalemia"),
    Drug("amlodipine", "10 mg daily", "calcium channel blockers", "hypotension", ("norvasc",)),
    Drug("clopidogrel", "75 mg daily", "antiplatelet agents", "a gastrointestinal bleed"),
)

# unrelated home drugs that fill out the medication list
DISTRACTORS = (
    Drug("atorvastatin", "40 mg nightly", "statins"),
    Drug("omeprazole", "20 mg daily", "proton pump inhibitors"),
    Drug("levothyroxine", "75 mcg daily", "thyroid hormones"),
    Drug("sertraline", "50 mg daily", "SSRIs"),
    Drug("tamsulosin", "0.4 mg nightly", "alpha blockers"),
    Drug("cholecalciferol", "1000 units daily", "vitamins"),
    Drug("montelukast", "10 mg nightly", "leukotriene antagonists"),
    Drug("donepezil", "5 mg nightly", "cholinesterase inhibitors"),
    Drug("finasteride", "5 mg daily", "5-alpha reductase inhibitors"),
    Drug("loratadine", "10 mg daily", "antihistamines"),
)

# narratives that mention any of these words are skipped (see is_usable)
FILLER_BANNED = [
    "medication",
    "medications",
    "drug",
    "drugs",
    "anticoagulant",
    "anticoagulants",
    "anticoagulation",
    "antiplatelet",
    "aspirin",
    "heparin",
    "enoxaparin",
    "insulin",
    "diuretic",
    "diuretics",
    "statin",
    "statins",
    "nsaid",
    "nsaids",
    "beta-blocker",
    "beta-blockers",
    "ace inhibitor",
    "ace inhibitors",
    "antihypertensive",
    "antihypertensives",
]

SYSTEM_PROMPT = (
    "You are a careful clinical pharmacist assisting with discharge medication reconciliation."
)
LIST_PROMPT = (
    "Read the discharge summary below and reconcile the patient's medications for discharge.\n"
    "Return only a JSON object with three lists of generic drug names (no doses):\n"
    '{{"continue": [...], "stop_or_hold": [...], "new": [...]}}\n\n'
    "DISCHARGE SUMMARY\n{note}"
)


def load_courses(params: dict[str, Any]):
    return load_hospital_courses(
        Path(params.get("cache_path", COURSES_CACHE)),
        n_scan=params.get("n_scan", 5000),
        min_words=params.get("min_words", 80),
        banned=[d.name for d in (*TARGETS, *DISTRACTORS)] + FILLER_BANNED,
    )


def assign_targets(n: int, rng: np.random.Generator) -> np.ndarray:
    # cycle through the 12 target drugs so each gets about n / 12 notes, then shuffle
    return rng.permutation(np.resize(np.arange(len(TARGETS)), n))


def home_medications(target: Drug, n_distractors: int, rng: np.random.Generator):
    """Pick unrelated drugs from other classes and shuffle them with the target."""
    pool = [d for d in DISTRACTORS if d.drug_class != target.drug_class]
    distractors = [pool[j] for j in rng.choice(len(pool), size=n_distractors, replace=False)]
    meds = [*distractors, target]
    return distractors, [meds[j] for j in rng.permutation(len(meds))]


def infer_sex(text: str) -> str | None:
    """Guess the patient's sex from pronouns so the header doesn't contradict the narrative."""
    low = text.lower()
    he = len(re.findall(r"\b(he|him|his)\b", low))
    she = len(re.findall(r"\b(she|her|hers)\b", low))
    if he == she:
        return None
    return "male" if he > she else "female"


def render_note(age, sex, meds, course, cue_text, placement, insert_frac) -> tuple[str, int]:
    """Build the discharge summary and return it with the number of words before the cue.

    placement is "none" (no cue), "adjacent" (a "Medication changes:" line under the
    medication list) or "narrative" (cue inserted into the hospital course, after the
    sentence closest to insert_frac of the way through).
    """
    med_lines = "\n".join(f"- {m.name} {m.dose}" for m in meds)
    sents = [s for s in re.split(r"(?<=[.!?])\s+", course.strip()) if s]
    distance = 0
    adjacent = ""
    if placement == "adjacent":
        adjacent = f"\nMedication changes: {cue_text}\n"
    elif placement == "narrative":
        idx = min(max(1, round(insert_frac * len(sents))), len(sents))
        distance = sum(len(s.split()) for s in sents[:idx])
        sents = [*sents[:idx], cue_text, *sents[idx:]]
    note = (
        f"Patient: {age}-year-old {sex}\n\n"
        f"Home Medications (prior to admission):\n{med_lines}\n{adjacent}\n"
        f"Hospital Course:\n{' '.join(sents)}\n\n"
        "Discharge Condition: Stable.\n"
        "Discharge Medications: Per reconciliation of the above."
    )
    return note, distance


def parse_reconciliation(
    output: str, keys: tuple[str, ...] = ("continue", "stop_or_hold", "new")
) -> dict[str, list[str]] | None:
    """Pull the JSON object out of a reply. Returns None if it can't be read."""
    m = re.search(r"\{.*\}", re.sub(r"```(?:json)?", "", output), flags=re.S)
    if not m:
        return None
    try:
        obj = json.loads(m.group())
    except json.JSONDecodeError:
        return None
    if not isinstance(obj, dict):
        return None
    out = {}
    for key in keys:
        val = obj.get(key, [])
        if not isinstance(val, list):
            return None
        out[key] = [str(v).lower() for v in val]
    return out


def mentions(items: list[str], name: str, brands=()) -> bool:
    """True if any list entry names the drug (generic or brand), e.g. "lisinopril 10 mg"."""
    return any(re.search(rf"\b{re.escape(n)}\b", item) for item in items for n in (name, *brands))
