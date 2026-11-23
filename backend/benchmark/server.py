"""A tiny local HTTP server for the benchmark fixtures — NOT part of the production API, never
imported by main.py, and never reachable through any public route. Exists only so the benchmark
runner can exercise the real scan pipeline (Playwright navigation, real HTTP responses) against
pages with precisely known, hand-authored ground truth, including server-level properties like
response headers that a static HTML file can't express on its own (e.g. "clean.html" is served
WITH the recommended security headers; "security_broken.html" deliberately withOUT them)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, Response

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

_GOOD_SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=63072000",
    # 'unsafe-inline' on script-src only: clean.html has an inline JSON-LD block (for the
    # structured-data ground truth case), and a strict `default-src 'self'` with no script-src
    # override blocks ALL inline <script> tags, JSON-LD included, which caused a CSP console
    # error — a real browser console error, but a self-inflicted fixture conflict, not evidence
    # of a SitePlus detection bug. This is also a realistic real-world CSP compromise.
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}

# Paths that get the good security headers. Every other path (notably security_broken.html)
# gets none — that absence IS the ground-truth defect for the security category.
_PATHS_WITH_SECURITY_HEADERS = {"/clean.html"}

app = FastAPI(title="SitePlus benchmark fixture server")


@app.get("/assets/{filename}")
async def asset(filename: str) -> Response:
    file_path = FIXTURES_DIR / "assets" / filename
    if not file_path.exists():
        # A deliberately-missing asset is itself a ground-truth fixture (ui_broken.html's
        # broken-image case) — it must 404 cleanly, not raise, so the browser sees a normal
        # failed image load rather than this process logging a server-side traceback.
        return Response(status_code=404, content="Not found")
    return FileResponse(file_path)


@app.get("/{page_name}.html")
async def page(page_name: str, request: Request) -> Response:
    file_path = FIXTURES_DIR / f"{page_name}.html"
    if not file_path.exists():
        return Response(status_code=404, content="Not found")
    body = file_path.read_bytes()
    headers = dict(_GOOD_SECURITY_HEADERS) if request.url.path in _PATHS_WITH_SECURITY_HEADERS else {}
    return Response(content=body, media_type="text/html", headers=headers)
