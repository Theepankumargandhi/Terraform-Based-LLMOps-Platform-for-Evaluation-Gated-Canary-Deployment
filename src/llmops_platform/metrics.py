from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


MODEL_PRICING = {
    "gpt-4o-mini": 0.0000006,
    "gpt-4.1-mini": 0.0000008,
}


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def estimate_cost(tokens: int, model: str) -> float:
    return round(tokens * MODEL_PRICING.get(model, 0.0000006), 6)


def compute_keyword_recall(text: str, expected_keywords: list[str]) -> float:
    lowered = text.lower()
    hits = sum(1 for keyword in expected_keywords if keyword.lower() in lowered)
    return round(hits / max(1, len(expected_keywords)), 4)


def compute_groundedness_proxy(text: str, evidence: list[str]) -> float:
    evidence_tokens = {
        token.strip(".,:;()").lower()
        for item in evidence
        for token in item.split()
        if len(token) > 3
    }
    if not evidence_tokens:
        return 0.0

    answer_tokens = {
        token.strip(".,:;()").lower() for token in text.split() if len(token) > 3
    }
    overlap = len(evidence_tokens & answer_tokens)
    return round(min(1.0, overlap / max(1, len(answer_tokens))), 4)


@dataclass(slots=True)
class TelemetrySink:
    output_path: Path

    def record(self, event_type: str, payload: dict[str, object]) -> None:
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps({"event_type": event_type, "payload": payload}, default=str)
                + "\n"
            )
