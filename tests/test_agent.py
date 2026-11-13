import json

import pytest

from rag_lesson_agent import LessonAgent
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
