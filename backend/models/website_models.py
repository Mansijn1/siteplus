"""Schemas for Phase 4's multi-page, website-level evaluation — one level above
`evaluation_models.py`'s single-page `EvaluationResult`, which this wraps one-per-page."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from models.evaluation_models import CategoryId, Issue, Priority, Severity


class WebsiteEvaluationStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WebsiteEvaluationRequest(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)
    max_pages: int = Field(default=5, ge=1, le=15)


class PageEvaluationSummary(BaseModel):
    url: str
    scan_id: str
    evaluation_id: str | None = None
    status: str  # "completed" | "failed"
    overall_score: float | None = None
    grade: str | None = None
    error: str | None = None


class SitewideIssue(BaseModel):
    """One recurring problem detected on 2+ pages, grouped so a single global defect (e.g. a
    missing meta description template-wide) is reported — and penalized — once, not as N
    unrelated issues. `affected_pages` preserves exactly which pages hit it."""

    category: CategoryId
    check_id: str
    title: str
    severity: Severity
    priority: Priority
    affected_pages: list[str]
    occurrence_count: int


class PageSpecificIssue(BaseModel):
    page_url: str
    issue: Issue


class WebsiteEvaluationResult(BaseModel):
    website_evaluation_id: str
    root_url: str
    status: WebsiteEvaluationStatus
    max_pages: int
    pages_discovered: int
    pages_scanned: int
    pages: list[PageEvaluationSummary] = Field(default_factory=list)
    overall_score: float | None = None
    grade: str | None = None
    category_scores: dict[str, float] = Field(default_factory=dict)
    sitewide_issues: list[SitewideIssue] = Field(default_factory=list)
    page_specific_issues: list[PageSpecificIssue] = Field(default_factory=list)
    highest_priority_problems: list[Issue] = Field(default_factory=list)
    started_at: str
    completed_at: str | None = None
    error: str | None = None
