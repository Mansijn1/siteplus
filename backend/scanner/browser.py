"""Core Playwright-driven scan: launches Chromium, navigates to the validated target at both
desktop and mobile viewports, and collects everything observable from that navigation —
screenshots, console output, failed requests, response/redirect info, load timing, and (Phase 3)
accessibility/typography/image/touch-target/TLS evidence captured from the same pages. Never
submits a form, clicks a link, or executes anything beyond what loading the page itself does."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from urllib.parse import urlparse

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import Route, TimeoutError as PlaywrightTimeoutError, async_playwright

from config import settings
from models.scan_models import (
    AccessibilityAudit,
    AuditExtras,
    FailedRequest,
    ImageDiagnostics,
    LayoutSignal,
    LoadTiming,
    MixedContentInfo,
    ResponseInfo,
    RobotsSitemapInfo,
    ScreenshotResult,
    TlsCertificateInfo,
    TouchTargetSignal,
    TypographySignal,
)
from scanner.accessibility_audit import run_accessibility_audit
from scanner.network_inspector import NetworkInspector
from scanner.page_diagnostics import (
    detect_mixed_content,
    run_image_diagnostics,
    run_layout_signal,
    run_touch_target_signal,
    run_typography_signal,
)
from scanner.screenshot import public_screenshot_url, save_screenshot
from scanner.site_probe import probe_robots_and_sitemap
from security.url_validation import URLValidationError, is_request_allowed


class ScanBrowserError(Exception):
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(message)


@dataclass
class NavigationResult:
    html: str
    response_info: ResponseInfo
    load_timing: LoadTiming
    console_messages: list = field(default_factory=list)
    failed_requests: list[FailedRequest] = field(default_factory=list)
    horizontal_overflow: bool | None = None
    accessibility: AccessibilityAudit = field(
        default_factory=lambda: AccessibilityAudit(available=False, reason="not_run")
    )
    tls: TlsCertificateInfo = field(default_factory=lambda: TlsCertificateInfo(available=False, reason="not_run"))
    typography: TypographySignal = field(
        default_factory=lambda: TypographySignal(available=False, reason="not_run")
    )
    images: ImageDiagnostics = field(default_factory=lambda: ImageDiagnostics(available=False, reason="not_run"))
    mixed_content: MixedContentInfo = field(default_factory=lambda: MixedContentInfo(available=False))
    layout: LayoutSignal = field(default_factory=lambda: LayoutSignal(available=False, reason="not_run"))


async def _guard_navigation(route: Route, *, allow_loopback_for_benchmark: bool = False) -> None:
    """Route handler applied to every main-frame document request (initial nav + every
    redirect hop) so a target that redirects to an internal address after passing the initial
    check is still blocked before Chromium ever connects to it.

    `allow_loopback_for_benchmark` exists for exactly one caller: benchmark/runner.py, which
    deliberately scans its own local fixture server (127.0.0.1) to compute precision/recall
    against hand-verified ground truth. It is never True on any path reachable from a public API
    route — scan_service.py and website_evaluation_service.py never pass it — so it does not
    weaken SSRF protection for any user-submitted URL."""
    request = route.request
    if request.resource_type == "document":
        allowed = is_request_allowed(request.url)
        if not allowed and allow_loopback_for_benchmark:
            hostname = urlparse(request.url).hostname
            allowed = hostname in ("127.0.0.1", "localhost", "::1")
        if not allowed:
            await route.abort("blockedbyclient")
            return
    await route.continue_()


def _redirect_chain(response) -> list[str]:
    chain: list[str] = []
    req = response.request
    seen = set()
    while req is not None and req.url not in seen:
        seen.add(req.url)
        chain.append(req.url)
        req = req.redirected_from
    chain.reverse()
    return chain


async def run_browser_scan(
    scan_id: str, url: str, *, allow_loopback_for_benchmark: bool = False
) -> tuple[NavigationResult, dict[str, ScreenshotResult], AuditExtras]:
    screenshots: dict[str, ScreenshotResult] = {}
    navigation_result: NavigationResult | None = None
    mobile_result = MobileScanResult(
        touch_targets=TouchTargetSignal(available=False, reason="not_run"),
        touch_targets_tablet=TouchTargetSignal(available=False, reason="not_run"),
    )

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
            )
            try:
                navigation_result = await _scan_desktop(
                    browser, scan_id, url, screenshots, allow_loopback_for_benchmark=allow_loopback_for_benchmark
                )
                mobile_result = await _scan_mobile(
                    browser, scan_id, url, screenshots, allow_loopback_for_benchmark=allow_loopback_for_benchmark
                )
            finally:
                await browser.close()
    except PlaywrightError as exc:
        raise ScanBrowserError(f"Could not launch or control the browser: {exc}", "browser_launch_failed") from exc

    if navigation_result is None:
        raise ScanBrowserError("Scan produced no result.", "unknown_browser_error")

    if settings.site_probe_enabled:
        robots_sitemap = await probe_robots_and_sitemap(navigation_result.response_info.final_url or url)
    else:
        robots_sitemap = RobotsSitemapInfo(available=False, reason="site_probe_disabled")

    audit_extras = AuditExtras(
        accessibility=navigation_result.accessibility,
        tls=navigation_result.tls,
        typography=navigation_result.typography,
        images=navigation_result.images,
        touch_targets=mobile_result.touch_targets,
        touch_targets_tablet=mobile_result.touch_targets_tablet,
        robots_sitemap=robots_sitemap,
        mixed_content=navigation_result.mixed_content,
        layout=navigation_result.layout,
    )

    return navigation_result, screenshots, audit_extras


async def _scan_desktop(
    browser, scan_id: str, url: str, screenshots: dict[str, ScreenshotResult], *, allow_loopback_for_benchmark: bool = False
) -> NavigationResult:
    width, height = settings.desktop_viewport
    context = await browser.new_context(viewport={"width": width, "height": height})
    inspector = NetworkInspector()
    page = await context.new_page()
    inspector.attach(page)

    async def _route_handler(route: Route) -> None:
        await _guard_navigation(route, allow_loopback_for_benchmark=allow_loopback_for_benchmark)

    await page.route("**/*", _route_handler)

    start = time.monotonic()
    try:
        response = await page.goto(url, wait_until="load", timeout=settings.navigation_timeout_ms)
    except PlaywrightTimeoutError as exc:
        await context.close()
        raise ScanBrowserError(
            f"The website took too long to respond (over {settings.navigation_timeout_ms / 1000:.0f}s).",
            "navigation_timeout",
        ) from exc
    except PlaywrightError as exc:
        await context.close()
        message = str(exc)
        if "net::ERR_BLOCKED_BY_CLIENT" in message or "blockedbyclient" in message.lower():
            raise URLValidationError(
                "The website redirected to a private or internal address and was blocked.", "blocked_redirect"
            ) from exc
        raise ScanBrowserError(f"The website could not be loaded: {exc}", "navigation_failed") from exc

    if response is None:
        await context.close()
        raise ScanBrowserError("The website did not return a response.", "no_response")

    elapsed_ms = (time.monotonic() - start) * 1000

    try:
        body = await response.body()
        if len(body) > settings.max_response_body_bytes:
            await context.close()
            raise ScanBrowserError("The website's response was too large to process.", "response_too_large")
    except PlaywrightError:
        pass  # body already consumed/unavailable — not fatal, html below still works

    html = await page.content()
    final_url = page.url
    redirect_chain = _redirect_chain(response)

    horizontal_overflow = None
    try:
        horizontal_overflow = await page.evaluate(
            "document.documentElement.scrollWidth > document.documentElement.clientWidth + 1"
        )
    except PlaywrightError:
        pass

    timing = LoadTiming(response_time_ms=round(elapsed_ms, 1))
    try:
        nav_timing = await page.evaluate(
            "() => { const n = performance.getEntriesByType('navigation')[0]; "
            "return n ? { dcl: n.domContentLoadedEventEnd, load: n.loadEventEnd } : null; }"
        )
        if nav_timing:
            timing.dom_content_loaded_ms = nav_timing.get("dcl")
            timing.load_event_ms = nav_timing.get("load")
    except PlaywrightError:
        pass

    try:
        screenshot_bytes = await page.screenshot(type="png")
        save_screenshot(scan_id, "desktop", screenshot_bytes)
        screenshots["desktop"] = ScreenshotResult(
            available=True, path=f"{scan_id}-desktop.png", url=public_screenshot_url(scan_id, "desktop"),
            width=width, height=height,
        )
    except PlaywrightError as exc:
        screenshots["desktop"] = ScreenshotResult(available=False, reason=str(exc))

    response_info = ResponseInfo(
        status_code=response.status,
        final_url=final_url,
        redirect_chain=redirect_chain[:-1] if redirect_chain else [],
        headers=dict(response.headers),
        https=final_url.startswith("https://"),
    )

    tls = TlsCertificateInfo(available=False, reason="not_https_or_unavailable")
    try:
        details = await response.security_details()
        if details:
            tls = TlsCertificateInfo(
                available=True,
                protocol=details.get("protocol"),
                issuer=details.get("issuer"),
                valid_from=details.get("validFrom"),
                valid_to=details.get("validTo"),
                subject_name=details.get("subjectName"),
            )
    except Exception:  # noqa: BLE001 — TLS detail capture is best-effort, never fatal to the scan
        pass

    accessibility = await run_accessibility_audit(page)
    typography = await run_typography_signal(page)
    images = await run_image_diagnostics(page)
    layout = await run_layout_signal(page)
    mixed_content = detect_mixed_content(html, final_url)

    result = NavigationResult(
        html=html,
        response_info=response_info,
        load_timing=timing,
        console_messages=inspector.console_messages,
        failed_requests=inspector.failed_requests,
        horizontal_overflow=horizontal_overflow,
        accessibility=accessibility,
        tls=tls,
        typography=typography,
        images=images,
        layout=layout,
        mixed_content=mixed_content,
    )

    await context.close()
    return result


@dataclass
class MobileScanResult:
    touch_targets: TouchTargetSignal
    touch_targets_tablet: TouchTargetSignal


async def _scan_mobile(
    browser, scan_id: str, url: str, screenshots: dict[str, ScreenshotResult], *, allow_loopback_for_benchmark: bool = False
) -> MobileScanResult:
    width, height = settings.mobile_viewport
    context = await browser.new_context(
        viewport={"width": width, "height": height},
        is_mobile=True,
        has_touch=True,
        user_agent=(
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
            "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        ),
    )
    page = await context.new_page()

    async def _route_handler(route: Route) -> None:
        await _guard_navigation(route, allow_loopback_for_benchmark=allow_loopback_for_benchmark)

    await page.route("**/*", _route_handler)

    touch_targets = TouchTargetSignal(available=False, reason="navigation_failed")
    touch_targets_tablet = TouchTargetSignal(available=False, reason="navigation_failed")
    try:
        await page.goto(url, wait_until="load", timeout=settings.navigation_timeout_ms)
        screenshot_bytes = await page.screenshot(type="png")
        save_screenshot(scan_id, "mobile", screenshot_bytes)
        screenshots["mobile"] = ScreenshotResult(
            available=True, path=f"{scan_id}-mobile.png", url=public_screenshot_url(scan_id, "mobile"),
            width=width, height=height,
        )
        touch_targets = await run_touch_target_signal(page)

        # Tablet re-measurement reuses this same loaded page via a viewport resize — a relayout,
        # not a second navigation — so "multiple viewport sizes" coverage costs no extra request.
        tablet_width, tablet_height = settings.tablet_viewport
        try:
            await page.set_viewport_size({"width": tablet_width, "height": tablet_height})
            touch_targets_tablet = await run_touch_target_signal(page)
        except PlaywrightError as exc:
            touch_targets_tablet = TouchTargetSignal(available=False, reason=f"viewport_resize_failed: {exc}"[:300])
    except (PlaywrightError, PlaywrightTimeoutError) as exc:
        screenshots["mobile"] = ScreenshotResult(available=False, reason=str(exc)[:300])
    finally:
        await context.close()

    return MobileScanResult(touch_targets=touch_targets, touch_targets_tablet=touch_targets_tablet)
