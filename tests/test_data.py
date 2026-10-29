from clinfail.data.asclepius import extract_section, is_usable
from clinfail.data.mcq import normalize_medqa


def test_normalize_medqa():
    rows = [
        {
            "question": " Q? ",
            "options": dict.fromkeys("ABCD", "x"),
            "answer_idx": "C",
            "meta_info": "step1",
        }
    ]
    (x,) = normalize_medqa(rows)
    assert (x["item_id"], x["question"], x["answer"]) == ("medqa-0", "Q?", "C")


def test_extract_hospital_course():
    note = (
        "Admission Diagnosis:\nflu\n\nHospital Course:\nThe patient improved.\nMore text.\n\n"
        "Discharge Instructions:\nrest"
    )
    assert extract_section(note, "Hospital Course") == "The patient improved.\nMore text."


def test_is_usable_rejects_drug_words_and_short_text():
    text = " ".join(["word"] * 100)
    assert is_usable(text, 80, ["warfarin"])
    assert not is_usable(text + " Warfarin was held.", 80, ["warfarin"])
    assert not is_usable("too short", 80, [])
    assert not is_usable(text + " [redacted]", 80, [])
