from __future__ import annotations

from models.evaluation_models import Effort, Priority, Recommendation, RecommendationBucket
from services.analyzers import accessibility_analyzer, seo_analyzer
from services.recommendation_engine import classify_recommendation, collect_recommendations
from tests.conftest import make_scan_results


def _rec(priority: Priority, effort: Effort) -> Recommendation:
    return Recommendation(
        issue_id="SEO-001", category="seo", title="t", what_to_fix="w", why_it_matters="why",
        how_to_fix=["step"], expected_benefit="benefit", priority=priority, estimated_effort=effort,
        affected_url="https://example.test/",
    )


def test_p0_is_always_a_critical_fix_regardless_of_effort():
    assert classify_recommendation(_rec(Priority.P0, Effort.HIGH)) == RecommendationBucket.CRITICAL_FIX
    assert classify_recommendation(_rec(Priority.P1, Effort.LOW)) == RecommendationBucket.CRITICAL_FIX


def test_low_effort_non_critical_is_a_quick_win():
    assert classify_recommendation(_rec(Priority.P2, Effort.LOW)) == RecommendationBucket.QUICK_WIN
    assert classify_recommendation(_rec(Priority.P3, Effort.LOW)) == RecommendationBucket.QUICK_WIN


def test_higher_effort_non_critical_is_long_term():
    assert classify_recommendation(_rec(Priority.P2, Effort.MEDIUM)) == RecommendationBucket.LONG_TERM
    assert classify_recommendation(_rec(Priority.P3, Effort.HIGH)) == RecommendationBucket.LONG_TERM


def test_collect_recommendations_assigns_bucket():
    scan = make_scan_results(title=None)  # missing title -> P1, LOW effort -> critical fix
    result = seo_analyzer.analyze(scan)
    recs = collect_recommendations({"seo": result})
    title_rec = next(r for r in recs if r.issue_id == next(i.issue_id for i in result.issues if "title" in i.title.lower()))
    assert title_rec.bucket == RecommendationBucket.CRITICAL_FIX


def test_recommendation_root_cause_matches_issue_description():
    scan = make_scan_results(title=None)
    result = seo_analyzer.analyze(scan)
    issue = next(i for i in result.issues if i.evidence.extra.get("check_id") == "title_present")
    rec = next(r for r in result.recommendations if r.issue_id == issue.issue_id)
    assert rec.root_cause == issue.description


def test_axe_recommendation_carries_documentation_url():
    from models.scan_models import AccessibilityAudit, AxeViolation, AxeViolationNode

    scan = make_scan_results()
    scan.audit_extras.accessibility = AccessibilityAudit(
        available=True,
        violations=[
            AxeViolation(
                rule_id="image-alt", impact="serious", description="d", help_text="h",
                help_url="https://dequeuniversity.com/rules/axe/image-alt", tags=[],
                nodes=[AxeViolationNode(selector="img")],
            )
        ],
        passed_rule_ids=[], passes_count=0, incomplete_count=0,
    )
    result = accessibility_analyzer.analyze(scan)
    rec = next(r for r in result.recommendations if r.issue_id.startswith("ACCESSIBILITY"))
    assert rec.documentation_url == "https://dequeuniversity.com/rules/axe/image-alt"
