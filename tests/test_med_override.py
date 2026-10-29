import json

import numpy as np
import pytest

from clinfail.probes import PROBES
from clinfail.probes.med_override import CONDITIONS, NEUTRAL, TRIGGERS

COURSE = (
    "The patient was admitted with community-acquired pneumonia. Blood cultures were drawn. "
    "He was treated with intravenous fluids and supportive care. Oxygen was weaned to room air. "
    "Physical therapy evaluated him on day three. He was ambulating independently by discharge. "
    "Follow-up chest imaging was arranged with his primary care physician in two weeks."
)
PREGNANT = COURSE.replace("community-acquired pneumonia", "pneumonia at 30 weeks of gestation")
CHILD = COURSE.replace("The patient was", "The 9-year-old patient was")
ADULT = COURSE.replace("The patient was", "The 67-year-old patient was")


def write_courses(path, rows):
    path.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return str(path)


@pytest.fixture
def probe(tmp_path):
    rows = [{"patient_id": str(i), "text": COURSE} for i in range(12)]
    rows += [{"patient_id": f"p{i}", "text": PREGNANT} for i in range(12)]
    rows += [{"patient_id": f"c{i}", "text": CHILD} for i in range(12)]
    rows += [{"patient_id": f"a{i}", "text": ADULT} for i in range(2)]
    return PROBES["med_override"]({"cache_path": write_courses(tmp_path / "c.jsonl", rows)})


def note(case):
    return case.messages[-1][1]


def reply(cont, stop=(), flags=()):
    return json.dumps(
        {"continue": list(cont), "stop_or_hold": list(stop), "new": [], "flags": list(flags)}
    )


def test_conditions_and_pregnancy_filter(probe):
    cases = probe.build_cases(12, np.random.default_rng(0))
    assert len(cases) == 12 * len(CONDITIONS)
    assert all("gestation" not in note(c) for c in cases)
    assert {c.meta["target"] for c in cases} == set(TRIGGERS)


def test_pairs_differ_only_in_inserted_sentences(probe):
    cases = probe.build_cases(3, np.random.default_rng(1))
    for pid in {c.pair_id for c in cases}:
        g = {c.condition: c for c in cases if c.pair_id == pid}
        target = g["trigger_silent"].gold["target"]
        assert TRIGGERS[target] in note(g["trigger_continued"])
        assert any(s in note(g["neutral_silent"]) for s in NEUTRAL)
        assert TRIGGERS[target] not in note(g["neutral_continue_at_discharge"])
        assert "should be continued at discharge" in note(g["trigger_continue_at_discharge"])
        assert "was continued" not in note(g["trigger_silent"])
        # header and medication list are identical across the versions of a note
        stripped = {c: note(x).replace(TRIGGERS[target], "") for c, x in g.items()}
        assert (
            stripped["trigger_silent"].split("Hospital Course:")[0]
            == stripped["neutral_silent"].split("Hospital Course:")[0]
        )


def test_score_override_flag_and_silent(probe):
    case = probe.build_cases(1, np.random.default_rng(2))[0]
    tgt = case.gold["target"]
    assert not probe.score(case, reply([tgt]))["failed"]
    silent = probe.score(case, reply([], [tgt]))
    assert silent["failed"] and silent["silent_override"]
    flagged = probe.score(case, reply([], [tgt], [f"review {tgt}: lab abnormality"]))
    assert flagged["failed"] and not flagged["silent_override"]
    assert probe.score(case, "not json")["parse_ok"] is False


def test_age_comes_from_narrative_and_children_are_excluded(probe):
    cases = probe.build_cases(14, np.random.default_rng(3))
    assert all("9-year-old" not in note(c) for c in cases)
    adult = [c for c in cases if "67-year-old patient" in note(c)]
    assert adult
    assert all("Patient: 67-year-old" in note(c) for c in adult)


def test_age_param_fixes_age_and_drops_stated_ages(tmp_path):
    rows = [{"patient_id": str(i), "text": COURSE} for i in range(12)]
    rows += [{"patient_id": f"a{i}", "text": ADULT} for i in range(12)]
    params = {
        "cache_path": write_courses(tmp_path / "c.jsonl", rows),
        "age": 85,
        "conditions": ["trigger_continued"],
    }
    cases = PROBES["med_override"](params).build_cases(12, np.random.default_rng(0))
    assert len(cases) == 12
    assert all("Patient: 85-year-old" in note(c) and "67-year-old" not in note(c) for c in cases)
