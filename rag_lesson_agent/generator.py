from __future__ import annotations

from typing import Protocol


class LessonGenerator(Protocol):
    def generate(self, topic: str, feedback: list[str], memory: list[dict]) -> str:
        ...


class TemplateGenerator:
    """Offline generator used by the demo and tests.

    The first draft intentionally lacks a concrete example. This makes the
    retry loop visible without requiring an API key or a flaky network call.
    """

    def generate(self, topic: str, feedback: list[str], memory: list[dict]) -> str:
        learned_from_memory = any(entry.get("failures") for entry in memory[-3:])
        if not feedback and not learned_from_memory:
            return self._draft(topic, include_example=False)
        return self._draft(topic, include_example=True)

    @staticmethod
    def _draft(topic: str, include_example: bool) -> str:
        example = (
            "\n### A simple example\n"
            'Suppose you ask, "What is our refund policy?" The system first '
            "retrieves the policy page, then gives that text to the language model. "
            'The answer can say, "Refunds are allowed within 30 days," and point '
            "back to the retrieved page.\n"
            if include_example
            else ""
        )
        return f"""# {topic}: a beginner lesson

## What it is
Retrieval-Augmented Generation (RAG) is a way to make an AI answer using
relevant information retrieved from a trusted collection. It combines search
with generation. The language model writes the answer, but the retrieved
documents provide the facts.

## Why it matters
A model may not know your private documents, and it may confidently make up
an answer. RAG lets a system use newer or organisation-specific information.
It can also show the source text so a person can check the answer. RAG does
not make every answer true: poor documents or poor search can still lead to
an incorrect answer.

## How it works
1. **Ask:** the learner sends a question.
2. **Retrieve:** a search system finds the most relevant chunks of documents.
3. **Augment:** the question and those chunks are placed together in a prompt.
4. **Generate:** the language model writes an answer based on that context.
5. **Check:** the application can show sources and ask a person to verify
   important answers.

{example}
## Important words
- **Document:** a source such as a webpage, PDF, or database record.
- **Chunk:** a smaller piece of a document used for search.
- **Embedding:** a list of numbers that represents meaning, so similar text
  can be found even when it uses different words.
- **Context:** the retrieved text given to the model.

## A useful mental model
RAG is like an open-book exam: search finds the right pages, and the model
uses those pages to write a clear answer. It is not the same as teaching the
model new permanent knowledge (fine-tuning).

## Summary
RAG retrieves relevant information, adds it to a prompt, and generates an
answer grounded in that information. It is useful when answers need private,
fresh, or checkable facts.
"""
