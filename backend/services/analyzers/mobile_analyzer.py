"""Mobile Responsiveness (10%) — viewport configuration, horizontal overflow, and touch-target
sizing, all measured on the real mobile viewport Phase 2 renders (390x844, iPhone UA). Image
quality/optimization is owned by the UI Design module (which has it explicitly in its own
bullet list) to avoid raising the same broken/oversized-image finding twice under two
categories."""

from __future__ import annotations

from models.evaluation_models import CategoryResult, Effort, Evidence, Priority, Severity
from models.scan_models import ScanResults
from services.analyzers.base import CategoryBuilder
from services.severity_engine import derive_priority


def analyze(scan: ScanResults) -> CategoryResult:
    url = scan.response.final_url or scan.submitted_url
    b = CategoryBuilder("mobile", url)

    if scan.extracted is None:
        b.unavailable("page_extraction", "Page content extraction", "scan_has_no_extracted_data")
        return b.build("Could not evaluate mobile responsiveness — this scan has no extracted page data.")

    _check_viewport_meta(b, scan)
    _check_horizontal_overflow(b, scan)
    _check_touch_targets(b, scan)
    _check_mobile_screenshot(b, scan)

    summary = (
        f"Mobile responsiveness analysis found {b.issue_count} issue(s) across viewport "
        "configuration, layout overflow, and touch-target sizing."
        if b.issue_count
        else "No mobile responsiveness issues detected across viewport configuration, layout overflow, and touch-target sizing."
    )
    return b.build(summary)


