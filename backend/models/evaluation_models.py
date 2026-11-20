"""Schemas for Phase 3's evaluation engine — issues, recommendations, category results, and the
top-level evaluation. Deliberately separate from `scan_models.py`: those are Phase 2's raw
scanning contract, these are what the 12 analyzers + scoring/severity/recommendation engines
produce from that raw evidence. Field names mirror the frontend's existing `CategoryId` list in
`src/lib/categories.ts` exactly, so the API response needs no renaming on the way to the UI."""

from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

CategoryId = Literal[
    "ui",
    "ux",
    "performance",
    "seo",
    "accessibility",
    "mobile",
    "security",
    "content",
    "conversion",
    "trust",
    "technical",
    "innovation",
]

CATEGORY_IDS: tuple[CategoryId, ...] = (
    "ui",
    "ux",
    "performance",
    "seo",
    "accessibility",
    "mobile",
    "security",
    "content",
    "conversion",
    "trust",
    "technical",
    "innovation",
)

# Single source of truth for category weights on the backend — must stay numerically identical
# to src/lib/categories.ts. There is no shared schema file across the Next.js/Python boundary,
# so this is checked against the frontend's values in tests/test_scoring.py rather than silently
# trusted to stay in sync.
CATEGORY_WEIGHTS: dict[CategoryId, float] = {
    "ui": 12,
    "ux": 12,
    "performance": 12,
    "seo": 10,
    "accessibility": 10,
    "mobile": 10,
    "security": 8,
    "content": 7,
    "conversion": 7,
    "trust": 5,
    "technical": 5,
    "innovation": 2,
}


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class Priority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class Effort(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CheckStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"  # could not be performed — never counted as a failure


class Evidence(BaseModel):
    """What was actually observed, so every issue is traceable back to real data rather than
    an assertion. `element`/`selector` are left None when the evidence is page-level (e.g. a
    missing meta tag has no selector to point at beyond `head`)."""

    element: str | None = None
    selector: str | None = None
    observed_value: Any | None = None
    expected_value: Any | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class Issue(BaseModel):
    issue_id: str
    category: CategoryId
    title: str
    description: str
    evidence: Evidence
    affected_url: str
    severity: Severity
    priority: Priority
    impact: str
    recommendation: str
    estimated_effort: Effort


class Recommendation(BaseModel):
    """One per `Issue` (joined by `issue_id`) — kept as a separate object, per the spec, so the
    API can serve `/recommendations` without the full issue/evidence payload."""

    issue_id: str
    category: CategoryId
    title: str
    what_to_fix: str
    why_it_matters: str
    how_to_fix: list[str]
    expected_benefit: str
    priority: Priority
    estimated_effort: Effort
    affected_url: str


class CheckResult(BaseModel):
    """One discrete thing an analyzer looked for. Every analyzer reports every check it
    attempted here — passed and unavailable included — so `passed/failed/unavailable` counts
    are always a true accounting of what was (and wasn't) actually evaluated."""

    check_id: str
    label: str
    status: CheckStatus
    detail: str | None = None


class CategoryResult(BaseModel):
    category: CategoryId
    weight: float
    score: float | None  # None only when every check in this category was unavailable
    checks: list[CheckResult]
    issues: list[Issue]
    recommendations: list[Recommendation]
    passed_count: int
    failed_count: int
    unavailable_count: int
    summary: str


class EvaluationStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EvaluationError(BaseModel):
    code: str
    message: str


class EvaluationRequest(BaseModel):
    scan_id: str = Field(..., min_length=1, max_length=64)


class EvaluationResult(BaseModel):
    evaluation_id: str
    scan_id: str
    submitted_url: str
    status: EvaluationStatus
    overall_score: float | None = None
    score_coverage_percent: float | None = None  # % of total weight actually scored
    grade: str | None = None
    categories: dict[str, CategoryResult] = Field(default_factory=dict)
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    unavailable_checks: int = 0
    error: EvaluationError | None = None
    started_at: str
    completed_at: str | None = None


class StartEvaluationResponse(BaseModel):
    evaluation_id: str
    status: EvaluationStatus


class IssuesResponse(BaseModel):
    evaluation_id: str
    total: int
    issues: list[Issue]


class RecommendationsResponse(BaseModel):
    evaluation_id: str
    total: int
    recommendations: list[Recommendation]


class CategorySummary(BaseModel):
    category: CategoryId
    weight: float
    score: float | None
    passed_count: int
    failed_count: int
    unavailable_count: int


class CategoriesResponse(BaseModel):
    evaluation_id: str
    overall_score: float | None
    categories: list[CategorySummary]
