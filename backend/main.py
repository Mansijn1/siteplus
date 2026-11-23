from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.benchmark_routes import router as benchmark_router
from api.evaluation_routes import router as evaluation_router
from api.scan_routes import router as scan_router
from api.website_routes import router as website_router
from config import settings

app = FastAPI(
    title="WebRate AI Scanner API",
    description=(
        "Phase 2: real, passive website scanning. Phase 3: the 12-category evaluation engine. "
        "Phase 4: multi-page website auditing, confidence scoring, and benchmarking."
    ),
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_origin_regex=settings.cors_allow_origin_regex,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
    allow_credentials=False,
)

app.mount("/static/screenshots", StaticFiles(directory=str(settings.screenshot_dir)), name="screenshots")

app.include_router(scan_router)
app.include_router(evaluation_router)
app.include_router(website_router)
app.include_router(benchmark_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
