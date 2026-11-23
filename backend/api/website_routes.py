"""Phase 4 multi-page website evaluation API. Like `/api/evaluate`, this runs synchronously —
the per-page concurrency semaphore already bounds how much browser work happens at once, and a
request for up to 15 pages still completes in a predictable, bounded time, so there's nothing
gained by adding a second start/poll pattern on top of it."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from models.website_models import WebsiteEvaluationRequest, WebsiteEvaluationResult
from security.url_validation import URLValidationError
from services import scan_service, website_evaluation_service

logger = logging.getLogger("website_routes")
router = APIRouter(prefix="/api/website", tags=["website"])


@router.post("/evaluate", response_model=WebsiteEvaluationResult)
async def evaluate_website(request: WebsiteEvaluationRequest) -> WebsiteEvaluationResult:
    try:
        validated = await scan_service.validate_url_for_api(request.url)
    except URLValidationError as exc:
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": exc.message}) from exc

    try:
        return await website_evaluation_service.start_website_evaluation(validated.url, request.max_pages)
    except Exception as exc:  # noqa: BLE001 — last-resort guard; the service already catches per-page failures
        logger.exception("Unexpected error evaluating website url=%s", request.url)
        raise HTTPException(status_code=500, detail={"code": "unexpected_error", "message": str(exc)[:500]}) from exc


@router.get("/evaluate/{website_evaluation_id}", response_model=WebsiteEvaluationResult)
async def get_website_evaluation(website_evaluation_id: str) -> WebsiteEvaluationResult:
    result = website_evaluation_service.get_website_evaluation(website_evaluation_id)
    if result is None:
        raise HTTPException(
            status_code=404, detail={"code": "website_evaluation_not_found", "message": "No website evaluation with that ID."}
        )
    return result
