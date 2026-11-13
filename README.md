# Self-Evaluating RAG Lesson Generator

This project is a small agentic content system for the take-home assessment. It
does not stop after the first plausible answer:

1. **Generate** a standalone beginner lesson.
2. **Evaluate** it against seven hard pass/fail rubric checkpoints.
3. **Regenerate** using the failed-check feedback (maximum two retries).
4. **Remember** the run, failures, and changes in an inspectable JSONL file.

The default generator is deterministic and offline. Its first draft intentionally
misses the concrete-example checkpoint, so the demo proves that the loop actually
rejects and improves content. A production adapter can implement the
`LessonGenerator` protocol and call an approved LLM without changing the engine
or evaluator.

## Run

Requires Python 3.10+.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python main.py "Introduction to RAG"
pytest -q
```

The run writes:

- `outputs/latest_run.json`: passing lesson, every check, attempts, and rejection log
- `data/memory.jsonl`: persistent run memory (ignored by git because it is runtime data)

## Rubric design

Every check is binary; one failure means the draft is rejected:

| Check | What must be present |
|---|---|
| Definition | What RAG is, in plain language |
| Why it matters | Fresh/private knowledge and source checking |
| Process | Retrieve → augment → generate |
| Concrete example | A question, retrieved information, and answer |
| Jargon | Chunk, embedding, and context explained |
| Accuracy boundary | RAG can still be wrong |
| Beginner flow | Standalone structure, summary, and sufficient teaching depth |

This is deliberately a lightweight evaluator. In production I would add a
second, independent model judge plus citation/claim checks, while keeping these
deterministic gates for repeatability.

## Self-evolving memory

Each run stores failed checkpoint reasons and requested changes. The next run
loads recent memory and passes it into the generator. The current offline
generator uses feedback to add the missing example; an LLM adapter can use the
same feedback to update prompt instructions or aggregate recurring failures.
Memory is JSONL rather than a database so a reviewer can inspect it line by
line and migrate it later.

## Architecture and trade-offs

- `LessonAgent` owns orchestration and the retry/termination invariant.
- `TemplateGenerator` is a no-key demo provider; the protocol is the model seam.
- `RubricEvaluator` is transparent and testable, avoiding a judge that can
  silently change its standard.
- `MemoryStore` persists feedback without introducing infrastructure.

The hard cap is `max_retries=2`; even a bad provider cannot create an infinite
loop. The system returns the final failed result with its rejection log if all
attempts fail, rather than pretending it passed.
