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


async def run_evaluation(evaluation_id: str, scan: ScanResults, started_at: str) -> EvaluationResult:
    category_results: dict[str, CategoryResult] = {}

    results = await asyncio.gather(
        *[asyncio.to_thread(analyze_fn, scan) for analyze_fn in _ANALYZERS.values()]
    )
    for category_id, result in zip(_ANALYZERS.keys(), results, strict=True):
        category_results[category_id] = result

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
