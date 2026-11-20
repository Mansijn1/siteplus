"""Aggregates the `Recommendation`s each analyzer already produced (paired 1:1 with its own
`Issue`s, with specific evidence-based text — see `services/analyzers/base.py`) across all 12
categories, de-duplicates, and ranks them. This module never writes recommendation text itself;
generic copy like "Improve your SEO" would come from exactly that kind of centralized,
evidence-blind text generation, which the spec explicitly rules out."""

from __future__ import annotations

from models.evaluation_models import CategoryResult, Priority, Recommendation

_PRIORITY_RANK: dict[Priority, int] = {Priority.P0: 0, Priority.P1: 1, Priority.P2: 2, Priority.P3: 3}


def collect_recommendations(categories: dict[str, CategoryResult]) -> list[Recommendation]:
    seen_issue_ids: set[str] = set()
    all_recs: list[Recommendation] = []
    for result in categories.values():
        for rec in result.recommendations:
            # Guards against an analyzer bug emitting the same issue_id twice rather than a
            # real possibility in normal operation — issue_ids are already per-category-scoped
            # sequential, so a duplicate here means something upstream double-counted a check.
            if rec.issue_id in seen_issue_ids:
                continue
            seen_issue_ids.add(rec.issue_id)
            all_recs.append(rec)

    all_recs.sort(key=lambda r: (_PRIORITY_RANK[r.priority], r.category))
    return all_recs
