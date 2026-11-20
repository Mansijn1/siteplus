"""Website Performance (12%) — real Lighthouse scores/Core Web Vitals when Lighthouse ran (it's
disabled by default on this deployment's free tier — see backend/README.md — but fully supported
when enabled), plus checks that work from Phase 2's always-available evidence (load timing,
resource counts, failed requests) so this category still scores meaningfully without Lighthouse.
True field INP isn't measurable from a single automated run; Lighthouse's own Total Blocking
Time is used as the closest lab-data proxy, and that substitution is stated plainly rather than
silently presented as INP."""

from __future__ import annotations

from models.evaluation_models import CategoryResult, Effort, Evidence, Priority, Severity
from models.scan_models import LighthouseRun, MetricResult, ScanResults
from services.analyzers.base import CategoryBuilder
from services.severity_engine import derive_priority

# (metric key, label, "good" threshold, unit, severity if failing)
_LIGHTHOUSE_METRIC_THRESHOLDS = [
    ("largest_contentful_paint", "Largest Contentful Paint (LCP)", 2500, "ms", Severity.HIGH),
    ("first_contentful_paint", "First Contentful Paint (FCP)", 1800, "ms", Severity.MEDIUM),
    ("cumulative_layout_shift", "Cumulative Layout Shift (CLS)", 0.1, "", Severity.MEDIUM),
    ("total_blocking_time", "Total Blocking Time (TBT, used as an INP proxy — true field INP isn't measurable from a single automated run)", 200, "ms", Severity.MEDIUM),
]


def analyze(scan: ScanResults) -> CategoryResult:
    url = scan.response.final_url or scan.submitted_url
    b = CategoryBuilder("performance", url)

    desktop_lh = scan.lighthouse.get("desktop")
    if desktop_lh and desktop_lh.available:
        _check_lighthouse_category_score(b, desktop_lh)
        _check_core_web_vitals(b, desktop_lh)
    else:
        reason = desktop_lh.reason if desktop_lh else "lighthouse_not_run"
        b.unavailable("lighthouse_performance_score", "Lighthouse Performance category score", reason or "unavailable")
        for key, label, *_ in _LIGHTHOUSE_METRIC_THRESHOLDS:
            b.unavailable(f"metric:{key}", label, reason or "unavailable")

    _check_response_time(b, scan)
    _check_resource_weight(b, scan)
    _check_failed_requests(b, scan)

    summary = (
        f"Performance analysis found {b.issue_count} issue(s)."
        if b.issue_count
        else "No performance issues detected from the available evidence."
    )
    return b.build(summary)


def _check_lighthouse_category_score(b: CategoryBuilder, lh: LighthouseRun) -> None:
    metric = lh.scores.performance if lh.scores else MetricResult(available=False)
    if not metric.available or metric.value is None:
        b.unavailable("lighthouse_performance_score", "Lighthouse Performance category score", metric.reason or "unavailable")
        return
    score = float(metric.value)
    if score >= 80:
        b.passed("lighthouse_performance_score", "Lighthouse Performance category score", detail=f"{score}/100")
    else:
        severity = Severity.CRITICAL if score < 50 else Severity.HIGH
        b.failed(
            "lighthouse_performance_score", "Lighthouse Performance category score",
            title=f"Lighthouse Performance score is low ({score}/100)",
            description="Google Lighthouse's overall lab-data Performance score for the desktop run.",
            severity=severity,
            priority=derive_priority(severity),
            impact="A low Lighthouse Performance score correlates with slower perceived load and higher visitor drop-off.",
            recommendation="Review the Core Web Vitals checks below and the full Lighthouse report for the specific slowest contributors.",
            how_to_fix=["Open the saved Lighthouse JSON report for this scan for the full opportunity/diagnostic list.", "Prioritize fixes for whichever Core Web Vitals checks below are failing."],
            expected_benefit="Improves real-world load speed and the metrics search engines use for ranking signals.",
            estimated_effort=Effort.HIGH,
            evidence=Evidence(observed_value=score, expected_value=">=80"),
        )


