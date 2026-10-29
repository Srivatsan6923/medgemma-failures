import json

import numpy as np
import pytest

from clinfail.probes import PROBES
from clinfail.probes.med_status import CONDITIONS
from clinfail.probes.notes import DISTRACTORS, TARGETS, infer_sex, mentions, parse_reconciliation

COURSE = (
    "The patient was admitted with community-acquired pneumonia. Blood cultures were drawn. "
    "He was treated with intravenous fluids and supportive care. Oxygen was weaned to room air. "
    "Physical therapy evaluated him on day three. He was ambulating independently by discharge. "
    "Follow-up chest imaging was arranged with his primary care physician in two weeks."
)


@pytest.fixture
def probe(tmp_path):
    cache = tmp_path / "courses.jsonl"
    cache.write_text(
        "".join(json.dumps({"patient_id": str(i), "text": COURSE}) + "\n" for i in range(10))
    )
    return PROBES["med_status"]({"cache_path": str(cache)})


def note(case):
    return case.messages[-1][1]


def test_every_condition_per_pair(probe):
    cases = probe.build_cases(4, np.random.default_rng(0))
    assert len(cases) == 4 * len(CONDITIONS)
    for pid in {c.pair_id for c in cases}:
        assert {c.condition for c in cases if c.pair_id == pid} == set(CONDITIONS)


def test_pairs_differ_only_by_the_cue(probe):
    cases = probe.build_cases(3, np.random.default_rng(1))
    for pid in {c.pair_id for c in cases}:
        group = {c.condition: c for c in cases if c.pair_id == pid}
        silent = set(note(group["active_silent"]).split(". "))
        for cond in ("stop_narrative", "held_narrative", "active_mentioned"):
            assert 1 <= len(set(note(group[cond]).split(". ")) - silent) <= 2


def test_cue_placement(probe):
    for c in probe.build_cases(5, np.random.default_rng(2)):
        if c.condition == "stopclass_narrative":
            assert f"{c.gold['target'].capitalize()} was" not in note(c)
            assert c.meta["target_class"] in note(c)
        if c.condition == "stop_adjacent":
            assert "Medication changes:" in note(c)
            assert c.meta["cue_distance_words"] == 0
        if c.condition == "stop_narrative":
            assert c.meta["cue_distance_words"] > 0


def test_distractors_never_share_target_class(probe):
    cls = {d.name: d.drug_class for d in (*TARGETS, *DISTRACTORS)}
    for c in probe.build_cases(10, np.random.default_rng(3)):
        assert all(cls[d] != cls[c.gold["target"]] for d in c.gold["distractors"])


def test_parse_reconciliation():
    out = '```json\n{"continue": ["Lisinopril 10 mg"], "stop_or_hold": [], "new": []}\n```'
    assert parse_reconciliation(out) == {
        "continue": ["lisinopril 10 mg"],
        "stop_or_hold": [],
        "new": [],
    }
    assert parse_reconciliation("no json here") is None
    assert parse_reconciliation('{"continue": "lisinopril"}') is None


def test_mentions():
    assert mentions(["zestril 10mg"], "lisinopril", ("zestril",))
    assert not mentions(["metformin er"], "metoprolol")


def score(probe, case, cont, stop=()):
    return probe.score(
        case, json.dumps({"continue": list(cont), "stop_or_hold": list(stop), "new": []})
    )


def test_score_leakage_and_omission(probe):
    c = {x.condition: x for x in probe.build_cases(1, np.random.default_rng(4))}
    tgt, dis = c["stop_narrative"].gold["target"], c["stop_narrative"].gold["distractors"]
    assert score(probe, c["stop_narrative"], [*dis, tgt])["failed"]
    assert not score(probe, c["stop_narrative"], dis, [tgt])["failed"]
    assert score(probe, c["active_silent"], dis)["failed"]
    r = score(probe, c["active_silent"], [tgt])
    assert not r["failed"]
    assert r["distractor_omission_rate"] == 1.0
    assert probe.score(c["active_silent"], "I cannot help with that.")["parse_ok"] is False


def test_infer_sex():
    assert infer_sex("He was admitted. His pain improved.") == "male"
    assert infer_sex("She was admitted with her daughter.") == "female"
    assert infer_sex("The patient was admitted.") is None
