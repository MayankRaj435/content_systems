import json

import pytest

from rag_lesson_agent import FallbackGenerator, GeminiGenerator, LessonAgent
from rag_lesson_agent.generator import GenerationError
from rag_lesson_agent.evaluator import RubricEvaluator
from rag_lesson_agent.memory import MemoryStore


def test_agent_retries_and_returns_passing_lesson(tmp_path):
    result = LessonAgent(memory=MemoryStore(tmp_path / "memory.jsonl")).run("Introduction to RAG")

    assert result.evaluation.passed
    assert result.attempts == 2
    assert len(result.rejections) == 1
    assert "concrete" in result.rejections[0].reasons[0].lower()


def test_memory_persists_feedback(tmp_path):
    path = tmp_path / "memory.jsonl"
    LessonAgent(memory=MemoryStore(path)).run("Introduction to RAG")

    entries = MemoryStore(path).recent()
    assert len(entries) == 1
    assert entries[0]["passed"] is True
    assert entries[0]["rejections"]


def test_blank_topic_is_rejected(tmp_path):
    with pytest.raises(ValueError):
        LessonAgent(memory=MemoryStore(tmp_path / "memory.jsonl")).run(" ")


def test_rubric_is_hard_pass_fail():
    evaluation = RubricEvaluator().evaluate("RAG is search. Summary.", "RAG")
    assert not evaluation.passed
    assert any(not check.passed for check in evaluation.checks)


def test_gemini_generator_uses_prompt_and_returns_text():
    class FakeResponse:
        text = "Generated lesson"

    class FakeModels:
        def generate_content(self, **kwargs):
            assert kwargs["model"] == "test-model"
            assert "Introduction to RAG" in kwargs["contents"]
            assert "Add an example" in kwargs["contents"]
            return FakeResponse()

    class FakeClient:
        models = FakeModels()

    generator = GeminiGenerator(model="test-model", client=FakeClient())
    assert generator.generate("Introduction to RAG", ["Add an example"], []) == (
        "Generated lesson"
    )


def test_provider_failure_falls_back_and_records_error(tmp_path):
    class BrokenGenerator:
        provider = "gemini"
        model = "test-model"

        def generate(self, topic, feedback, memory):
            raise GenerationError("temporary Gemini outage")

    generator = FallbackGenerator(BrokenGenerator())
    result = LessonAgent(
        generator=generator,
        memory=MemoryStore(tmp_path / "memory.jsonl"),
    ).run("Introduction to RAG")

    assert result.evaluation.passed
    assert result.provider == "gemini+offline"
    assert result.provider_errors == ["temporary Gemini outage"]
