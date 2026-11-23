from __future__ import annotations

from models.evaluation_models import CATEGORY_WEIGHTS, CategoryId, CategoryResult
from services import scoring_engine

# The frontend's independent source of truth (src/lib/categories.ts) — duplicated here
# deliberately, not imported, so this test fails loudly if either side drifts out of sync
# rather than the two silently disagreeing about what a score means.
_FRONTEND_WEIGHTS: dict[CategoryId, float] = {
    "ui": 12, "ux": 12, "performance": 12, "seo": 10, "accessibility": 10, "mobile": 10,
    "security": 8, "content": 7, "conversion": 7, "trust": 5, "technical": 5, "innovation": 2,
}


def test_weights_match_frontend_exactly():
    assert CATEGORY_WEIGHTS == _FRONTEND_WEIGHTS


def test_weights_sum_to_100():
    assert scoring_engine.validate_category_weights() is True
    assert sum(CATEGORY_WEIGHTS.values()) == 100


def _result(category: CategoryId, score: float | None) -> CategoryResult:
    return CategoryResult(
        category=category, weight=CATEGORY_WEIGHTS[category], score=score,
        checks=[], issues=[], recommendations=[], passed_count=0, failed_count=0, unavailable_count=0,
        summary="",
    )


def test_overall_score_all_categories_present():
    categories = {cid: _result(cid, 80.0) for cid in CATEGORY_WEIGHTS}
    overall, coverage = scoring_engine.calculate_overall_score(categories)
    assert overall == 80.0
    assert coverage == 100.0


def test_overall_score_matches_manual_weighted_sum():
    scores = {"ui": 90, "ux": 85, "performance": 78, "seo": 88, "accessibility": 72, "mobile": 91,
              "security": 95, "content": 80, "conversion": 76, "trust": 84, "technical": 82, "innovation": 90}
    categories = {cid: _result(cid, score) for cid, score in scores.items()}
    overall, coverage = scoring_engine.calculate_overall_score(categories)
    expected = round(sum(scores[cid] * CATEGORY_WEIGHTS[cid] for cid in scores) / 100, 2)
    assert overall == expected
    assert coverage == 100.0


def test_overall_score_renormalizes_when_a_category_is_unavailable():
    categories = {cid: _result(cid, 100.0) for cid in CATEGORY_WEIGHTS}
    categories["innovation"] = _result("innovation", None)  # weight 2 — smallest category
    overall, coverage = scoring_engine.calculate_overall_score(categories)
    # Every scored category is 100, so the renormalized overall must still be 100 —
    # a missing category must never drag the score down as if it had failed.
    assert overall == 100.0
    assert coverage == 98.0


def test_overall_score_none_when_everything_unavailable():
    categories = {cid: _result(cid, None) for cid in CATEGORY_WEIGHTS}
    overall, coverage = scoring_engine.calculate_overall_score(categories)
    assert overall is None
    assert coverage == 0.0


def test_grade_thresholds_match_frontend():
    assert scoring_engine.grade_label(95) == "Excellent"
    assert scoring_engine.grade_label(90) == "Excellent"
    assert scoring_engine.grade_label(89.9) == "Good"
    assert scoring_engine.grade_label(75) == "Good"
    assert scoring_engine.grade_label(74.9) == "Needs Attention"
    assert scoring_engine.grade_label(60) == "Needs Attention"
    assert scoring_engine.grade_label(59.9) == "Critical"
    assert scoring_engine.grade_label(0) == "Critical"


def test_explain_category_score_describes_pass_fail_ratio():
    from models.evaluation_models import CheckResult, CheckStatus

    result = CategoryResult(
        category="seo", weight=10, score=66.7,
        checks=[
            CheckResult(check_id="a", label="Title present", status=CheckStatus.PASSED),
            CheckResult(check_id="b", label="Meta description present", status=CheckStatus.PASSED),
            CheckResult(check_id="c", label="Canonical present", status=CheckStatus.FAILED, detail="x"),
            CheckResult(check_id="d", label="Sitemap present", status=CheckStatus.UNAVAILABLE, detail="probe_failed"),
        ],
        issues=[], recommendations=[], passed_count=2, failed_count=1, unavailable_count=1, summary="",
    )
    explanation = scoring_engine.explain_category_score(result)
    assert "2 of 3" in explanation
    assert "1 additional check" in explanation
    assert "Canonical present" in explanation


def test_explain_category_score_when_entirely_unavailable():
    result = CategoryResult(
        category="seo", weight=10, score=None, checks=[], issues=[], recommendations=[],
        passed_count=0, failed_count=0, unavailable_count=3, summary="",
    )
    explanation = scoring_engine.explain_category_score(result)
    assert "No score" in explanation
    assert "3" in explanation
