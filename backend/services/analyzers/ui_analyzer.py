"""UI & Visual Design Evaluation (12%) — typography consistency and image quality, both real
computed-style/DOM measurements captured in the same Playwright session (see
`scanner/page_diagnostics.py`). Color contrast is owned by the Accessibility module (axe-core's
own `color-contrast` rule is the actual check; re-deriving it here would duplicate that finding
under a second category). Several bullets from the brief — subjective visual hierarchy quality,
"visual clutter," spacing/alignment rhythm, button-styling consistency beyond typography — have
no automatable, evidence-based check available from what Phase 2 captures, and are reported as
`unavailable` rather than scored by guesswork; see each check's `reason` for specifics."""

from __future__ import annotations

from models.evaluation_models import CategoryResult, Effort, Evidence, Priority, Severity
from models.scan_models import ScanResults
from services.analyzers.base import CategoryBuilder
from services.severity_engine import derive_priority

_UNAUTOMATABLE_CHECKS = [
    ("visual_hierarchy_quality", "Visual hierarchy quality", "subjective_design_judgment_not_automatable"),
    ("visual_clutter", "Visual clutter / information density", "requires_human_design_review_not_automatable"),
    ("spacing_alignment_rhythm", "Spacing and alignment consistency", "requires_cross_page_design_system_baseline_not_available"),
    ("button_styling_consistency", "Button styling consistency", "requires_human_design_review_not_automatable"),
]


def analyze(scan: ScanResults) -> CategoryResult:
    url = scan.response.final_url or scan.submitted_url
    b = CategoryBuilder("ui", url)

    _check_typography(b, scan)
    _check_broken_images(b, scan)
    _check_oversized_images(b, scan)
    b.unavailable("color_contrast", "Color contrast", "covered_under_accessibility_module_via_axe_core_color_contrast_rule")

    for check_id, label, reason in _UNAUTOMATABLE_CHECKS:
        b.unavailable(check_id, label, reason)

    summary = (
        f"UI analysis found {b.issue_count} issue(s) in the automatable checks (typography, "
        "image quality). Several subjective design-quality checks (visual hierarchy, clutter, "
        "spacing rhythm) have no automated equivalent and are marked unavailable rather than guessed."
        if b.issue_count
        else "No issues detected in the automatable UI checks (typography, image quality); several "
        "subjective design-quality checks have no automated equivalent and are marked unavailable."
    )
    return b.build(summary)


def _check_typography(b: CategoryBuilder, scan: ScanResults) -> None:
    extras = scan.audit_extras
    if extras is None or not extras.typography.available:
        reason = "scan_predates_phase3_evidence_capture" if extras is None else (extras.typography.reason or "unavailable")
        b.unavailable("font_family_consistency", "Limited number of distinct font families", reason)
        b.unavailable("font_size_consistency", "Limited number of distinct font sizes", reason)
        return

    typo = extras.typography
    families = typo.distinct_font_families or 0
    if families <= 3:
        b.passed("font_family_consistency", "Limited number of distinct font families", detail=f"{families} distinct families")
    else:
        b.failed(
            "font_family_consistency", "Limited number of distinct font families",
            title=f"{families} distinct font families detected in sampled text",
            description=f"Sampled visible text uses: {', '.join(typo.font_family_samples)}.",
            severity=Severity.LOW,
            priority=derive_priority(Severity.LOW),
            impact="Too many font families in one design tends to read as inconsistent and can slow page load (more font files).",
            recommendation="Consolidate to 2-3 font families (e.g. one for headings, one for body, optionally one for monospace/code).",
            how_to_fix=["Audit where each detected font family is used.", "Standardize on 2-3 families across the site's type scale.", "Update stylesheets/design tokens accordingly."],
            expected_benefit="More consistent, intentional typographic system and fewer font files to load.",
            estimated_effort=Effort.MEDIUM,
            evidence=Evidence(observed_value=typo.font_family_samples, expected_value="<=3 families"),
        )

    sizes = typo.distinct_font_sizes or 0
    if sizes <= 8:
        b.passed("font_size_consistency", "Limited number of distinct font sizes", detail=f"{sizes} distinct sizes")
    else:
        b.failed(
            "font_size_consistency", "Limited number of distinct font sizes",
            title=f"{sizes} distinct font sizes detected in sampled text",
            description="A large number of distinct computed font-size values suggests the page isn't using a constrained type scale.",
            severity=Severity.LOW,
            priority=derive_priority(Severity.LOW),
            impact="An unconstrained type scale tends to look inconsistent and makes the visual hierarchy harder to read at a glance.",
            recommendation="Define a fixed type scale (e.g. 6-8 sizes) and migrate components to use it.",
            how_to_fix=["Audit where font sizes diverge from a clean scale.", "Define a small, fixed set of font-size tokens.", "Migrate one-off sizes to the nearest scale step."],
            expected_benefit="Clearer, more consistent visual hierarchy.",
            estimated_effort=Effort.MEDIUM,
            evidence=Evidence(observed_value=sizes, expected_value="<=8 sizes"),
        )


