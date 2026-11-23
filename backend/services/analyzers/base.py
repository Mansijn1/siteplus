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
        documentation_url: str | None = None,
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
        # The stable check_id (e.g. "title_present"), not the per-scan sequential issue_id, is
        # what the multi-page crawler groups recurring sitewide issues by — issue_id numbering
        # depends on which checks happened to fail first on a given page, so it isn't stable
        # across pages, but check_id always identifies the same underlying rule.
        evidence_with_check_id = evidence.model_copy(update={"extra": {**evidence.extra, "check_id": check_id}})
        issue = Issue(
            issue_id=issue_id,
            category=self.category,
            title=title,
            description=description,
            evidence=evidence_with_check_id,
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
                # `description` is what was actually observed (e.g. "the page has no <title>
                # element") — that observation IS the root cause for virtually every check this
                # project runs, so reusing it here (rather than asking 12 analyzer files to
                # author a second, separate root-cause string) keeps it always in sync with the
                # evidence instead of risking the two texts drifting apart.
                root_cause=description,
                what_to_fix=recommendation,
                why_it_matters=impact,
                how_to_fix=how_to_fix,
                expected_benefit=expected_benefit,
                priority=priority,
                estimated_effort=estimated_effort,
                affected_url=resolved_url,
                documentation_url=documentation_url,
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
