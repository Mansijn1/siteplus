"""Innovation & Modern Web Experience (2%) — the lowest-weighted and most inherently subjective
module. Per the spec, a minimal design must not be penalized for being minimal, so this module
checks only concrete, low-stakes PWA indicators (web app manifest, theme-color meta) and reports
everything genuinely subjective (animation/interaction quality, "modern" framework usage,
progressive enhancement testing) as unavailable rather than inventing a creativity score."""

from __future__ import annotations

from models.evaluation_models import CategoryResult, Effort, Evidence, Priority, Severity
from models.scan_models import ScanResults
from services.analyzers.base import CategoryBuilder
from services.severity_engine import derive_priority


def analyze(scan: ScanResults) -> CategoryResult:
    url = scan.response.final_url or scan.submitted_url
    b = CategoryBuilder("innovation", url)

    if scan.extracted is None:
        b.unavailable("page_extraction", "Page content extraction", "scan_has_no_extracted_data")
        return b.build("Could not evaluate innovation signals — this scan has no extracted page data.")

    signals = scan.extracted.page_signals

    if signals.has_manifest_link:
        b.passed("pwa_manifest_present", "Web app manifest linked")
    else:
        b.failed(
            "pwa_manifest_present", "Web app manifest linked",
            title="No web app manifest found",
            description="No <link rel=\"manifest\"> tag was found.",
            severity=Severity.INFORMATIONAL,
            priority=derive_priority(Severity.INFORMATIONAL),
            impact="A manifest is what enables 'Add to Home Screen'/installable-PWA behavior — optional for most sites, but a low-effort modernization signal.",
            recommendation="Consider adding a web app manifest if an installable/app-like experience would benefit this site.",
            how_to_fix=["Create a manifest.json with name, icons, and theme colors.", "Link it via <link rel=\"manifest\" href=\"/manifest.json\"> in <head>."],
            expected_benefit="Enables installable/app-like behavior in supporting browsers.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(element="link[rel=manifest]", observed_value=None),
        )

    if signals.has_theme_color_meta:
        b.passed("theme_color_configured", "Theme color meta tag configured")
    else:
        b.failed(
            "theme_color_configured", "Theme color meta tag configured",
            title="No theme-color meta tag found",
            description="No <meta name=\"theme-color\"> tag was found.",
            severity=Severity.INFORMATIONAL,
            priority=derive_priority(Severity.INFORMATIONAL),
            impact="theme-color lets mobile browsers tint their UI chrome to match the site's branding — a small polish detail, not a functional issue.",
            recommendation="Add a theme-color meta tag matching the site's brand color.",
            how_to_fix=["Add <meta name=\"theme-color\" content=\"#yourbrandcolor\"> inside <head>."],
            expected_benefit="Small branding/polish improvement on supporting mobile browsers.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(element="meta[name=theme-color]", observed_value=None),
        )

    b.unavailable("modern_interaction_patterns", "Modern interaction patterns in use", "subjective_design_judgment_not_automatable")
    b.unavailable("animation_interaction_quality", "Animation and interaction quality", "subjective_design_judgment_not_automatable")
    b.unavailable("progressive_enhancement", "Page functions reasonably with JavaScript disabled", "requires_dedicated_no_js_test_pass_out_of_scope_for_this_scan")

    summary = (
        f"Innovation analysis found {b.issue_count} low-stakes improvement(s); a minimal, well-executed design is not penalized here."
        if b.issue_count
        else "No issues in the automatable innovation checks; subjective creativity/polish judgments require manual review."
    )
    return b.build(summary)
