from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class CheckResult:
    name: str
    passed: bool
    reason: str


@dataclass
class Evaluation:
    passed: bool
    checks: list[CheckResult]

    @property
    def failures(self) -> list[CheckResult]:
        return [check for check in self.checks if not check.passed]

    def to_dict(self) -> dict[str, Any]:
        return {"passed": self.passed, "checks": [asdict(check) for check in self.checks]}


@dataclass
class Rejection:
    attempt: int
    reasons: list[str]
    changes_requested: list[str]


@dataclass
class RunResult:
    topic: str
    lesson: str
    evaluation: Evaluation
    attempts: int
    rejections: list[Rejection] = field(default_factory=list)
    provider: str = "offline"
    model: str | None = None
    provider_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "topic": self.topic,
            "lesson": self.lesson,
            "evaluation": self.evaluation.to_dict(),
            "attempts": self.attempts,
            "rejections": [asdict(item) for item in self.rejections],
            "provider": self.provider,
            "model": self.model,
            "provider_errors": self.provider_errors,
        }
