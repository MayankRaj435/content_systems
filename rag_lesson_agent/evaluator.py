from __future__ import annotations

import re

from .models import CheckResult, Evaluation


class RubricEvaluator:
    """Hard pass/fail rubric: every checkpoint must pass before shipping."""

    def evaluate(self, lesson: str, topic: str) -> Evaluation:
        lower = lesson.lower()
        checks = [
            self._check(
                "definition",
                any(term in lower for term in ("retrieval-augmented generation", "rag is")),
                "Defines RAG in plain language.",
                "Add a plain-language definition of RAG.",
            ),
            self._check(
                "why_it_matters",
                all(term in lower for term in ("private", "newer", "source")),
                "Explains private/fresh knowledge and why sources help.",
                "Explain why RAG matters, including fresh or private information and sources.",
            ),
            self._check(
                "process",
                all(term in lower for term in ("retrieve", "augment", "generate")),
                "Explains the retrieve → augment → generate flow.",
                "Describe the retrieve, augment, and generate steps.",
            ),
            self._check(
                "concrete_example",
                any(term in lower for term in ("example", "suppose", "for instance")),
                "Uses a concrete question and answer example.",
                "Add a concrete beginner-friendly example.",
            ),
            self._check(
                "jargon",
                all(term in lower for term in ("chunk", "embedding", "context")),
                "Explains key terms instead of leaving them unexplained.",
                "Explain chunk, embedding, and context in simple words.",
            ),
            self._check(
                "accuracy_boundary",
                "not make every answer true" in lower
                or "not every answer true" in lower
                or "can still lead to an incorrect answer" in lower,
                "States a limitation so learners do not over-trust RAG.",
                "State that RAG can still be wrong when retrieval or documents are poor.",
            ),
            self._check(
                "beginner_flow",
                len(lesson.split()) >= 220 and "summary" in lower,
                "Has enough standalone teaching flow and a summary.",
                "Keep the lesson standalone, structured, and long enough for a beginner.",
            ),
        ]
        return Evaluation(passed=all(check.passed for check in checks), checks=checks)

    @staticmethod
    def _check(name: str, passed: bool, success: str, failure: str) -> CheckResult:
        return CheckResult(name=name, passed=passed, reason=success if passed else failure)
