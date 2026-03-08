from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EvaluationThresholds(BaseModel):
    min_keyword_recall: float = 0.7
    min_groundedness_proxy: float = 0.65
    max_average_latency_ms: float = 2500
    max_average_cost_usd: float = 0.05
    max_quality_regression: float = 0.05


class ReleaseConfig(BaseModel):
    name: str
    version: str
    provider: Literal["mock", "openai"] = "mock"
    model: str = "gpt-4o-mini"
    tool_policy: str = "read_only"
    canary_weight: int = Field(default=10, ge=0, le=100)
    system_prompt: str
    evaluation: EvaluationThresholds = Field(default_factory=EvaluationThresholds)


class IncidentContext(BaseModel):
    service: str
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    summary: str
    recent_changes: list[str] = Field(default_factory=list)
    logs: list[str] = Field(default_factory=list)
    metrics: dict[str, float] = Field(default_factory=dict)
    runbook_excerpt: str | None = None


class InvestigationRequest(BaseModel):
    question: str
    context: IncidentContext
    preferred_release: Literal["stable", "candidate"] | None = None
    request_id: str | None = None


class InvestigationResponse(BaseModel):
    request_id: str
    release_name: str
    release_version: str
    answer: str
    evidence: list[str]
    risk_flags: list[str]
    latency_ms: float
    estimated_tokens: int
    estimated_cost_usd: float


class FeedbackRecord(BaseModel):
    request_id: str
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class EvalExample(BaseModel):
    question: str
    context: IncidentContext
    expected_keywords: list[str]


class EvalCaseResult(BaseModel):
    request_id: str
    release_name: str
    keyword_recall: float
    groundedness_proxy: float
    latency_ms: float
    estimated_cost_usd: float
    passed: bool


class EvalSummary(BaseModel):
    release_name: str
    release_version: str
    average_keyword_recall: float
    average_groundedness_proxy: float
    average_latency_ms: float
    average_cost_usd: float
    passed: bool
    total_cases: int


class ReleaseComparisonReport(BaseModel):
    generated_at: str
    stable: EvalSummary
    candidate: EvalSummary
    quality_delta: float
    candidate_passed_gate: bool
    cases: list[EvalCaseResult]
