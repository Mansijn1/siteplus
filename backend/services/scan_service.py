from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from config import settings
from models.scan_models import (
    ExtractedData,
    LighthouseRun,
    ScanError,
    ScanResults,
    ScanStatus,
    TechnicalInfo,
)
from scanner import page_extractor
from scanner.browser import NavigationResult, ScanBrowserError, run_browser_scan
from scanner.lighthouse import run_lighthouse
from security.url_validation import URLValidationError, ValidatedTarget, validate_public_url

_PIPELINE_STAGES = {
    "validating": ("Validating URL", 5),
    "launching": ("Launching browser", 15),
    "loading": ("Loading page", 30),
    "capturing": ("Capturing screenshots", 45),
    "network": ("Inspecting network & console", 55),
    "extracting": ("Extracting page content", 68),
    "lighthouse_desktop": ("Running Lighthouse audit (desktop)", 82),
    "lighthouse_mobile": ("Running Lighthouse audit (mobile)", 94),
    "finalizing": ("Finalizing results", 100),
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ScanRecord:
    scan_id: str
    submitted_url: str
    status: ScanStatus = ScanStatus.QUEUED
    progress: int = 0
    current_stage: str = "Queued"
    error: ScanError | None = None
    results: ScanResults | None = None
    started_at: str = field(default_factory=_now)
    completed_at: str | None = None


_scans: dict[str, ScanRecord] = {}
_semaphore = asyncio.Semaphore(settings.max_concurrent_scans)


def get_scan(scan_id: str) -> ScanRecord | None:
    return _scans.get(scan_id)


async def validate_url_for_api(raw_url: str) -> ValidatedTarget:
    """Runs the (blocking, DNS-resolving) validator off the event loop. Raises URLValidationError."""
    return await asyncio.to_thread(validate_public_url, raw_url)


def start_scan(validated: ValidatedTarget) -> ScanRecord:
    scan_id = uuid.uuid4().hex[:16]
    record = ScanRecord(scan_id=scan_id, submitted_url=validated.url)
    _scans[scan_id] = record
    asyncio.create_task(_run_pipeline(record, validated.url))
    return record


def _set_stage(record: ScanRecord, key: str) -> None:
    stage, progress = _PIPELINE_STAGES[key]
    record.status = ScanStatus.RUNNING
    record.current_stage = stage
    record.progress = progress


def _fail(record: ScanRecord, code: str, message: str) -> None:
    record.status = ScanStatus.FAILED
    record.error = ScanError(code=code, message=message)
    record.completed_at = _now()


async def _run_pipeline(record: ScanRecord, url: str) -> None:
    async with _semaphore:
        try:
            _set_stage(record, "launching")
            nav_result, screenshots = await run_browser_scan(record.scan_id, url)

            _set_stage(record, "extracting")
            extracted = _build_extracted_data(nav_result, url)

            lighthouse: dict[str, LighthouseRun] = {}
            if settings.lighthouse_enabled:
                _set_stage(record, "lighthouse_desktop")
                lighthouse["desktop"] = await run_lighthouse(nav_result.response_info.final_url or url, "desktop")
                if settings.lighthouse_mobile_enabled:
                    _set_stage(record, "lighthouse_mobile")
                    lighthouse["mobile"] = await run_lighthouse(
                        nav_result.response_info.final_url or url, "mobile"
                    )

            _set_stage(record, "finalizing")
            record.results = ScanResults(
                scan_id=record.scan_id,
                submitted_url=record.submitted_url,
                extracted=extracted,
                screenshots=screenshots,
                lighthouse=lighthouse,
                console_messages=nav_result.console_messages,
                response=nav_result.response_info,
                load_timing=nav_result.load_timing,
                started_at=record.started_at,
                completed_at=_now(),
            )
            record.status = ScanStatus.COMPLETED
            record.progress = 100
            record.current_stage = "Completed"
            record.completed_at = _now()

        except URLValidationError as exc:
            _fail(record, exc.code, exc.message)
        except ScanBrowserError as exc:
            _fail(record, exc.code, exc.message)
        except Exception as exc:  # noqa: BLE001 — last-resort guard so a scan always resolves to failed, never hangs
            _fail(record, "unexpected_error", f"The scan failed unexpectedly: {exc}")


def _build_extracted_data(nav: NavigationResult, submitted_url: str) -> ExtractedData:
    basic = page_extractor.extract_basic_info(nav.html, submitted_url, nav.response_info.final_url or submitted_url)
    seo = page_extractor.extract_seo_info(nav.html, nav.response_info.final_url or submitted_url)
    content = page_extractor.extract_content_info(nav.html, seo)
    ux = page_extractor.extract_ux_info(nav.html, nav.horizontal_overflow)

    from bs4 import BeautifulSoup  # local import avoids cross-module coupling for a tiny count

    soup = BeautifulSoup(nav.html, "html.parser")
    technical = TechnicalInfo(
        https=nav.response_info.https,
        status_code=nav.response_info.status_code,
        was_redirected=len(nav.response_info.redirect_chain) > 0,
        redirect_count=len(nav.response_info.redirect_chain),
        response_headers=nav.response_info.headers,
        image_count=len(soup.find_all("img")),
        script_count=len(soup.find_all("script")),
        stylesheet_count=len(soup.find_all("link", rel="stylesheet")),
        failed_requests=nav.failed_requests,
    )

    return ExtractedData(basic=basic, seo=seo, content=content, technical=technical, ux=ux)
