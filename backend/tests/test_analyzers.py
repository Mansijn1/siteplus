from __future__ import annotations

from models.evaluation_models import CheckStatus, Severity
from models.scan_models import (
    AccessibilityAudit,
    AxeViolation,
    AxeViolationNode,
    LayoutSignal,
    MixedContentInfo,
    RobotsSitemapInfo,
    TouchTargetSignal,
)
from services.analyzers import (
    accessibility_analyzer,
    content_analyzer,
    mobile_analyzer,
    performance_analyzer,
    security_analyzer,
    seo_analyzer,
    technical_analyzer,
    trust_analyzer,
    ui_analyzer,
    ux_analyzer,
)
from services.recommendation_engine import collect_recommendations
from tests.conftest import make_scan_results


def _check(result, check_id: str):
    return next(c for c in result.checks if c.check_id == check_id)


# ---- SEO ----

def test_seo_missing_title_is_flagged_high_severity():
    scan = make_scan_results(title=None)
    result = seo_analyzer.analyze(scan)
    assert _check(result, "title_present").status == CheckStatus.FAILED
    issue = next(i for i in result.issues if i.issue_id.startswith("SEO") and "title" in i.title.lower())
    assert issue.severity == Severity.HIGH


def test_seo_missing_meta_description_is_flagged():
    scan = make_scan_results(meta_description=None)
    result = seo_analyzer.analyze(scan)
    assert _check(result, "meta_description_present").status == CheckStatus.FAILED


def test_seo_healthy_page_has_no_issues_in_core_checks():
    scan = make_scan_results()
    result = seo_analyzer.analyze(scan)
    for check_id in ("title_present", "meta_description_present", "canonical_present", "single_h1"):
        assert _check(result, check_id).status == CheckStatus.PASSED


def test_seo_missing_alt_text_severity_scales_with_ratio():
    low_ratio = seo_analyzer.analyze(make_scan_results(images_total=10, images_missing_alt=1))
    high_ratio = seo_analyzer.analyze(make_scan_results(images_total=10, images_missing_alt=8))
    low_issue = next(i for i in low_ratio.issues if "alt" in i.title.lower())
    high_issue = next(i for i in high_ratio.issues if "alt" in i.title.lower())
    assert low_issue.severity == Severity.MEDIUM
    assert high_issue.severity == Severity.HIGH


def test_seo_noindex_is_critical():
    scan = make_scan_results(meta_robots="noindex, nofollow")
    result = seo_analyzer.analyze(scan)
    issue = next(i for i in result.issues if "noindex" in i.title.lower())
    assert issue.severity == Severity.CRITICAL


def test_seo_robots_disallow_all_detected():
    scan = make_scan_results()
    scan.audit_extras.robots_sitemap = RobotsSitemapInfo(
        available=True, robots_txt_present=True, robots_txt_status=200,
        robots_txt_disallow_all=True, sitemap_declared_in_robots=False,
        sitemap_xml_present=False, sitemap_xml_status=404,
    )
    result = seo_analyzer.analyze(scan)
    assert _check(result, "robots_txt_not_disallow_all").status == CheckStatus.FAILED


# ---- Accessibility ----

def test_accessibility_axe_violation_maps_impact_to_severity():
    scan = make_scan_results()
    scan.audit_extras.accessibility = AccessibilityAudit(
        available=True,
        violations=[
            AxeViolation(
                rule_id="image-alt", impact="critical", description="Images must have alt text",
                help_text="Add alt attributes", help_url="https://example.com/rule",
                tags=["wcag2a"], nodes=[AxeViolationNode(selector="img.hero")],
            )
        ],
        passed_rule_ids=["label"], passes_count=1, incomplete_count=0,
    )
    result = accessibility_analyzer.analyze(scan)
    issue = next(i for i in result.issues if i.evidence.extra.get("rule_id") == "image-alt")
    assert issue.severity == Severity.CRITICAL


def test_accessibility_unavailable_when_axe_did_not_run():
    scan = make_scan_results()
    scan.audit_extras.accessibility = AccessibilityAudit(available=False, reason="axe_core_not_vendored")
    result = accessibility_analyzer.analyze(scan)
    assert _check(result, "axe_core_audit").status == CheckStatus.UNAVAILABLE


