from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from llmops_platform.models import IncidentContext, ReleaseConfig
from llmops_platform.providers import BaseResponder


class InvestigationState(TypedDict, total=False):
    question: str
    context: dict[str, object]
    release: dict[str, object]
    evidence: list[str]
    risk_flags: list[str]
    answer: str


def build_investigation_graph(responder: BaseResponder):
    workflow = StateGraph(InvestigationState)

    def collect_evidence(state: InvestigationState) -> InvestigationState:
        context = IncidentContext.model_validate(state["context"])
        evidence = [
            f"Service {context.service} is in {context.severity} severity.",
            f"Summary: {context.summary}",
        ]
        if context.recent_changes:
            evidence.append(f"Recent changes: {', '.join(context.recent_changes)}")
        if context.logs:
            evidence.append(f"Logs: {' | '.join(context.logs)}")
        if context.metrics:
            metrics_line = ", ".join(f"{key}={value}" for key, value in context.metrics.items())
            evidence.append(f"Metrics: {metrics_line}")
        if context.runbook_excerpt:
            evidence.append(f"Runbook: {context.runbook_excerpt}")
        return {"evidence": evidence}

    def assess_risk(state: InvestigationState) -> InvestigationState:
        context = IncidentContext.model_validate(state["context"])
        risk_flags: list[str] = []
        if context.severity in {"high", "critical"}:
            risk_flags.append("high-severity incident")
        if any("deploy" in change.lower() for change in context.recent_changes):
            risk_flags.append("recent deployment detected")
        if any("flag" in change.lower() for change in context.recent_changes):
            risk_flags.append("feature flag rollout detected")
        if context.metrics.get("cpu_utilization", 0) >= 90:
            risk_flags.append("cpu saturation")
        if any("timeout" in log.lower() or "503" in log.lower() for log in context.logs):
            risk_flags.append("user-facing failure pattern in logs")
        return {"risk_flags": risk_flags}

    async def generate_answer(state: InvestigationState) -> InvestigationState:
        context = IncidentContext.model_validate(state["context"])
        release = ReleaseConfig.model_validate(state["release"])
        answer = await responder.generate(
            question=state["question"],
            context=context,
            evidence=state.get("evidence", []),
            risk_flags=state.get("risk_flags", []),
            release=release,
        )
        return {"answer": answer}

    workflow.add_node("collect_evidence", collect_evidence)
    workflow.add_node("assess_risk", assess_risk)
    workflow.add_node("generate_answer", generate_answer)
    workflow.add_edge(START, "collect_evidence")
    workflow.add_edge("collect_evidence", "assess_risk")
    workflow.add_edge("assess_risk", "generate_answer")
    workflow.add_edge("generate_answer", END)

    return workflow.compile()
