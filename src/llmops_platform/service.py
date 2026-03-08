from __future__ import annotations

from time import perf_counter
from uuid import uuid4

from llmops_platform.graph import build_investigation_graph
from llmops_platform.metrics import TelemetrySink, estimate_cost, estimate_tokens
from llmops_platform.models import FeedbackRecord, InvestigationRequest, InvestigationResponse
from llmops_platform.providers import build_responder
from llmops_platform.releases import ReleaseRegistry
from llmops_platform.routing import CanaryRouter
from llmops_platform.settings import AppSettings


class LLMOpsService:
    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        self.registry = ReleaseRegistry(
            stable_path=settings.stable_release_path,
            candidate_path=settings.candidate_release_path,
        )
        self.router = CanaryRouter(candidate_weight=settings.candidate_weight)
        self.telemetry = TelemetrySink(output_path=settings.metrics_output_path)

    async def respond(
        self,
        payload: InvestigationRequest | dict[str, object],
        preferred_release: str | None = None,
        request_id: str | None = None,
        emit_telemetry: bool = True,
    ) -> InvestigationResponse:
        request = (
            payload
            if isinstance(payload, InvestigationRequest)
            else InvestigationRequest.model_validate(payload)
        )
        resolved_request_id = request_id or request.request_id or str(uuid4())
        release_alias = self.router.choose_release(
            request_id=resolved_request_id,
            preferred_release=preferred_release or request.preferred_release,
        )
        release = self.registry.get(release_alias)
        responder = build_responder(release=release, api_key=self.settings.openai_api_key)
        graph = build_investigation_graph(responder)

        started = perf_counter()
        result = await graph.ainvoke(
            {
                "question": request.question,
                "context": request.context.model_dump(),
                "release": release.model_dump(),
            }
        )
        latency_ms = round((perf_counter() - started) * 1000, 2)
        answer = result["answer"]
        estimated_tokens = estimate_tokens(answer)
        estimated_cost = estimate_cost(estimated_tokens, release.model)

        response = InvestigationResponse(
            request_id=resolved_request_id,
            release_name=release.name,
            release_version=release.version,
            answer=answer,
            evidence=result.get("evidence", []),
            risk_flags=result.get("risk_flags", []),
            latency_ms=latency_ms,
            estimated_tokens=estimated_tokens,
            estimated_cost_usd=estimated_cost,
        )

        if emit_telemetry:
            self.telemetry.record("inference", response.model_dump())
        return response

    def list_releases(self) -> dict[str, dict[str, object]]:
        return {
            alias: release.model_dump()
            for alias, release in self.registry.all().items()
        }

    def record_feedback(self, payload: FeedbackRecord | dict[str, object]) -> FeedbackRecord:
        feedback = (
            payload if isinstance(payload, FeedbackRecord) else FeedbackRecord.model_validate(payload)
        )
        self.telemetry.record("feedback", feedback.model_dump())
        return feedback