def test_accessibility_missing_lang_attribute_flagged():
    scan = make_scan_results(language=None)
    result = accessibility_analyzer.analyze(scan)
    assert _check(result, "html_lang_attribute").status == CheckStatus.FAILED


# ---- Mobile ----

def test_mobile_missing_viewport_is_critical():
    scan = make_scan_results(has_viewport_meta=False, viewport_content=None)
    result = mobile_analyzer.analyze(scan)
    issue = next(i for i in result.issues if "viewport" in i.title.lower())
    assert issue.severity == Severity.CRITICAL


def test_mobile_horizontal_overflow_flagged():
    scan = make_scan_results(horizontal_overflow=True)
    result = mobile_analyzer.analyze(scan)
    assert _check(result, "horizontal_overflow").status == CheckStatus.FAILED


def test_mobile_undersized_touch_targets_flagged():
    scan = make_scan_results()
    scan.audit_extras.touch_targets = TouchTargetSignal(
        available=True, total_checked=10, undersized_count=4, undersized_examples=["A:Menu"]
    )
    result = mobile_analyzer.analyze(scan)
    assert _check(result, "touch_target_size").status == CheckStatus.FAILED


def test_mobile_healthy_viewport_passes():
    scan = make_scan_results()
    result = mobile_analyzer.analyze(scan)
    assert _check(result, "viewport_meta").status == CheckStatus.PASSED


# ---- Security ----

def test_security_plain_http_is_critical():
    scan = make_scan_results(https=False)
    result = security_analyzer.analyze(scan)
    issue = next(i for i in result.issues if "https" in i.title.lower())
    assert issue.severity == Severity.CRITICAL


def test_security_missing_header_detected():
    scan = make_scan_results(response_headers={"content-type": "text/html"})
    result = security_analyzer.analyze(scan)
    assert _check(result, "header:strict-transport-security").status == CheckStatus.FAILED
    assert _check(result, "header:content-security-policy").status == CheckStatus.FAILED


def test_security_all_headers_present_passes():
    scan = make_scan_results()
    result = security_analyzer.analyze(scan)
    assert _check(result, "header:strict-transport-security").status == CheckStatus.PASSED


def test_security_mixed_content_detected():
    scan = make_scan_results()
    scan.audit_extras.mixed_content = MixedContentInfo(
        available=True, insecure_resource_count=2, insecure_resource_examples=["http://cdn.example/a.js"]
    )
    result = security_analyzer.analyze(scan)
    assert _check(result, "no_mixed_content").status == CheckStatus.FAILED


# ---- Technical ----

def test_technical_non_2xx_status_is_critical():
    scan = make_scan_results(status_code=500)
    result = technical_analyzer.analyze(scan)
    issue = next(i for i in result.issues if "500" in i.title)
    assert issue.severity == Severity.CRITICAL


def test_technical_long_redirect_chain_flagged():
    scan = make_scan_results(redirect_chain=["https://example.test/a", "https://example.test/b"])
    result = technical_analyzer.analyze(scan)
    assert _check(result, "redirect_chain_minimal").status == CheckStatus.FAILED


# ---- Content ----

def test_content_thin_content_flagged():
    scan = make_scan_results(word_count=20)
    result = content_analyzer.analyze(scan)
    assert _check(result, "sufficient_content_length").status == CheckStatus.FAILED


def test_content_duplicate_headings_flagged():
    scan = make_scan_results(duplicate_headings=["welcome"])
    result = content_analyzer.analyze(scan)
    assert _check(result, "no_duplicate_headings").status == CheckStatus.FAILED


# ---- UX ----

def test_ux_console_errors_flagged():
    from models.scan_models import ConsoleMessage

    scan = make_scan_results(console_messages=[ConsoleMessage(type="error", text="TypeError: x is not a function")])
    result = ux_analyzer.analyze(scan)
    assert _check(result, "no_js_console_errors").status == CheckStatus.FAILED


def test_ux_no_nav_flagged():
    scan = make_scan_results(nav_elements=0)
    result = ux_analyzer.analyze(scan)
    assert _check(result, "navigation_landmark_present").status == CheckStatus.FAILED


# ---- Missing / incomplete scan data must degrade to unavailable, never crash ----

