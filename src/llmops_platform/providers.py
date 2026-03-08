from __future__ import annotations

from abc import ABC, abstractmethod

from llmops_platform.models import IncidentContext, ReleaseConfig


class BaseResponder(ABC):
    @abstractmethod
    async def generate(
        self,
        question: str,
        context: IncidentContext,
        evidence: list[str],
        risk_flags: list[str],
        release: ReleaseConfig,
    ) -> str:
        raise NotImplementedError


class MockResponder(BaseResponder):
    async def generate(
        self,
        question: str,
        context: IncidentContext,
        evidence: list[str],
        risk_flags: list[str],
        release: ReleaseConfig,
    ) -> str:
        root_cause = "downstream service instability"
        next_action = "validate logs and contain impact"
        evidence_focus = context.summary

        joined_logs = " ".join(context.logs).lower()
        joined_changes = " ".join(context.recent_changes).lower()

        if "deploy" in joined_changes or "release" in joined_changes:
            root_cause = "a recent deployment likely introduced latency or dependency pressure"
            next_action = "rollback the recent deployment and confirm recovery"
            evidence_focus = "recent deployment, elevated latency, and timeout errors"
        elif "feature flag" in joined_changes or "flag" in joined_changes:
            root_cause = "a newly enabled feature flag is likely triggering upstream failures"
            next_action = "disable the feature flag and verify 5xx recovery"
            evidence_focus = "feature flag rollout and 503 errors from the promo engine"
        elif "database" in joined_logs or "connection" in joined_logs:
            root_cause = "database connection pool exhaustion is blocking workers"
            next_action = "reduce worker pressure, reset batch size, and restore DB headroom"
            evidence_focus = "database connection pool exhaustion and increased batch size"
        elif context.metrics.get("cpu_utilization", 0) > 90:
            root_cause = "CPU saturation is causing timeouts and elevated latency"
            next_action = "shift traffic away or rollback while investigating hot paths"
            evidence_focus = "cpu utilization above 90 percent with timeout errors"

        evidence_lines = evidence[:4] if evidence else [context.summary]
        flags_line = ", ".join(risk_flags) if risk_flags else "No major risk flags detected"
        evidence_block = " | ".join(evidence_lines)

        return (
            f"Question: {question}\n"
            f"Probable root cause: {root_cause}.\n"
            f"Immediate action: {next_action}.\n"
            f"Primary evidence: {evidence_focus}.\n"
            f"Evidence used: {evidence_block}.\n"
            f"Risk flags: {flags_line}.\n"
            f"Release policy: {release.tool_policy}."
        )


class OpenAIResponder(BaseResponder):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    async def generate(
        self,
        question: str,
        context: IncidentContext,
        evidence: list[str],
        risk_flags: list[str],
        release: ReleaseConfig,
    ) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(api_key=self._api_key, model=release.model, temperature=0)
        prompt = "\n".join(
            [
                f"Question: {question}",
                f"Service: {context.service}",
                f"Severity: {context.severity}",
                f"Summary: {context.summary}",
                f"Evidence: {' | '.join(evidence)}",
                f"Risk flags: {' | '.join(risk_flags) if risk_flags else 'none'}",
                "Respond with probable root cause, immediate action, and next validation.",
            ]
        )
        response = await llm.ainvoke(
            [SystemMessage(content=release.system_prompt), HumanMessage(content=prompt)]
        )
        return str(response.content)


def build_responder(release: ReleaseConfig, api_key: str | None) -> BaseResponder:
    if release.provider == "openai" and api_key:
        return OpenAIResponder(api_key=api_key)
    return MockResponder()