def _check_viewport_meta(b: CategoryBuilder, scan: ScanResults) -> None:
    ux = scan.extracted.ux
    if ux.has_viewport_meta:
        content = ux.viewport_content or ""
        if "width=device-width" in content.replace(" ", ""):
            b.passed("viewport_meta", "Responsive viewport meta tag configured", detail=content)
        else:
            b.failed(
                "viewport_meta", "Responsive viewport meta tag configured",
                title="Viewport meta tag present but not responsive",
                description=f"The viewport tag's content is '{content}', which doesn't include width=device-width.",
                severity=Severity.HIGH,
                priority=derive_priority(Severity.HIGH),
                impact="Mobile browsers may render at a fixed width instead of adapting to the device's screen.",
                recommendation="Update the viewport content to include width=device-width, initial-scale=1.",
                how_to_fix=["Change the <meta name=\"viewport\"> content attribute to \"width=device-width, initial-scale=1\"."],
                expected_benefit="Ensures the page renders at the correct scale on mobile devices.",
                estimated_effort=Effort.LOW,
                evidence=Evidence(element="meta[name=viewport]", observed_value=content, expected_value="width=device-width, initial-scale=1"),
            )
    else:
        b.failed(
            "viewport_meta", "Responsive viewport meta tag configured",
            title="Missing viewport meta tag",
            description="No <meta name=\"viewport\"> tag was found.",
            severity=Severity.CRITICAL,
            priority=derive_priority(Severity.CRITICAL),
            impact="Without this tag, mobile browsers render the page at desktop width and shrink it down, making text unreadably small without zooming.",
            recommendation="Add a responsive viewport meta tag.",
            how_to_fix=["Add <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"> inside <head>."],
            expected_benefit="Makes the page render at a legible, correctly-scaled size on mobile devices.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(element="meta[name=viewport]", observed_value=None),
        )


def _check_horizontal_overflow(b: CategoryBuilder, scan: ScanResults) -> None:
    overflow = scan.extracted.ux.horizontal_overflow
    if overflow is None:
        b.unavailable("horizontal_overflow", "No horizontal overflow on load", "overflow_measurement_unavailable")
        return
    if overflow:
        b.failed(
            "horizontal_overflow", "No horizontal overflow on load",
            title="Page has horizontal overflow",
            description="The page's content is wider than the viewport, causing horizontal scrolling.",
            severity=Severity.HIGH,
            priority=derive_priority(Severity.HIGH),
            impact="Forces users to scroll sideways to read content — one of the most common real-world mobile usability complaints.",
            recommendation="Find the element(s) wider than the viewport (often a fixed-width container, table, or unconstrained image) and constrain them.",
            how_to_fix=[
                "Open the page in a mobile-width viewport and use browser dev tools to identify the overflowing element.",
                "Add max-width: 100% (or a responsive container width) to the offending element.",
                "Re-check that no fixed pixel widths exceed the smallest supported viewport.",
            ],
            expected_benefit="Removes horizontal scrolling, a significant mobile usability improvement.",
            estimated_effort=Effort.MEDIUM,
            evidence=Evidence(observed_value=True, expected_value=False),
        )
    else:
        b.passed("horizontal_overflow", "No horizontal overflow on load")


def _check_touch_targets(b: CategoryBuilder, scan: ScanResults) -> None:
    extras = scan.audit_extras
    if extras is None or not extras.touch_targets.available:
        reason = "scan_predates_phase3_evidence_capture" if extras is None else (extras.touch_targets.reason or "unavailable")
        b.unavailable("touch_target_size", "Interactive elements meet minimum touch-target size", reason)
        return

    tt = extras.touch_targets
    if tt.total_checked == 0:
        b.unavailable("touch_target_size", "Interactive elements meet minimum touch-target size", "no_interactive_elements_found")
        return
    if tt.undersized_count == 0:
        b.passed("touch_target_size", "Interactive elements meet minimum touch-target size", detail=f"0 of {tt.total_checked} undersized")
        return

    ratio = tt.undersized_count / tt.total_checked
    severity = Severity.HIGH if ratio > 0.3 else Severity.MEDIUM
    b.failed(
        "touch_target_size", "Interactive elements meet minimum touch-target size",
        title=f"{tt.undersized_count} of {tt.total_checked} interactive elements are smaller than the recommended touch-target size",
        description="Measured on the real mobile viewport: these elements render under the commonly recommended 44x44 CSS px minimum.",
        severity=severity,
        priority=derive_priority(severity),
        impact="Small touch targets are harder to tap accurately, especially for users with larger fingers or motor impairments.",
        recommendation="Increase padding or min-width/min-height on undersized interactive elements to at least 44x44 CSS px.",
        how_to_fix=[
            f"Review the flagged elements, for example: {', '.join(tt.undersized_examples) or 'see evidence'}.",
            "Increase padding, or set an explicit min-width/min-height of 44px, on each.",
            "Re-test on the mobile viewport to confirm the new size.",
        ],
        expected_benefit="Reduces mis-taps and improves usability for all mobile users.",
        estimated_effort=Effort.MEDIUM,
        evidence=Evidence(observed_value=tt.undersized_examples, expected_value="min 44x44 CSS px", extra={"undersized_count": tt.undersized_count, "total_checked": tt.total_checked}),
    )


def _check_mobile_screenshot(b: CategoryBuilder, scan: ScanResults) -> None:
    mobile_shot = scan.screenshots.get("mobile")
    if mobile_shot and mobile_shot.available:
        b.passed("mobile_render", "Page renders successfully on a mobile viewport")
    else:
        reason = mobile_shot.reason if mobile_shot else "no_mobile_screenshot_captured"
        b.failed(
            "mobile_render", "Page renders successfully on a mobile viewport",
            title="Page failed to render on a mobile viewport",
            description=f"The mobile-viewport scan did not complete successfully: {reason}",
            severity=Severity.CRITICAL,
            priority=derive_priority(Severity.CRITICAL),
            impact="If the page doesn't render at all on a mobile viewport, it's entirely unusable for mobile visitors.",
            recommendation="Investigate why the page fails to load on a mobile viewport/user agent — check for mobile-specific redirects, blocking scripts, or errors.",
            how_to_fix=["Load the page with a mobile viewport and user agent locally.", "Check the browser console for errors specific to that rendering path."],
            expected_benefit="Restores basic mobile usability.",
            estimated_effort=Effort.HIGH,
            evidence=Evidence(observed_value=reason),
        )


