from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any

from .evaluator import RubricEvaluator
from .generator import LessonGenerator, TemplateGenerator
from .memory import MemoryStore
from .models import Rejection, RunResult


class LessonAgent:
    def __init__(
        self,
        generator: LessonGenerator | None = None,
        evaluator: RubricEvaluator | None = None,
        memory: MemoryStore | None = None,
        max_retries: int = 2,
    ) -> None:
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        self.generator = generator or TemplateGenerator()
        self.evaluator = evaluator or RubricEvaluator()
        self.memory = memory or MemoryStore()
        self.max_retries = max_retries

    def run(self, topic: str) -> RunResult:
        topic = topic.strip()
        if not topic:
            raise ValueError("topic must not be empty")
        rejections: list[Rejection] = []
        feedback: list[str] = []
        lesson = ""
        evaluation = None

        for attempt in range(self.max_retries + 1):
            lesson = self.generator.generate(topic, feedback, self.memory.recent())
            evaluation = self.evaluator.evaluate(lesson, topic)
            if evaluation.passed:
                result = RunResult(topic, lesson, evaluation, attempt + 1, rejections)
                self._remember(result)
                return result
            if attempt < self.max_retries:
                feedback = [check.reason for check in evaluation.failures]
                rejections.append(
                    Rejection(
                        attempt=attempt + 1,
                        reasons=feedback,
                        changes_requested=feedback.copy(),
                    )
                )

        assert evaluation is not None
        result = RunResult(topic, lesson, evaluation, self.max_retries + 1, rejections)
        self._remember(result)
        return result

    def _remember(self, result: RunResult) -> None:
        self.memory.record(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "topic": result.topic,
                "attempts": result.attempts,
                "passed": result.evaluation.passed,
                "failures": [
                    reason
                    for rejection in result.rejections
                    for reason in rejection.reasons
                ] or [check.reason for check in result.evaluation.failures],
                "rejections": [asdict(item) for item in result.rejections],
            }
        )
