"""Runs all 12 analyzers against one completed scan's results and assembles the full
`EvaluationResult` — the only place that happens, so adding a 13th analyzer later is a one-line
registration here, not a change scattered across the API/service layer. Analyzers are pure,
synchronous functions over already-collected data (no I/O), so "run independently... where
safe" is satisfied by running them off the event loop via asyncio.to_thread rather than
serializing them behind awaits for data that's already in memory."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from models.evaluation_models import CategoryResult, EvaluationResult, EvaluationStatus
from models.scan_models import ScanResults
from services import scoring_engine
from services.analyzers import (
    accessibility_analyzer,
    content_analyzer,
    conversion_analyzer,
    innovation_analyzer,
    mobile_analyzer,
    performance_analyzer,
    security_analyzer,
    seo_analyzer,
    technical_analyzer,
    trust_analyzer,
    ui_analyzer,
    ux_analyzer,
)
from services.llm_seo_agent import analyze_seo_with_llm
from services.validation_engine import validate_category_result

_ANALYZERS = {
    "ui": ui_analyzer.analyze,
    "ux": ux_analyzer.analyze,
    "performance": performance_analyzer.analyze,
    "seo": seo_analyzer.analyze,
    "accessibility": accessibility_analyzer.analyze,
    "mobile": mobile_analyzer.analyze,
    "security": security_analyzer.analyze,
    "content": content_analyzer.analyze,
    "conversion": conversion_analyzer.analyze,
    "trust": trust_analyzer.analyze,
    "technical": technical_analyzer.analyze,
    "innovation": innovation_analyzer.analyze,
}

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _merge_category_results(primary: CategoryResult, additional: CategoryResult) -> CategoryResult:
    """Appends an additional analyzer's checks/issues/recommendations onto an already-built
    CategoryResult and recomputes its score with the same passed/(passed+failed) formula
    CategoryBuilder.build() uses — used to layer the optional LLM SEO agent's findings onto the
    rule-based seo_analyzer's result without the two analyzers needing to know about each other."""
    passed = primary.passed_count + additional.passed_count
    failed = primary.failed_count + additional.failed_count
    unavailable = primary.unavailable_count + additional.unavailable_count
    denom = passed + failed
    score = round((passed / denom) * 100, 1) if denom > 0 else None
    return primary.model_copy(
        update={
            "checks": primary.checks + additional.checks,
            "issues": primary.issues + additional.issues,
            "recommendations": primary.recommendations + additional.recommendations,
            "passed_count": passed,
            "failed_count": failed,
            "unavailable_count": unavailable,
            "score": score,
        }
    )


async def run_evaluation(evaluation_id: str, scan: ScanResults, started_at: str) -> EvaluationResult:
    category_results: dict[str, CategoryResult] = {}

    results = await asyncio.gather(
        *[asyncio.to_thread(analyze_fn, scan) for analyze_fn in _ANALYZERS.values()]
    )
    for category_id, result in zip(_ANALYZERS.keys(), results, strict=True):
        category_results[category_id] = validate_category_result(result)

    # Optional LLM-assisted SEO judgment, layered on top of the rule-based seo_analyzer result.
    # Genuinely async (network I/O), unlike the 12 analyzers above — and a no-op, zero-network-
    # call pass-through when no OPENAI_API_KEY is configured (see llm_seo_agent.py).
    llm_seo_result = await analyze_seo_with_llm(scan)
    category_results["seo"] = _merge_category_results(category_results["seo"], llm_seo_result)

    for category_id, result in category_results.items():
        category_results[category_id] = result.model_copy(
            update={"score_explanation": scoring_engine.explain_category_score(result)}
        )

    overall_score, coverage = scoring_engine.calculate_overall_score(category_results)
    grade = scoring_engine.grade_label(overall_score) if overall_score is not None else None

    total_checks = sum(len(r.checks) for r in category_results.values())
    passed_checks = sum(r.passed_count for r in category_results.values())
    failed_checks = sum(r.failed_count for r in category_results.values())
    unavailable_checks = sum(r.unavailable_count for r in category_results.values())

    return EvaluationResult(
        evaluation_id=evaluation_id,
        scan_id=scan.scan_id,
        submitted_url=scan.submitted_url,
        status=EvaluationStatus.COMPLETED,
        scoring_config_version=scoring_engine.SCORING_CONFIG_VERSION,
        overall_score=overall_score,
        score_coverage_percent=coverage,
        grade=grade,
        categories=category_results,
        total_checks=total_checks,
        passed_checks=passed_checks,
        failed_checks=failed_checks,
        unavailable_checks=unavailable_checks,
        started_at=started_at,
        completed_at=_now(),
    )
