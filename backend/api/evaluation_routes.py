"""Phase 3 evaluation API. `POST /api/evaluate` runs synchronously (not the async start/poll
pattern Phase 2's scan endpoints use) because all 12 analyzers are pure computation over
already-collected scan data — no browser, no network, consistently well under a second — so
there's nothing to poll for. The result is still stored by evaluation_id for the GET endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from models.evaluation_models import (
    CategoriesResponse,
    CategorySummary,
    EvaluationRequest,
    EvaluationResult,
    Issue,
    IssuesResponse,
    Priority,
    Recommendation,
    RecommendationsResponse,
    Severity,
)
from services import evaluation_service, recommendation_engine
from services.evaluation_service import ScanNotCompletedError, ScanNotFoundError

logger = logging.getLogger("evaluation_routes")
router = APIRouter(prefix="/api", tags=["evaluation"])


@router.post("/evaluate", response_model=EvaluationResult)
async def evaluate(request: EvaluationRequest) -> EvaluationResult:
    try:
        return await evaluation_service.start_evaluation(request.scan_id)
    except ScanNotFoundError as exc:
        raise HTTPException(status_code=404, detail={"code": "scan_not_found", "message": str(exc)}) from exc
    except ScanNotCompletedError as exc:
        raise HTTPException(
            status_code=409,
            detail={"code": "scan_not_completed", "message": f"Scan status is '{exc.status}', not 'completed'."},
        ) from exc
    except Exception as exc:  # noqa: BLE001 — last-resort guard; evaluation_service already catches analyzer failures
        logger.exception("Unexpected error starting evaluation for scan_id=%s", request.scan_id)
        raise HTTPException(status_code=500, detail={"code": "unexpected_error", "message": str(exc)[:500]}) from exc


def _get_or_404(evaluation_id: str) -> EvaluationResult:
    result = evaluation_service.get_evaluation(evaluation_id)
    if result is None:
        raise HTTPException(status_code=404, detail={"code": "evaluation_not_found", "message": "No evaluation with that ID."})
    return result


@router.get("/evaluation/{evaluation_id}", response_model=EvaluationResult)
async def get_evaluation(evaluation_id: str) -> EvaluationResult:
    return _get_or_404(evaluation_id)


@router.get("/evaluation/{evaluation_id}/issues", response_model=IssuesResponse)
async def get_issues(
    evaluation_id: str,
    severity: Severity | None = Query(default=None),
    category: str | None = Query(default=None),
    priority: Priority | None = Query(default=None),
) -> IssuesResponse:
    result = _get_or_404(evaluation_id)
    issues: list[Issue] = [issue for cat in result.categories.values() for issue in cat.issues]

    if severity is not None:
        issues = [i for i in issues if i.severity == severity]
    if category is not None:
        issues = [i for i in issues if i.category == category]
    if priority is not None:
        issues = [i for i in issues if i.priority == priority]

    severity_rank = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.LOW: 3, Severity.INFORMATIONAL: 4}
    issues.sort(key=lambda i: severity_rank[i.severity])

    return IssuesResponse(evaluation_id=evaluation_id, total=len(issues), issues=issues)


@router.get("/evaluation/{evaluation_id}/recommendations", response_model=RecommendationsResponse)
async def get_recommendations(evaluation_id: str) -> RecommendationsResponse:
    result = _get_or_404(evaluation_id)
    recs: list[Recommendation] = recommendation_engine.collect_recommendations(result.categories)
    return RecommendationsResponse(evaluation_id=evaluation_id, total=len(recs), recommendations=recs)


@router.get("/evaluation/{evaluation_id}/categories", response_model=CategoriesResponse)
async def get_categories(evaluation_id: str) -> CategoriesResponse:
    result = _get_or_404(evaluation_id)
    summaries = [
        CategorySummary(
            category=cat.category,
            weight=cat.weight,
            score=cat.score,
            passed_count=cat.passed_count,
            failed_count=cat.failed_count,
            unavailable_count=cat.unavailable_count,
        )
        for cat in result.categories.values()
    ]
    return CategoriesResponse(evaluation_id=evaluation_id, overall_score=result.overall_score, categories=summaries)
