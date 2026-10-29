"""Stopped-drug probe (our first candidate, which did not turn up a failure).

Question: does the model keep a drug on the discharge list after the note says
it was stopped or held? Each note gets six versions:

  active_silent        drug on the home list, never mentioned again (should be kept)
  active_mentioned     "X was continued at the home dose throughout the admission."
  stop_adjacent        stop instruction on a line right under the medication list
  stop_narrative       the same stop instruction, inside the hospital course
  held_narrative       "X was held ...; it may be resumed at follow-up"
  stopclass_narrative  the whole drug class is stopped, without naming X

A case fails when the target's place in the reply is wrong: listed as continued
when it was stopped or held, or missing when it was active.
"""

import numpy as np
import pandas as pd

from clinfail.probes.base import Case, Probe
from clinfail.probes.notes import (
    LIST_PROMPT,
    SYSTEM_PROMPT,
    TARGETS,
    Drug,
    assign_targets,
    home_medications,
    infer_sex,
    load_courses,
    mentions,
    parse_reconciliation,
    render_note,
)

PLACEMENT = {
    "active_silent": "none",
    "active_mentioned": "narrative",
    "stop_adjacent": "adjacent",
    "stop_narrative": "narrative",
    "held_narrative": "narrative",
    "stopclass_narrative": "narrative",
}
CONDITIONS = list(PLACEMENT)


def cue(drug: Drug, condition: str) -> str:
    name = drug.name.capitalize()
    stop = f"{name} was discontinued due to {drug.reason} and should not be restarted."
    return {
        "active_mentioned": f"{name} was continued at the home dose throughout the admission.",
        "stop_adjacent": stop,
        "stop_narrative": stop,
        "held_narrative": f"{name} was held due to {drug.reason}; it may be resumed at follow-up if appropriate.",
        "stopclass_narrative": f"Given {drug.reason}, all {drug.drug_class} were discontinued and should not be restarted.",
    }[condition]


class MedStatusProbe(Probe):
    def build_cases(self, n: int, rng: np.random.Generator) -> list[Case]:
        p = self.params
        courses, courses_sha = load_courses(p)
        lo, hi = p.get("insert_frac_range", [0.3, 0.7])
        course_idx = rng.permutation(len(courses))[:n]
        target_ids = assign_targets(n, rng)

        cases = []
        for i, ci in enumerate(course_idx):
            target = TARGETS[target_ids[i]]
            distractors, meds = home_medications(target, p.get("n_distractors", 5), rng)
            age = int(rng.integers(45, 90))
            course = courses[ci]["text"]
            sex = infer_sex(course) or str(rng.choice(["male", "female"]))
            insert_frac = float(rng.uniform(lo, hi))
            for cond in p.get("conditions", CONDITIONS):
                placement = PLACEMENT[cond]
                cue_text = None if placement == "none" else cue(target, cond)
                note, distance = render_note(
                    age, sex, meds, course, cue_text, placement, insert_frac
                )
                cases.append(
                    Case(
                        case_id=f"{i}-{cond}",
                        pair_id=str(i),
                        condition=cond,
                        messages=(
                            ("system", SYSTEM_PROMPT),
                            ("user", LIST_PROMPT.format(note=note)),
                        ),
                        gold={
                            "target": target.name,
                            "target_brands": list(target.brands),
                            "target_active": cond.startswith("active"),
                            "distractors": [d.name for d in distractors],
                        },
                        meta={
                            "source": "synthetic-real-derived",
                            "target": target.name,
                            "target_class": target.drug_class,
                            "cue_distance_words": distance,
                            "note_words": len(note.split()),
                            "course_patient_id": courses[ci]["patient_id"],
                            "courses_sha256": courses_sha,
                        },
                    )
                )
        return cases

    def score(self, case: Case, output: str) -> dict:
        parsed = parse_reconciliation(output)
        if parsed is None:
            return {"parse_ok": False, "failed": False, "target_in_continue": None}
        g = case.gold
        in_cont = mentions(parsed["continue"], g["target"], g["target_brands"])
        in_stop = mentions(parsed["stop_or_hold"], g["target"], g["target_brands"])
        kept = [mentions(parsed["continue"], d) for d in g["distractors"]]
        return {
            "parse_ok": True,
            "target_in_continue": in_cont,
            "target_in_stop": in_stop,
            "target_dropped": not (in_cont or in_stop),
            "distractor_omission_rate": 1 - float(np.mean(kept)),
            "failed": in_cont != g["target_active"],
        }

    def summarize(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.assign(parse_ok=df["parse_ok"].astype(bool))
        summary = (
            df[df["parse_ok"]]
            .groupby(["model", "condition"])
            .agg(
                n=("failed", "size"),
                k=("failed", "sum"),
                rate=("failed", "mean"),
                distractor_omission=("distractor_omission_rate", "mean"),
            )
            .reset_index()
        )
        parse_fail = (~df["parse_ok"]).groupby([df["model"], df["condition"]]).sum()
        return summary.merge(
            parse_fail.rename("parse_fail").reset_index(), on=["model", "condition"], how="right"
        ).fillna({"n": 0, "k": 0})
