import numpy as np

from clinfail.probes import PROBES
from clinfail.probes.anchoring import NEUTRAL, insert_before_question, parse_letter

VIGNETTE = (
    "A 30-year-old man has joint pain. His nails are pitted. "
    "Which of the following is the most likely diagnosis?"
)


def test_insert_before_question():
    out = insert_before_question(VIGNETTE, "LINE.")
    assert out.endswith("LINE. Which of the following is the most likely diagnosis?")
    assert out.startswith("A 30-year-old man has joint pain.")


def test_parse_letter():
    assert parse_letter("B") == "B"
    assert parse_letter("**C.** Lupus") == "C"
    assert parse_letter("The answer is D") == "D"
    assert parse_letter("A 45-year-old patient most likely has lupus, so the answer is C") == "C"
    assert parse_letter("I am not sure") is None


def test_parse_letter_skips_medgemma_thinking():
    assert parse_letter("<unused94>thought\nOption A looks wrong, B fits.<unused95>B") == "B"
    # reasoning that never closes was cut off by max_tokens
    assert parse_letter("<unused94>thought\nThe answer is A because") is None


def test_parse_letter_reads_boxed_final_answer():
    out = r"<unused94>thought\n...<unused95>Rationale: A 30-year-old man ...\n\nFinal Answer: The final answer is $\boxed{B}$"
    assert parse_letter(out) == "B"


def test_cases_and_scoring(mcq_dir):
    probe = PROBES["anchoring"]({})
    cases = probe.build_cases(10, np.random.default_rng(0))
    assert len(cases) == 5 * 4  # the non-diagnosis item is skipped
    by = {c.condition: c for c in cases if c.pair_id == cases[0].pair_id}
    wrong = by["wrong_anchor"].gold["anchor"]
    assert wrong != "A"
    assert NEUTRAL in by["neutral"].messages[-1][1]
    assert "Psoriatic arthritis." in by["right_anchor"].messages[-1][1]
    assert probe.score(by["wrong_anchor"], wrong)["chose_anchor"]
    assert not probe.score(by["baseline"], "A")["failed"]
    assert probe.score(by["baseline"], "unsure")["parse_ok"] is False