def _check_broken_images(b: CategoryBuilder, scan: ScanResults) -> None:
    extras = scan.audit_extras
    if extras is None or not extras.images.available:
        reason = "scan_predates_phase3_evidence_capture" if extras is None else (extras.images.reason or "unavailable")
        b.unavailable("no_broken_images", "No broken images", reason)
        return
    images = extras.images
    if images.total_checked == 0:
        b.unavailable("no_broken_images", "No broken images", "no_images_on_page")
        return
    if images.broken_count == 0:
        b.passed("no_broken_images", "No broken images", detail=f"0 of {images.total_checked} broken")
    else:
        b.failed(
            "no_broken_images", "No broken images",
            title=f"{images.broken_count} of {images.total_checked} images failed to load",
            description="One or more <img> elements had zero natural dimensions after load, indicating a broken image reference.",
            severity=Severity.HIGH,
            priority=derive_priority(Severity.HIGH),
            impact="Broken images look unprofessional and, if the image carried information, that information is lost to visitors.",
            recommendation="Fix or replace the broken image references.",
            how_to_fix=[f"Check these image sources: {', '.join(images.broken_examples) or 'see evidence'}.", "Confirm the file exists at that path and is served with a successful status code."],
            expected_benefit="Restores the intended visual content.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(selector="img", observed_value=images.broken_examples, extra={"broken_count": images.broken_count, "total": images.total_checked}),
        )


def _check_oversized_images(b: CategoryBuilder, scan: ScanResults) -> None:
    extras = scan.audit_extras
    if extras is None or not extras.images.available:
        return  # already reported as unavailable by _check_broken_images for the same reason
    images = extras.images
    if images.total_checked == 0:
        return
    if images.oversized_count == 0:
        b.passed("images_not_oversized", "Images not significantly larger than their displayed size")
    else:
        b.failed(
            "images_not_oversized", "Images not significantly larger than their displayed size",
            title=f"{images.oversized_count} image(s) are more than 2.5x larger than their displayed size",
            description="These images' natural resolution is much higher than the size they're actually rendered at on the page.",
            severity=Severity.MEDIUM,
            priority=derive_priority(Severity.MEDIUM),
            impact="Serving an oversized image wastes bandwidth and slows page load for no visual benefit beyond the rendered size.",
            recommendation="Resize or use responsive image techniques (srcset/sizes, or a resizing CDN) to serve images closer to their displayed size.",
            how_to_fix=["Identify the oversized images flagged in evidence.", "Resize the source file closer to its rendered dimensions, or serve a responsive srcset.", "Re-check after the change."],
            expected_benefit="Reduces page weight and improves load performance.",
            estimated_effort=Effort.MEDIUM,
            evidence=Evidence(observed_value=images.oversized_count, extra={"total": images.total_checked}),
        )