def _check_core_web_vitals(b: CategoryBuilder, lh: LighthouseRun) -> None:
    if lh.metrics is None:
        for key, label, *_ in _LIGHTHOUSE_METRIC_THRESHOLDS:
            b.unavailable(f"metric:{key}", label, "no_metrics_in_report")
        return
    for key, label, threshold, unit, severity in _LIGHTHOUSE_METRIC_THRESHOLDS:
        metric: MetricResult = getattr(lh.metrics, key)
        if not metric.available or metric.value is None:
            b.unavailable(f"metric:{key}", label, metric.reason or "unavailable")
            continue
        value = float(metric.value)
        if value <= threshold:
            b.passed(f"metric:{key}", label, detail=f"{value}{unit}")
        else:
            b.failed(
                f"metric:{key}", label,
                title=f"{label} exceeds the recommended threshold ({value}{unit} vs {threshold}{unit})",
                description=f"Measured by Lighthouse on the desktop run: {value}{unit}, recommended threshold is {threshold}{unit}.",
                severity=severity,
                priority=derive_priority(severity),
                impact=_impact_for_metric(key),
                recommendation=_recommendation_for_metric(key),
                how_to_fix=_how_to_fix_for_metric(key),
                expected_benefit="Improves this specific Core Web Vital, which directly affects perceived load speed.",
                estimated_effort=Effort.MEDIUM,
                evidence=Evidence(observed_value=value, expected_value=f"<= {threshold}{unit}"),
            )


def _impact_for_metric(key: str) -> str:
    return {
        "largest_contentful_paint": "Slow LCP means visitors wait longer to see the page's main content, a leading cause of bounce on slow connections.",
        "first_contentful_paint": "Slow FCP delays the very first visual feedback that the page is loading at all.",
        "cumulative_layout_shift": "High CLS means visible content jumps around as the page loads, which can cause mis-clicks and feels unpolished.",
        "total_blocking_time": "High TBT means the main thread is busy for long stretches, delaying how quickly the page responds to input.",
    }.get(key, "Affects perceived page performance.")


def _recommendation_for_metric(key: str) -> str:
    return {
        "largest_contentful_paint": "Optimize the largest above-the-fold element (usually a hero image or heading) — compress/resize images, preload the LCP resource, and remove render-blocking resources above it.",
        "first_contentful_paint": "Reduce render-blocking CSS/JS and ensure the server responds quickly (check Time to First Byte).",
        "cumulative_layout_shift": "Add explicit width/height (or aspect-ratio) to images and embeds, and avoid injecting content above existing content after load.",
        "total_blocking_time": "Break up long JavaScript tasks, defer non-critical scripts, and reduce third-party script weight.",
    }.get(key, "Review the full Lighthouse report for specific opportunities.")


def _how_to_fix_for_metric(key: str) -> list[str]:
    return {
        "largest_contentful_paint": ["Identify the LCP element in the Lighthouse report.", "Compress/resize its image (if applicable) and serve a modern format (WebP/AVIF).", "Preload the LCP resource and remove render-blocking CSS/JS before it."],
        "first_contentful_paint": ["Inline critical CSS or reduce its size.", "Defer non-critical JavaScript.", "Check server response time (Time to First Byte)."],
        "cumulative_layout_shift": ["Add width/height or aspect-ratio to all images, video, and embeds.", "Reserve space for ads/embeds that load asynchronously.", "Avoid injecting banners above existing content after initial load."],
        "total_blocking_time": ["Split long JavaScript tasks into smaller chunks.", "Defer or lazy-load non-critical third-party scripts.", "Remove unused JavaScript."],
    }.get(key, ["Review the full Lighthouse diagnostics for this metric."])