def test_analyzers_handle_missing_extracted_data_without_crashing():
    scan = make_scan_results(extracted=None, audit_extras=None)
    for analyze_fn in (seo_analyzer.analyze, content_analyzer.analyze, ux_analyzer.analyze, trust_analyzer.analyze):
        result = analyze_fn(scan)
        assert result.score is None
        assert all(c.status == CheckStatus.UNAVAILABLE for c in result.checks)


def test_analyzers_handle_missing_audit_extras_gracefully():
    scan = make_scan_results(audit_extras=None)
    result = accessibility_analyzer.analyze(scan)
    assert _check(result, "axe_core_audit").status == CheckStatus.UNAVAILABLE
    assert _check(result, "axe_core_audit").detail == "scan_predates_phase3_evidence_capture"


# ---- Duplicate issue prevention ----

def test_recommendation_engine_dedupes_by_issue_id():
    scan = make_scan_results(meta_robots="noindex")
    result = seo_analyzer.analyze(scan)
    categories = {"seo": result, "seo_dupe": result}  # simulate the same recs appearing twice
    recs = collect_recommendations(categories)
    issue_ids = [r.issue_id for r in recs]
    assert len(issue_ids) == len(set(issue_ids))


# ---- UI: layout/alignment signal (Phase 4) ----


def test_ui_heading_size_inversion_flagged():
    scan = make_scan_results()
    scan.audit_extras.layout = LayoutSignal(available=True, heading_hierarchy_sizes_ok=False, distinct_left_edges=2)
    result = ui_analyzer.analyze(scan)
    assert _check(result, "heading_size_hierarchy").status == CheckStatus.FAILED


def test_ui_inconsistent_alignment_flagged():
    scan = make_scan_results()
    scan.audit_extras.layout = LayoutSignal(available=True, heading_hierarchy_sizes_ok=True, distinct_left_edges=9)
    result = ui_analyzer.analyze(scan)
    assert _check(result, "alignment_consistency").status == CheckStatus.FAILED


def test_ui_layout_unavailable_degrades_gracefully():
    scan = make_scan_results()
    scan.audit_extras.layout = LayoutSignal(available=False, reason="evaluate_failed")
    result = ui_analyzer.analyze(scan)
    assert _check(result, "heading_size_hierarchy").status == CheckStatus.UNAVAILABLE


# ---- SEO: structured data (Phase 4) ----


def test_seo_missing_structured_data_flagged():
    result = seo_analyzer.analyze(make_scan_results())  # default fixture has no JSON-LD
    assert _check(result, "structured_data_present").status == CheckStatus.FAILED


def test_no_analyzer_ever_reports_unavailable_as_failed_or_passed():
    # The "never treat unavailable data as a confirmed failure" rule, checked mechanically:
    # every check must be exactly one of the three statuses, and unavailable checks must carry
    # a reason in `detail` (not a None).
    scan = make_scan_results()
    for analyze_fn in (seo_analyzer.analyze, mobile_analyzer.analyze, security_analyzer.analyze):
        result = analyze_fn(scan)
        for check in result.checks:
            if check.status == CheckStatus.UNAVAILABLE:
                assert check.detail, f"{check.check_id} is unavailable with no reason"


def test_accessibility_same_rule_in_passes_and_violations_counts_as_failed_only():
    # Regression test: axe-core evaluates rules like color-contrast per-element, so the same
    # rule_id can appear in BOTH `passes` and `violations` on one page. Found by the benchmark
    # (benchmark/runner.py) as a real false negative before this fix.
    scan = make_scan_results()
    scan.audit_extras.accessibility = AccessibilityAudit(
        available=True,
        violations=[
            AxeViolation(
                rule_id="color-contrast", impact="serious", description="d", help_text="h",
                help_url=None, tags=[], nodes=[AxeViolationNode(selector=".low-contrast")],
            )
        ],
        passed_rule_ids=["color-contrast", "label"],  # same rule_id also reported as passed
        passes_count=2, incomplete_count=0,
    )
    result = accessibility_analyzer.analyze(scan)
    contrast_checks = [c for c in result.checks if c.check_id == "axe:color-contrast"]
    assert len(contrast_checks) == 1
    assert contrast_checks[0].status == CheckStatus.FAILED
