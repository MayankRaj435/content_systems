from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class MemoryStore:
    """Small JSONL memory store; easy to inspect, back up, and replace with a DB."""

    def __init__(self, path: str | Path = "data/memory.jsonl") -> None:
        self.path = Path(path)

    def record(self, item: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(item, ensure_ascii=False) + "\n")

    def recent(self, limit: int = 10) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines[-limit:] if line.strip()]
