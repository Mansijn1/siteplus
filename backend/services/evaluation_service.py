"""In-memory evaluation store + the orchestration entrypoint the API routes call — mirrors
`scan_service.py`'s pattern exactly (same in-memory-dict tradeoff, same reasons it's fine for
this phase's scope: see that file's own docstring)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from models.evaluation_models import EvaluationError, EvaluationResult, EvaluationStatus
from services import evaluation_engine, scan_service


class ScanNotFoundError(Exception):
    pass


class ScanNotCompletedError(Exception):
    def __init__(self, status: str):
        self.status = status
        super().__init__(f"Scan is not completed (status={status})")


_evaluations: dict[str, EvaluationResult] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_evaluation(evaluation_id: str) -> EvaluationResult | None:
    return _evaluations.get(evaluation_id)


async def start_evaluation(scan_id: str) -> EvaluationResult:
    """Synchronous-feeling but genuinely async: analyzers run off the event loop (see
    evaluation_engine), so this can simply be awaited rather than needing scan_service's
    create_task + polling pattern — a full evaluation over already-collected data finishes in
    well under a second, unlike a multi-stage browser scan."""
    scan_record = scan_service.get_scan(scan_id)
    if scan_record is None:
        raise ScanNotFoundError(scan_id)
    if scan_record.status.value != "completed" or scan_record.results is None:
        raise ScanNotCompletedError(scan_record.status.value)

    evaluation_id = uuid.uuid4().hex[:16]
    started_at = _now()

    try:
        result = await evaluation_engine.run_evaluation(evaluation_id, scan_record.results, started_at)
    except Exception as exc:  # noqa: BLE001 — an evaluation must resolve to failed, never raise past the API
        result = EvaluationResult(
            evaluation_id=evaluation_id,
            scan_id=scan_id,
            submitted_url=scan_record.results.submitted_url,
            status=EvaluationStatus.FAILED,
            error=EvaluationError(code="evaluation_failed", message=str(exc)[:500]),
            started_at=started_at,
            completed_at=_now(),
        )

    _evaluations[evaluation_id] = result
    return result
