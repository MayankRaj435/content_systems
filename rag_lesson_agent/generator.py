from __future__ import annotations

import os
from typing import Protocol


class GenerationError(RuntimeError):
    """A provider failed to produce usable lesson text."""


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

    @property
    def provider(self) -> str:
        return "offline"

    @property
    def model(self) -> str | None:
        return None

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


class FallbackGenerator:
    def __init__(
        self,
        primary: LessonGenerator,
        fallback: LessonGenerator | None = None,
    ) -> None:
        self.primary = primary
        self.fallback = fallback or TemplateGenerator()
        self.errors: list[str] = []

    def generate(self, topic: str, feedback: list[str], memory: list[dict]) -> str:
        try:
            return self.primary.generate(topic, feedback, memory)
        except GenerationError as error:
            message = str(error)
            if message not in self.errors:
                self.errors.append(message)
            return self.fallback.generate(topic, feedback, memory)

    @property
    def provider(self) -> str:
        return f"{self.primary.provider}+{self.fallback.provider}"

    @property
    def model(self) -> str | None:
        return self.primary.model


class GeminiGenerator:
    """Gemini Developer API adapter using Google's current ``google-genai`` SDK."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        client: object | None = None,
    ) -> None:
        if client is None:
            try:
                from dotenv import load_dotenv
            except ImportError as error:
                raise RuntimeError(
                    "Gemini support requires the optional dependencies: "
                    "pip install -r requirements-gemini.txt"
                ) from error
            load_dotenv()
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        if client is not None:
            self.client = client
            return
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError(
                "GEMINI_API_KEY is required when using the Gemini provider"
            )
        try:
            from google import genai
        except ImportError as error:
            raise RuntimeError(
                "Gemini support requires the optional dependency: "
                "pip install -r requirements-gemini.txt"
            ) from error
        self.client = genai.Client(api_key=key)

    def generate(self, topic: str, feedback: list[str], memory: list[dict]) -> str:
        prompt = self._build_prompt(topic, feedback, memory)
        try:
            from google.genai import errors as genai_errors
        except ImportError as error:
            raise GenerationError(
                "Gemini support requires the optional dependency: "
                "pip install -r requirements-gemini.txt"
            ) from error
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
        except genai_errors.APIError as error:
            raise GenerationError(f"Gemini request failed: {error}") from error
        text = getattr(response, "text", None)
        if not isinstance(text, str) or not text.strip():
            raise GenerationError("Gemini returned an empty lesson")
        return text.strip()

    @property
    def provider(self) -> str:
        return "gemini"

    @staticmethod
    def _build_prompt(topic: str, feedback: list[str], memory: list[dict]) -> str:
        feedback_text = "\n".join(f"- {item}" for item in feedback) or "- None"
        memory_text = "\n".join(
            f"- Previous run: {entry.get('failures', [])}"
            for entry in memory[-3:]
        ) or "- No previous runs"
        return f"""You write a standalone beginner lesson for a learner who finished
12th grade in India and is new to AI. Use simple English and short sentences.

Topic: {topic}

The lesson must:
- define the topic and explain why it matters;
- explain the process step by step;
- teach at least one practical example;
- define every technical term before relying on it;
- explain limitations and avoid claiming unsupported facts;
- use headings and end with a short summary.

Fix every failure from the previous draft:
{feedback_text}

Relevant memory from earlier runs:
{memory_text}

Return only the lesson in Markdown. Do not mention this prompt, evaluation,
feedback, or memory."""
