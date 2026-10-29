"""How often do the two triggers appear in real-style notes? Counted with regular
expressions over MTSamples, a public set of medical transcription samples.

  A: a discharge summary that describes a home drug as continued
     (optionally: with no discharge-medication section)
  B: any note that attributes a diagnosis to a person ("working diagnosis",
     "confirmed by Dr", "per the referring physician")

Prints example matches for a manual check and writes results/prevalence.json.

    python scripts/prevalence.py
"""

import json
import re
from pathlib import Path

from datasets import load_dataset

REVISION = "139c3fb2d00cd390766b15ff905f88dd40e0faee"
CONTINUED = re.compile(
    r"\b(?:was|were|been) continued\b"
    r"|\bcontinued (?:on|at) (?:his|her|the|their) (?:home|usual|same|current)\b"
    r"|\bcontinued (?:his|her|their) (?:home|usual|outpatient)\b",
    re.I,
)
DISCHARGE_MEDS = re.compile(
    r"discharge medications?|medications? (?:on|at|upon) discharge|discharged (?:home )?on\b", re.I
)
ATTRIBUTED_DX = re.compile(
    r"working diagnosis|(?:diagnos\w*|confirmed) by (?:dr\b|doctor|the (?:attending|referring|primary|outside))|"
    r"per (?:the )?(?:referring|outside|primary) (?:physician|doctor|provider)|"
    r"(?:referring|outside) (?:physician|doctor|hospital)[^.]{0,80}diagnos",
    re.I,
)
# most "continued" sentences are about inpatient drugs (IV antibiotics, heparin), so we also
# count only those that name a home drug or one of our target drugs ("home health" is a service)
HOME_DRUG = re.compile(
    r"\bhome\b(?! health)|\busual\b|\boutpatient\b|\bchronic\b|prior to admission|"
    r"lisinopril|metformin|apixaban|eliquis|warfarin|coumadin|ibuprofen|furosemide|lasix|metoprolol|"
    r"simvastatin|glipizide|spironolactone|amlodipine|clopidogrel|plavix",
    re.I,
)


def sentence(text: str, m: re.Match) -> str:
    start = max(text.rfind(".", 0, m.start()), text.rfind("\n", 0, m.start())) + 1
    end = text.find(".", m.end())
    return " ".join(text[start : end if end > 0 else len(text)].split())


def snippet(text: str, m: re.Match, width: int = 110) -> str:
    return " ".join(text[max(0, m.start() - width) : m.end() + width].split())


def main() -> None:
    ds = load_dataset("harishnair04/mtsamples", split="train", revision=REVISION)
    notes = [(r["medical_specialty"].strip(), r["transcription"] or "") for r in ds]
    dc = [t for s, t in notes if s == "Discharge Summary"]

    cont = [t for t in dc if CONTINUED.search(t)]
    no_list = [t for t in cont if not DISCHARGE_MEDS.search(t)]
    print(f"Discharge summaries: {len(dc)}")
    print(f"  documenting a medication as continued: {len(cont)} ({len(cont) / len(dc):.1%})")
    print(f"  ...of which without any discharge-medication section: {len(no_list)}")
    for t in cont[:8]:
        print("   A>", snippet(t, CONTINUED.search(t)))

    home = [t for t in cont if any(HOME_DRUG.search(sentence(t, m)) for m in CONTINUED.finditer(t))]
    home_no_list = [t for t in home if not DISCHARGE_MEDS.search(t)]
    print(
        f"  restricted to a home or study drug in the 'continued' sentence: {len(home)} "
        f"({len(home) / len(dc):.1%}); of which without a discharge-medication section: "
        f"{len(home_no_list)} ({len(home_no_list) / len(dc):.1%})"
    )
    for t in home:
        for m in CONTINUED.finditer(t):
            if HOME_DRUG.search(sentence(t, m)):
                print("   A home>", sentence(t, m)[:240])

    hits = [t for _, t in notes if ATTRIBUTED_DX.search(t)]
    print(
        f"All notes: {len(notes)}; with an attributed diagnosis phrase: {len(hits)} "
        f"({len(hits) / len(notes):.1%})"
    )
    for t in hits[:: max(1, len(hits) // 10)][:10]:
        print("   B>", snippet(t, ATTRIBUTED_DX.search(t)))

    counts = {
        "revision": REVISION,
        "notes": len(notes),
        "discharge_summaries": len(dc),
        "continued": len(cont),
        "continued_without_discharge_section": len(no_list),
        "continued_home_drug": len(home),
        "continued_home_drug_without_discharge_section": len(home_no_list),
        "attributed_diagnosis": len(hits),
    }
    Path("results/prevalence.json").write_text(
        json.dumps(counts, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
