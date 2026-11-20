"""The ONE place the overall score is computed from category results — mirrors
`src/lib/scoring.ts`'s `calculateOverallScore` / `getGradeInfo` exactly (same weights, same
formula, same grade thresholds) so the backend and the existing frontend demo-data path never
disagree about what a given score means. Analyzer logic lives in `services/analyzers/`; this
module never looks at raw scan evidence, only at the `CategoryResult`s analyzers already
produced — keeping scoring rules separate from analyzer logic, as the spec requires."""

from __future__ import annotations

from models.evaluation_models import CATEGORY_WEIGHTS, CategoryId, CategoryResult


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
