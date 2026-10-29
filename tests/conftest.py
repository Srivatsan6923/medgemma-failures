import json

import pytest

from clinfail.models.llm import Completion, LLMClient


@pytest.fixture
def fake_backend(monkeypatch):
    """Replace the API call with a model that always answers "A"; returns the sent requests."""
    sent = []

    def call(self, req):
        sent.append(req)
        return Completion(text="A", finish_reason="stop")

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setattr(LLMClient, "_call", call)
    return sent


@pytest.fixture
def mcq_dir(tmp_path, monkeypatch):
    """A working directory with a tiny MedQA cache: five diagnosis items and one other item."""
    items = [
        {
            "item_id": f"medqa-{i}",
            "source": "medqa",
            "question": f"A {30 + i}-year-old man has joint pain. His nails are pitted. "
            "Which of the following is the most likely diagnosis?",
            "options": {"A": "Psoriatic arthritis", "B": "Gout", "C": "Lupus", "D": "Lyme disease"},
            "answer": "A",
            "subject": "",
        }
        for i in range(5)
    ]
    items.append(
        {
            "item_id": "medqa-x",
            "source": "medqa",
            "question": "Which drug is first line?",
            "options": dict.fromkeys("ABCD", "x"),
            "answer": "B",
            "subject": "",
        }
    )
    (tmp_path / "data" / "processed").mkdir(parents=True)
    (tmp_path / "data" / "processed" / "medqa_train_v1.jsonl").write_text(
        "".join(json.dumps(x) + "\n" for x in items)
    )
    monkeypatch.chdir(tmp_path)
    return tmp_path
