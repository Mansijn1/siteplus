"""Shared helper every one of the 12 analyzers builds its `CategoryResult` through. Keeping the
check/issue bookkeeping and scoring arithmetic here (not duplicated per analyzer) is what makes
"Do not assign arbitrary scores when evidence is missing" and "never invent issues" structurally
true rather than a convention each analyzer has to remember."""

from __future__ import annotations

from models.evaluation_models import (
    CATEGORY_WEIGHTS,
    CategoryId,
    CategoryResult,
    CheckResult,
    CheckStatus,
    Effort,
    Evidence,
    Issue,
    Priority,
    Recommendation,
    Severity,
)


class CategoryBuilder:
    """Accumulates checks and issues for one category, then derives that category's 0-100
    score from ONLY the checks that were actually evaluated: unavailable checks are excluded
    from both the numerator and denominator, so they neither help nor hurt the score — they
    just show up in `unavailable_count` for transparency."""

    def __init__(self, category: CategoryId, affected_url: str):
        self.category = category
        self.affected_url = affected_url
        self._checks: list[CheckResult] = []
        self._issues: list[Issue] = []
        self._recommendations: list[Recommendation] = []
        self._issue_seq = 0

    @property
    def issue_count(self) -> int:
        return len(self._issues)

    def passed(self, check_id: str, label: str, detail: str | None = None) -> None:
        self._checks.append(CheckResult(check_id=check_id, label=label, status=CheckStatus.PASSED, detail=detail))

    def unavailable(self, check_id: str, label: str, reason: str) -> None:
        self._checks.append(
            CheckResult(check_id=check_id, label=label, status=CheckStatus.UNAVAILABLE, detail=reason)
        )

    def failed(
        self,
        check_id: str,
        label: str,
        *,
        title: str,
        description: str,
        severity: Severity,
        priority: Priority,
        impact: str,
        recommendation: str,
        estimated_effort: Effort,
        evidence: Evidence,
        how_to_fix: list[str],
        expected_benefit: str,
        affected_url: str | None = None,
    ) -> Issue:
        """Records one failed check as both an `Issue` (the evidence-bearing finding) and a
        paired `Recommendation` (the actionable fix) — a failed check always produces exactly
        one of each, joined by `issue_id`, never an issue without a recommendation or vice versa.
        `recommendation` is the one-line summary carried on the issue itself; `how_to_fix` is the
        specific step-by-step version the spec asks for on the richer Recommendation object.
        """
        self._checks.append(CheckResult(check_id=check_id, label=label, status=CheckStatus.FAILED, detail=title))
        self._issue_seq += 1
        issue_id = f"{self.category.upper()}-{self._issue_seq:03d}"
        resolved_url = affected_url or self.affected_url
        issue = Issue(
            issue_id=issue_id,
            category=self.category,
            title=title,
            description=description,
            evidence=evidence,
            affected_url=resolved_url,
            severity=severity,
            priority=priority,
            impact=impact,
            recommendation=recommendation,
            estimated_effort=estimated_effort,
        )
        self._issues.append(issue)
        self._recommendations.append(
            Recommendation(
                issue_id=issue_id,
                category=self.category,
                title=title,
                what_to_fix=recommendation,
                why_it_matters=impact,
                how_to_fix=how_to_fix,
                expected_benefit=expected_benefit,
                priority=priority,
                estimated_effort=estimated_effort,
                affected_url=resolved_url,
            )
        )
        return issue

    def build(self, summary: str) -> CategoryResult:
        passed = sum(1 for c in self._checks if c.status == CheckStatus.PASSED)
        failed = sum(1 for c in self._checks if c.status == CheckStatus.FAILED)
        unavailable = sum(1 for c in self._checks if c.status == CheckStatus.UNAVAILABLE)
        denom = passed + failed
        score = round((passed / denom) * 100, 1) if denom > 0 else None
        return CategoryResult(
            category=self.category,
            weight=CATEGORY_WEIGHTS[self.category],
            score=score,
            checks=self._checks,
            issues=self._issues,
            recommendations=self._recommendations,
            passed_count=passed,
            failed_count=failed,
            unavailable_count=unavailable,
            summary=summary,
        )