def _check_response_time(b: CategoryBuilder, scan: ScanResults) -> None:
    rt = scan.load_timing.response_time_ms
    if rt is None:
        b.unavailable("response_time", "Initial response time under 1s", "not_measured")
        return
    if rt <= 1000:
        b.passed("response_time", "Initial response time under 1s", detail=f"{rt:.0f}ms")
    else:
        severity = Severity.HIGH if rt > 3000 else Severity.MEDIUM
        b.failed(
            "response_time", "Initial response time under 1s",
            title=f"Slow initial server response ({rt:.0f}ms)",
            description="Time from navigation start to the main document response, measured during this scan.",
            severity=severity,
            priority=derive_priority(severity),
            impact="A slow server response delays everything downstream — the browser can't start rendering until this completes.",
            recommendation="Investigate server/backend response time: database query performance, server-side rendering cost, or hosting capacity.",
            how_to_fix=["Profile the server-side request handling for this page.", "Check for slow database queries or uncached expensive computations.", "Consider a CDN or edge caching for static/cacheable responses."],
            expected_benefit="Faster responses benefit every subsequent load-time metric.",
            estimated_effort=Effort.MEDIUM,
            evidence=Evidence(observed_value=round(rt), expected_value="<=1000ms"),
        )


def _check_resource_weight(b: CategoryBuilder, scan: ScanResults) -> None:
    tech = scan.extracted.technical if scan.extracted else None
    if tech is None:
        b.unavailable("resource_count", "Reasonable script/stylesheet count", "no_extracted_data")
        return
    total = tech.script_count + tech.stylesheet_count
    if total <= 40:
        b.passed("resource_count", "Reasonable script/stylesheet count", detail=f"{total} total")
    else:
        b.failed(
            "resource_count", "Reasonable script/stylesheet count",
            title=f"High number of script/stylesheet requests ({total})",
            description=f"{tech.script_count} scripts and {tech.stylesheet_count} stylesheets were loaded for this single page.",
            severity=Severity.MEDIUM,
            priority=derive_priority(Severity.MEDIUM),
            impact="Each additional request adds connection/parse overhead, compounding load time, especially on slower connections.",
            recommendation="Bundle and minify scripts/stylesheets, and audit for third-party scripts that aren't earning their cost.",
            how_to_fix=["Review the list of loaded scripts/stylesheets for duplicates or unused libraries.", "Bundle first-party assets with a build tool.", "Audit third-party scripts (analytics, widgets) and remove any that aren't actively used."],
            expected_benefit="Reduces request overhead and parse/execution time.",
            estimated_effort=Effort.MEDIUM,
            evidence=Evidence(observed_value=total, expected_value="<=40", extra={"scripts": tech.script_count, "stylesheets": tech.stylesheet_count}),
        )


def _check_failed_requests(b: CategoryBuilder, scan: ScanResults) -> None:
    tech = scan.extracted.technical if scan.extracted else None
    if tech is None:
        b.unavailable("no_failed_resource_requests", "No failed resource requests during load", "no_extracted_data")
        return
    if len(tech.failed_requests) == 0:
        b.passed("no_failed_resource_requests", "No failed resource requests during load")
    else:
        examples = [f"{r.method} {r.url}" for r in tech.failed_requests[:5]]
        b.failed(
            "no_failed_resource_requests", "No failed resource requests during load",
            title=f"{len(tech.failed_requests)} resource request(s) failed during page load",
            description="One or more scripts, stylesheets, images, or other resources failed to load.",
            severity=Severity.MEDIUM,
            priority=derive_priority(Severity.MEDIUM),
            impact="A failed resource can break functionality (a script that never runs) or degrade appearance (a missing stylesheet/image), and wastes the browser's time retrying/erroring.",
            recommendation="Fix or remove references to the failing resources.",
            how_to_fix=[f"Investigate these failed requests: {', '.join(examples)}.", "Fix the broken URL, or remove the reference if the resource is no longer needed."],
            expected_benefit="Restores intended functionality/appearance and removes wasted load time on failed requests.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(observed_value=examples, extra={"total_failed": len(tech.failed_requests)}),
        )
