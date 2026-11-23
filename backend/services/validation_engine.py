"""The layer between raw analyzer output and the final issue list, run once per category result
right after its analyzer produces it (see evaluation_engine.py). Maps directly onto the spec's
pipeline:

    Raw Detection          -> the analyzer's own b.failed(...) calls (services/analyzers/*)
    Evidence Verification  -> confidence_engine._has_concrete_evidence (folded into scoring below)
    Duplicate Detection     -> _dedupe_issues here (within one page; cross-page grouping is
                               services/website_evaluation_service.py's job, a different scope)
    Context Validation      -> already structural: a check is `unavailable` (not failed) when it
                               couldn't be performed, so "scanner limitation" vs "real defect" is
                               decided at detection time, not guessed at here
    Confidence Assessment  -> confidence_engine.verify_and_score
    Severity Classification -> already decided by the analyzer (it has the evidence); unchanged
    Final Issue             -> the CategoryResult this module returns
"""

from __future__ import annotations

from models.evaluation_models import CategoryResult
from services.confidence_engine import verify_and_score


def _dedupe_issues(result: CategoryResult) -> CategoryResult:
    """Defensive, not load-bearing: each analyzer's CategoryBuilder already calls a given
    check_id at most once per run, so this should never actually drop anything today. It exists
    because the spec explicitly asks for same-page duplicate detection, and because a future
    analyzer bug (e.g. a loop that calls `b.failed` with the same check_id twice) should degrade
    to "one issue" rather than silently double-counting against the score."""
    seen_check_ids: set[str] = set()
    deduped_issues = []
    kept_issue_ids: set[str] = set()
    for issue in result.issues:
        check_id = issue.evidence.extra.get("check_id") if issue.evidence.extra else issue.issue_id
        if check_id in seen_check_ids:
            continue
        seen_check_ids.add(check_id)
        deduped_issues.append(issue)
        kept_issue_ids.add(issue.issue_id)

    if len(deduped_issues) == len(result.issues):
        return result  # nothing to change — avoid an unnecessary copy on the common path

    deduped_recommendations = [r for r in result.recommendations if r.issue_id in kept_issue_ids]
    # failed_count == len(issues) by construction (every failed check produces exactly one
    # issue) — so the deduplicated count is just the deduplicated issue count, directly. Score
    # is recomputed with the same passed/(passed+failed) formula CategoryBuilder.build() uses,
    # since a dropped duplicate changes that ratio.
    new_failed_count = len(deduped_issues)
    denom = result.passed_count + new_failed_count
    new_score = round((result.passed_count / denom) * 100, 1) if denom > 0 else None
    return result.model_copy(
        update={
            "issues": deduped_issues,
            "recommendations": deduped_recommendations,
            "failed_count": new_failed_count,
            "score": new_score,
        }
    )


def validate_category_result(result: CategoryResult) -> CategoryResult:
    deduped = _dedupe_issues(result)
    scored_issues = [verify_and_score(issue) for issue in deduped.issues]
    if scored_issues == deduped.issues:
        return deduped
    return deduped.model_copy(update={"issues": scored_issues})
