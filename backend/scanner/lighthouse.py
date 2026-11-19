"""Runs Google Lighthouse (via the `lighthouse` npm CLI, invoked through `npx`) against the
already-validated target URL and parses the category scores and key metrics out of its JSON
report. The full raw report is always saved to disk so the future scoring engine can go back
to it for audit-level detail.

If Lighthouse is unavailable or fails for any reason, every field comes back `available=False`
with a `reason` — this module never invents a score."""

from __future__ import annotations

import asyncio
import json
import shutil
import uuid
from pathlib import Path

from config import settings
from models.scan_models import LighthouseCategoryScores, LighthouseMetrics, LighthouseRun, MetricResult

_UNAVAILABLE_METRIC = MetricResult(available=False, reason="lighthouse_unavailable")
_UNAVAILABLE_SCORES = LighthouseCategoryScores(
    performance=_UNAVAILABLE_METRIC,
    accessibility=_UNAVAILABLE_METRIC,
    seo=_UNAVAILABLE_METRIC,
    best_practices=_UNAVAILABLE_METRIC,
)
_UNAVAILABLE_METRICS = LighthouseMetrics(
    first_contentful_paint=_UNAVAILABLE_METRIC,
    largest_contentful_paint=_UNAVAILABLE_METRIC,
    speed_index=_UNAVAILABLE_METRIC,
    total_blocking_time=_UNAVAILABLE_METRIC,
    cumulative_layout_shift=_UNAVAILABLE_METRIC,
)


def _unavailable(form_factor: str, reason: str) -> LighthouseRun:
    return LighthouseRun(available=False, reason=reason, form_factor=form_factor, scores=None, metrics=None)


def _resolve_npx() -> str | None:
    # `npx` itself is enough — it will fetch `lighthouse` on demand. Resolved via shutil.which
    # (not passed as the bare string "npx") because on Windows, asyncio's subprocess exec does
    # not search PATHEXT the way a real shell does — a bare "npx" raises FileNotFoundError even
    # though it resolves fine to npx.CMD via `where`/`which`.
    return shutil.which("npx") or shutil.which("lighthouse")


def _score_or_unavailable(categories: dict, key: str) -> MetricResult:
    cat = categories.get(key)
    if not cat or cat.get("score") is None:
        return MetricResult(available=False, reason=f"lighthouse_category_missing:{key}")
    return MetricResult(available=True, value=round(cat["score"] * 100, 1))


def _audit_metric(audits: dict, key: str) -> MetricResult:
    audit = audits.get(key)
    if not audit or audit.get("numericValue") is None:
        return MetricResult(available=False, reason=f"lighthouse_audit_missing:{key}")
    return MetricResult(available=True, value=audit["numericValue"])


async def run_lighthouse(url: str, form_factor: str = "desktop") -> LighthouseRun:
    if not settings.enable_lighthouse:
        return _unavailable(form_factor, "lighthouse_disabled")
    npx_path = _resolve_npx()
    if not npx_path:
        return _unavailable(form_factor, "lighthouse_cli_not_found")

    report_path = settings.lighthouse_dir / f"{uuid.uuid4().hex}-{form_factor}.json"

    # Extra flags trim Chrome's memory footprint for Render's free tier (512MB total, shared with
    # the Python/uvicorn process) — a plain headless launch was enough to OOM-restart the whole
    # container mid-scan there, separate from (and after) the getDebuggableChrome fix.
    chrome_flags = (
        "--headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage "
        "--disable-extensions --disable-background-networking --disable-sync --disable-translate "
        "--disable-default-apps --no-first-run --mute-audio --disable-backgrounding-occluded-windows "
        "--renderer-process-limit=1 --disable-ipc-flooding-protection"
    )
    cmd = [
        npx_path,
        "--yes",
        "lighthouse",
        url,
        "--output=json",
        f"--output-path={report_path}",
        f"--chrome-flags={chrome_flags}",
        "--only-categories=performance,accessibility,seo,best-practices",
        "--quiet",
        "--disable-full-page-screenshot",
    ]
    # `--preset=desktop` sets form-factor, screenEmulation, and throttling together — passing
    # `--form-factor=desktop` alone leaves screenEmulation at its mobile default and Lighthouse
    # refuses to run ("Screen emulation mobile setting (true) does not match formFactor setting
    # (desktop)"). The mobile run needs no extra flags: Lighthouse's own default preset already
    # is mobile, matching the viewport this project scans at.
    if form_factor == "desktop":
        cmd.append("--preset=desktop")
    env = None
    if settings.lighthouse_chrome_path:
        import os

        env = {**os.environ, "CHROME_PATH": settings.lighthouse_chrome_path}

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            shell=False,
        )
        try:
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=settings.lighthouse_timeout_s)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return _unavailable(form_factor, "lighthouse_timeout")

        if proc.returncode != 0 or not report_path.exists():
            full_stderr = (stderr or b"").decode("utf-8", errors="ignore")
            # Printed in full to stdout (captured in the platform's runtime logs) because the
            # `reason` field returned to the API is deliberately kept short — chrome-launcher's
            # own diagnostic (e.g. why Chrome's remote-debugging port never became reachable)
            # is usually earlier in stderr than the last few hundred characters.
            print(f"[lighthouse:{form_factor}] subprocess failed, full stderr:\n{full_stderr}", flush=True)
            detail = full_stderr[-1200:]
            return _unavailable(form_factor, f"lighthouse_process_failed: {detail}".strip())

        report = json.loads(report_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return _unavailable(form_factor, "npx_not_found")
    except Exception as exc:  # noqa: BLE001 — any parsing/process failure degrades, never fabricates
        return _unavailable(form_factor, f"lighthouse_error: {exc}")

    categories = report.get("categories", {})
    audits = report.get("audits", {})

    scores = LighthouseCategoryScores(
        performance=_score_or_unavailable(categories, "performance"),
        accessibility=_score_or_unavailable(categories, "accessibility"),
        seo=_score_or_unavailable(categories, "seo"),
        best_practices=_score_or_unavailable(categories, "best-practices"),
    )
    metrics = LighthouseMetrics(
        first_contentful_paint=_audit_metric(audits, "first-contentful-paint"),
        largest_contentful_paint=_audit_metric(audits, "largest-contentful-paint"),
        speed_index=_audit_metric(audits, "speed-index"),
        total_blocking_time=_audit_metric(audits, "total-blocking-time"),
        cumulative_layout_shift=_audit_metric(audits, "cumulative-layout-shift"),
    )

    return LighthouseRun(
        available=True,
        form_factor=form_factor,
        scores=scores,
        metrics=metrics,
        raw_report_path=str(report_path.relative_to(settings.lighthouse_dir.parent.parent)),
    )
