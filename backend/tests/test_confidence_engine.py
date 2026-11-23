from __future__ import annotations

from models.evaluation_models import (
    CategoryResult,
    ConfidenceLevel,
    Effort,
    Evidence,
    Issue,
    Priority,
    Severity,
    VerificationStatus,
)
from services.confidence_engine import verify_and_score
from services.validation_engine import validate_category_result


def _issue(check_id: str, **overrides) -> Issue:
    defaults = dict(
        issue_id="SEO-001",
        category="seo",
        title="Example issue",
        description="Example description",
        evidence=Evidence(selector="title", observed_value=None, extra={"check_id": check_id}),
        affected_url="https://example.test/",
        severity=Severity.HIGH,
        priority=Priority.P1,
        impact="Example impact",
        recommendation="Example recommendation",
        estimated_effort=Effort.LOW,
    )
    defaults.update(overrides)
    return Issue(**defaults)


def test_rendered_dom_check_gets_very_high_confidence():
    issue = verify_and_score(_issue("title_present"))
    assert issue.confidence_level == ConfidenceLevel.VERY_HIGH
    assert issue.verification_status == VerificationStatus.VERIFIED
    assert issue.evidence_source == "rendered_dom"


def test_heuristic_threshold_check_gets_medium_confidence_and_needs_review():
    issue = verify_and_score(_issue("touch_target_size"))
    assert issue.confidence_level == ConfidenceLevel.MEDIUM
    assert issue.verification_status == VerificationStatus.NEEDS_REVIEW
    assert issue.confidence < 0.90


def test_axe_violation_prefix_maps_to_external_tool():
    issue = verify_and_score(_issue("axe:color-contrast"))
    assert issue.evidence_source == "external_tool"
    assert issue.confidence_level == ConfidenceLevel.VERY_HIGH  # 0.90 is the VERY_HIGH boundary


def test_header_prefix_maps_to_http_response():
    issue = verify_and_score(_issue("header:strict-transport-security"))
    assert issue.evidence_source == "http_response"


def test_unmapped_check_id_defaults_to_conservative_confidence():
    issue = verify_and_score(_issue("some_future_check_nobody_classified_yet"))
    assert issue.evidence_source == "heuristic_threshold"
    assert issue.verification_status == VerificationStatus.NEEDS_REVIEW


def test_issue_with_no_concrete_evidence_is_downgraded_regardless_of_source():
    bare_evidence = Evidence(extra={"check_id": "title_present"})  # no selector/observed_value
    issue = verify_and_score(_issue("title_present", evidence=bare_evidence))
    assert issue.confidence <= 0.6
    assert issue.verification_status == VerificationStatus.NEEDS_REVIEW


def test_confidence_level_bands_match_spec_thresholds():
    from services.confidence_engine import _confidence_level

    assert _confidence_level(0.99) == ConfidenceLevel.VERY_HIGH
    assert _confidence_level(0.90) == ConfidenceLevel.VERY_HIGH
    assert _confidence_level(0.89) == ConfidenceLevel.HIGH
    assert _confidence_level(0.75) == ConfidenceLevel.HIGH
    assert _confidence_level(0.74) == ConfidenceLevel.MEDIUM
    assert _confidence_level(0.50) == ConfidenceLevel.MEDIUM
    assert _confidence_level(0.49) == ConfidenceLevel.LOW


def test_confidence_never_substitutes_for_severity():
    # A low-confidence finding can still be a critical-severity one — confidence and severity
    # are independent axes, exactly as the spec requires.
    issue = verify_and_score(_issue("touch_target_size", severity=Severity.CRITICAL, priority=Priority.P0))
    assert issue.severity == Severity.CRITICAL
    assert issue.confidence_level == ConfidenceLevel.MEDIUM


def _category_result(issues: list[Issue], passed_count: int = 5) -> CategoryResult:
    return CategoryResult(
        category="seo",
        weight=10,
        score=round(passed_count / (passed_count + len(issues)) * 100, 1) if issues else 100.0,
        checks=[],
        issues=issues,
        recommendations=[],
        passed_count=passed_count,
        failed_count=len(issues),
        unavailable_count=0,
        summary="test",
    )


def test_validate_category_result_dedupes_same_check_id():
    duplicate_a = _issue("title_present", issue_id="SEO-001")
    duplicate_b = _issue("title_present", issue_id="SEO-002")  # same check_id, different issue_id
    result = _category_result([duplicate_a, duplicate_b], passed_count=3)
    validated = validate_category_result(result)
    assert len(validated.issues) == 1
    assert validated.failed_count == 1
    # score recomputed against the deduplicated count: 3 passed / (3 passed + 1 failed) = 75.0
    assert validated.score == 75.0


def test_validate_category_result_applies_confidence_to_every_issue():
    result = _category_result([_issue("title_present"), _issue("touch_target_size", issue_id="SEO-002")])
    validated = validate_category_result(result)
    levels = {i.evidence.extra["check_id"]: i.confidence_level for i in validated.issues}
    assert levels["title_present"] == ConfidenceLevel.VERY_HIGH
    assert levels["touch_target_size"] == ConfidenceLevel.MEDIUM


def test_validate_category_result_is_a_noop_when_nothing_to_dedupe():
    result = _category_result([_issue("title_present")])
    validated = validate_category_result(result)
    assert len(validated.issues) == 1
    assert validated.failed_count == result.failed_count
