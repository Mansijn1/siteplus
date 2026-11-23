"""Exposes the benchmark's last recorded result (benchmark/results/latest.json) so the dashboard
can show REAL precision/recall/F1 numbers — never fabricated ones — clearly separated from any
individual scan's confidence scores. Read-only: running the benchmark itself is a deliberate,
developer-run action (`python -m benchmark.runner`), not something a public API call triggers,
since it launches real browser automation against the local fixture server."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])

_RESULTS_PATH = Path(__file__).resolve().parent.parent / "benchmark" / "results" / "latest.json"


@router.get("/latest")
async def get_latest_benchmark() -> dict:
    if not _RESULTS_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail={"code": "no_benchmark_results", "message": "No benchmark has been run yet (python -m benchmark.runner)."},
        )
    return json.loads(_RESULTS_PATH.read_text(encoding="utf-8"))
