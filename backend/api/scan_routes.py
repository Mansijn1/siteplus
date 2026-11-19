from __future__ import annotations

from fastapi import APIRouter, HTTPException

from models.scan_models import (
    ScanError,
    ScanRequest,
    ScanResultsResponse,
    ScanStatus,
    ScanStatusResponse,
    StartScanResponse,
)
from security.url_validation import URLValidationError
from services.scan_service import get_scan, start_scan, validate_url_for_api

router = APIRouter(prefix="/api/scans", tags=["scans"])


@router.post("", response_model=StartScanResponse, status_code=202)
async def create_scan(payload: ScanRequest) -> StartScanResponse:
    try:
        validated = await validate_url_for_api(payload.url)
    except URLValidationError as exc:
        raise HTTPException(status_code=400, detail={"code": exc.code, "message": exc.message}) from exc

    record = start_scan(validated)
    return StartScanResponse(scan_id=record.scan_id, status=record.status)


@router.get("/{scan_id}/status", response_model=ScanStatusResponse)
async def get_scan_status(scan_id: str) -> ScanStatusResponse:
    record = get_scan(scan_id)
    if record is None:
        raise HTTPException(status_code=404, detail={"code": "scan_not_found", "message": "No scan with that ID."})
    return ScanStatusResponse(
        scan_id=record.scan_id,
        status=record.status,
        progress=record.progress,
        current_stage=record.current_stage,
        error=record.error,
    )


@router.get("/{scan_id}/results", response_model=ScanResultsResponse)
async def get_scan_results(scan_id: str) -> ScanResultsResponse:
    record = get_scan(scan_id)
    if record is None:
        raise HTTPException(status_code=404, detail={"code": "scan_not_found", "message": "No scan with that ID."})

    if record.status == ScanStatus.FAILED:
        return ScanResultsResponse(scan_id=scan_id, status=record.status, results=None, error=record.error)

    if record.status in (ScanStatus.QUEUED, ScanStatus.RUNNING):
        raise HTTPException(
            status_code=409,
            detail={
                "code": "scan_not_complete",
                "message": f"Scan is still {record.status.value}. Poll /status until it completes.",
            },
        )

    if record.results is None:
        raise HTTPException(
            status_code=500,
            detail={"code": "missing_results", "message": "Scan completed but produced no results."},
        )

    return ScanResultsResponse(scan_id=scan_id, status=record.status, results=record.results, error=None)
