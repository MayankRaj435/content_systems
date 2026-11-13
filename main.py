from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from rag_lesson_agent import (
    FallbackGenerator,
    GeminiGenerator,
    LessonAgent,
    TemplateGenerator,
)
from rag_lesson_agent.memory import MemoryStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and self-evaluate a beginner lesson.")
    parser.add_argument("topic", nargs="?", default="Introduction to RAG")
    parser.add_argument("--memory", default="data/memory.jsonl")
    parser.add_argument("--output", default="outputs/latest_run.json")
    parser.add_argument(
        "--provider",
        choices=("offline", "gemini"),
        default=os.getenv("LESSON_PROVIDER", "offline"),
    )
    args = parser.parse_args()

    generator = (
        FallbackGenerator(GeminiGenerator())
        if args.provider == "gemini"
        else TemplateGenerator()
    )
    result = LessonAgent(
        generator=generator,
        memory=MemoryStore(args.memory),
    ).run(args.topic)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Status: {'PASS' if result.evaluation.passed else 'FAIL'}")
    print(f"Attempts: {result.attempts}")
    print(f"Rejections: {len(result.rejections)}")
    print(f"Saved: {output}")
    print("\n" + result.lesson)


if __name__ == "__main__":
    main()
