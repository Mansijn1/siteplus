from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.scan_routes import router as scan_router
from config import settings

app = FastAPI(
    title="WebRate AI Scanner API",
    description="Phase 2: real, passive website scanning and raw data collection.",
    version="0.1.0",
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


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
