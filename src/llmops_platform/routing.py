from __future__ import annotations

import hashlib


class CanaryRouter:
    def __init__(self, candidate_weight: int) -> None:
        self._candidate_weight = max(0, min(candidate_weight, 100))

    def choose_release(
        self, request_id: str, preferred_release: str | None = None
    ) -> str:
        if preferred_release in {"stable", "candidate"}:
            return preferred_release

        bucket = int(hashlib.sha256(request_id.encode("utf-8")).hexdigest()[:8], 16) % 100
        return "candidate" if bucket < self._candidate_weight else "stable"
