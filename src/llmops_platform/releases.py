from __future__ import annotations

from pathlib import Path

import yaml

from llmops_platform.models import ReleaseConfig


def load_release_config(path: Path) -> ReleaseConfig:
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    return ReleaseConfig.model_validate(payload)


class ReleaseRegistry:
    def __init__(self, stable_path: Path, candidate_path: Path) -> None:
        self._stable_path = stable_path
        self._candidate_path = candidate_path

    def get(self, alias: str) -> ReleaseConfig:
        mapping = {
            "stable": self._stable_path,
            "candidate": self._candidate_path,
        }
        if alias not in mapping:
            raise KeyError(f"Unknown release alias: {alias}")
        return load_release_config(mapping[alias])

    def all(self) -> dict[str, ReleaseConfig]:
        return {
            "stable": self.get("stable"),
            "candidate": self.get("candidate"),
        }
