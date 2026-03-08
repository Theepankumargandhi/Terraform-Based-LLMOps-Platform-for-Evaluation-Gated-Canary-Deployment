from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(slots=True)
class AppSettings:
    app_name: str = "llmops-canary-platform"
    environment: str = "local"
    app_port: int = 8080
    stable_release_path: Path = Path("configs/releases/stable.yaml")
    candidate_release_path: Path = Path("configs/releases/candidate.yaml")
    candidate_weight: int = 10
    metrics_output_path: Path = Path("artifacts/runtime/events.jsonl")
    openai_api_key: str | None = None
    langsmith_api_key: str | None = None


def load_settings(**overrides: object) -> AppSettings:
    settings = AppSettings(
        app_name=os.getenv("APP_NAME", "llmops-canary-platform"),
        environment=os.getenv("ENVIRONMENT", "local"),
        app_port=int(os.getenv("APP_PORT", "8080")),
        stable_release_path=Path(
            os.getenv("STABLE_RELEASE_PATH", "configs/releases/stable.yaml")
        ),
        candidate_release_path=Path(
            os.getenv("CANDIDATE_RELEASE_PATH", "configs/releases/candidate.yaml")
        ),
        candidate_weight=int(os.getenv("CANDIDATE_WEIGHT", "10")),
        metrics_output_path=Path(
            os.getenv("METRICS_OUTPUT_PATH", "artifacts/runtime/events.jsonl")
        ),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        langsmith_api_key=os.getenv("LANGSMITH_API_KEY"),
    )
    return AppSettings(**(asdict(settings) | overrides))
