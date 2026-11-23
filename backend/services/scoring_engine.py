"""The ONE place the overall score is computed from category results — mirrors
`src/lib/scoring.ts`'s `calculateOverallScore` / `getGradeInfo` exactly (same weights, same
formula, same grade thresholds) so the backend and the existing frontend demo-data path never
disagree about what a given score means. Analyzer logic lives in `services/analyzers/`; this
module never looks at raw scan evidence, only at the `CategoryResult`s analyzers already
produced — keeping scoring rules separate from analyzer logic, as the spec requires."""

from __future__ import annotations

from models.evaluation_models import CATEGORY_WEIGHTS, CategoryId, CategoryResult, CheckStatus

# Bump whenever CATEGORY_WEIGHTS, the renormalization formula, or confidence_engine's source
# bands change in a way that makes an older evaluation's score not directly comparable to a new
# one. 1.0.0 is Phase 4's baseline — no scoring changes have shipped past it yet. See Stage F's
# calibration notes (services/calibration.py) for the process before this number moves: the spec
# is explicit that scoring weights must not change automatically in production without the
# benchmark framework (Stage H) validating the change first.
SCORING_CONFIG_VERSION = "1.0.0"


def calculate_overall_score(categories: dict[str, CategoryResult]) -> tuple[float | None, float]:
    """Overall Score = Sum(Category Score x Category Weight) / Sum(weight of SCORED categories).

    When every category has a score, that denominator is exactly 100 — identical to the
    frontend's `Overall Score = Sum(Category Score x Category Weight) / 100`. When some
    categories are `score=None` (every check in them was unavailable), this renormalizes over
    only the categories that actually produced a score, rather than silently scoring the
    missing ones as 0 — scoring missing evidence as a failure would be exactly the "arbitrary
    score when evidence is missing" the spec forbids. Returns (overall_score, coverage_percent)
    where coverage is what fraction of the full 100-point weight was actually scored.
    """
    scored_weight = 0.0
    weighted_sum = 0.0
    for category_id, result in categories.items():
        if result.score is None:
            continue
        weighted_sum += result.score * result.weight
        scored_weight += result.weight

    if scored_weight == 0:
        return None, 0.0

    overall = round(weighted_sum / scored_weight, 2)
    coverage = round(scored_weight, 2)  # out of 100, since weights already sum to 100
    return overall, coverage


_GRADE_THRESHOLDS: list[tuple[float, str]] = [
    (90, "Excellent"),
    (75, "Good"),
    (60, "Needs Attention"),
    (0, "Critical"),
]


def grade_label(score: float) -> str:
    clamped = max(0.0, min(100.0, score))
    for threshold, label in _GRADE_THRESHOLDS:
        if clamped >= threshold:
            return label
    return _GRADE_THRESHOLDS[-1][1]


def validate_category_weights() -> bool:
    return sum(CATEGORY_WEIGHTS.values()) == 100


def explain_category_score(result: CategoryResult) -> str:
    """A short, literal statement of what produced this score — generated mechanically from the
    checks list, not written by the analyzer, so the explanation can never drift from the
    arithmetic it's describing. Satisfies "every category should explain what was tested, what
    passed, what failed, what could not be tested, and why it received its score"."""
    total_performed = result.passed_count + result.failed_count
    if result.score is None:
        return (
            f"No score: all {result.unavailable_count} check(s) attempted for this category "
            "could not be performed on this scan (see each check's reason), so there is no "
            "evidence to score against."
        )

    unavailable_note = (
        f" ({result.unavailable_count} additional check(s) could not be performed and were "
        "excluded from this ratio rather than counted as failing.)"
        if result.unavailable_count > 0
        else ""
    )
    failing_labels = [c.label for c in result.checks if c.status == CheckStatus.FAILED][:3]
    failing_note = f" Failing: {', '.join(failing_labels)}{'…' if result.failed_count > 3 else ''}." if failing_labels else ""

    return (
        f"Score {result.score}/100 = {result.passed_count} of {total_performed} performed "
        f"check(s) passed.{unavailable_note}{failing_note}"
    )
