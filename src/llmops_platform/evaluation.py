from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

from llmops_platform.metrics import compute_groundedness_proxy, compute_keyword_recall
from llmops_platform.models import EvalCaseResult, EvalExample, EvalSummary, ReleaseComparisonReport
from llmops_platform.service import LLMOpsService


class ReleaseEvaluator:
    def __init__(self, service: LLMOpsService, dataset_path: Path) -> None:
        self._service = service
        self._dataset_path = dataset_path

    def load_dataset(self) -> list[EvalExample]:
        with self._dataset_path.open("r", encoding="utf-8") as handle:
            return [EvalExample.model_validate(json.loads(line)) for line in handle if line.strip()]

    async def evaluate_release(self, release_alias: str) -> tuple[EvalSummary, list[EvalCaseResult]]:
        release = self._service.registry.get(release_alias)
        thresholds = release.evaluation
        dataset = self.load_dataset()

        case_results: list[EvalCaseResult] = []
        for index, example in enumerate(dataset):
            response = await self._service.respond(
                example.model_dump(),
                preferred_release=release_alias,
                request_id=f"{release_alias}-{index}",
                emit_telemetry=False,
            )
            recall = compute_keyword_recall(response.answer, example.expected_keywords)
            groundedness = compute_groundedness_proxy(response.answer, response.evidence)
            passed = (
                recall >= thresholds.min_keyword_recall
                and groundedness >= thresholds.min_groundedness_proxy
                and response.latency_ms <= thresholds.max_average_latency_ms
                and response.estimated_cost_usd <= thresholds.max_average_cost_usd
            )
            case_results.append(
                EvalCaseResult(
                    request_id=response.request_id,
                    release_name=response.release_name,
                    keyword_recall=recall,
                    groundedness_proxy=groundedness,
                    latency_ms=response.latency_ms,
                    estimated_cost_usd=response.estimated_cost_usd,
                    passed=passed,
                )
            )

        total_cases = len(case_results)
        summary = EvalSummary(
            release_name=release.name,
            release_version=release.version,
            average_keyword_recall=round(
                sum(case.keyword_recall for case in case_results) / max(1, total_cases), 4
            ),
            average_groundedness_proxy=round(
                sum(case.groundedness_proxy for case in case_results) / max(1, total_cases), 4
            ),
            average_latency_ms=round(
                sum(case.latency_ms for case in case_results) / max(1, total_cases), 2
            ),
            average_cost_usd=round(
                sum(case.estimated_cost_usd for case in case_results) / max(1, total_cases), 6
            ),
            passed=all(case.passed for case in case_results),
            total_cases=total_cases,
        )
        return summary, case_results

    async def compare(self) -> ReleaseComparisonReport:
        stable_summary, _ = await self.evaluate_release("stable")
        candidate_summary, candidate_cases = await self.evaluate_release("candidate")

        quality_delta = round(
            stable_summary.average_keyword_recall - candidate_summary.average_keyword_recall, 4
        )
        candidate_thresholds = self._service.registry.get("candidate").evaluation
        candidate_passed_gate = (
            candidate_summary.passed
            and quality_delta <= candidate_thresholds.max_quality_regression
        )

        return ReleaseComparisonReport(
            generated_at=datetime.now(UTC).isoformat(),
            stable=stable_summary,
            candidate=candidate_summary,
            quality_delta=quality_delta,
            candidate_passed_gate=candidate_passed_gate,
            cases=candidate_cases,
        )


def compare_releases(service: LLMOpsService, dataset_path: Path) -> ReleaseComparisonReport:
    evaluator = ReleaseEvaluator(service, dataset_path)
    return asyncio.run(evaluator.compare())
