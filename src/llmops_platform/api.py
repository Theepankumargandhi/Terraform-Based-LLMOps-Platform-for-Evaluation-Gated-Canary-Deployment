from __future__ import annotations

from fastapi import FastAPI

from llmops_platform.models import FeedbackRecord, InvestigationRequest
from llmops_platform.service import LLMOpsService
from llmops_platform.settings import load_settings


def create_app() -> FastAPI:
    settings = load_settings()
    service = LLMOpsService(settings)
    app = FastAPI(title="LLMOps Canary Platform", version="0.1.0")

    @app.get("/healthz")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok", "environment": settings.environment}

    @app.get("/v1/releases")
    async def list_releases() -> dict[str, dict[str, object]]:
        return service.list_releases()

    @app.post("/v1/respond")
    async def respond(request: InvestigationRequest) -> dict[str, object]:
        response = await service.respond(request)
        return response.model_dump()

    @app.post("/v1/feedback")
    async def record_feedback(record: FeedbackRecord) -> dict[str, object]:
        feedback = service.record_feedback(record)
        return feedback.model_dump()

    return app
