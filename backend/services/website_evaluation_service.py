"""Orchestrates a multi-page website evaluation: scans the homepage, discovers same-domain
pages from its sitemap/internal links, scans+evaluates each (each discovered URL is
independently re-validated through the same SSRF gate as any user-submitted URL — these come
from page content, not from the request, so they get no special trust), then aggregates into
one website-level report. Recurring issues are grouped across pages (never double-counted as
unrelated findings); category scores are averaged across the pages that produced a score for
that category, so a page with no evidence for a category doesn't drag the site average down."""

from __future__ import annotations

import asyncio
import uuid
from collections import defaultdict
from datetime import datetime, timezone

from models.evaluation_models import Effort, EvaluationResult, Evidence, Issue, Priority, Severity
from models.scan_models import ScanResults
from models.website_models import (
    PageEvaluationSummary,
    PageSpecificIssue,
    SitewideIssue,
    WebsiteEvaluationResult,
    WebsiteEvaluationStatus,
)
from scanner.browser import ScanBrowserError
from security.url_validation import URLValidationError
from services import evaluation_engine, scan_service, scoring_engine
from services.confidence_engine import verify_and_score
from services.severity_engine import derive_priority
from services.site_crawler import discover_pages, normalize_url

_PRIORITY_RANK: dict[Priority, int] = {Priority.P0: 0, Priority.P1: 1, Priority.P2: 2, Priority.P3: 3}

_website_evaluations: dict[str, WebsiteEvaluationResult] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_website_evaluation(website_evaluation_id: str) -> WebsiteEvaluationResult | None:
    return _website_evaluations.get(website_evaluation_id)


async def _scan_and_evaluate(url: str) -> tuple[PageEvaluationSummary, EvaluationResult | None, ScanResults | None]:
    scan_id = uuid.uuid4().hex[:16]
    try:
        validated = await scan_service.validate_url_for_api(url)
    except URLValidationError as exc:
        return PageEvaluationSummary(url=url, scan_id=scan_id, status="failed", error=exc.message), None, None

    try:
        scan_results = await scan_service.run_scan_for_url(scan_id, validated.url)
    except ScanBrowserError as exc:
        return PageEvaluationSummary(url=url, scan_id=scan_id, status="failed", error=exc.message), None, None
    except Exception as exc:  # noqa: BLE001 — one page's failure must not take down the whole crawl
        return PageEvaluationSummary(url=url, scan_id=scan_id, status="failed", error=str(exc)[:300]), None, None

    evaluation_id = uuid.uuid4().hex[:16]
    try:
        evaluation = await evaluation_engine.run_evaluation(evaluation_id, scan_results, _now())
    except Exception as exc:  # noqa: BLE001 — same guarantee for the evaluation step
        return (
            PageEvaluationSummary(url=url, scan_id=scan_id, status="failed", error=f"evaluation_failed: {exc}"[:300]),
            None,
            scan_results,
        )

    summary = PageEvaluationSummary(
        url=url,
        scan_id=scan_id,
        evaluation_id=evaluation_id,
        status=evaluation.status.value,
        overall_score=evaluation.overall_score,
        grade=evaluation.grade,
    )
    return summary, evaluation, scan_results


def _aggregate_category_scores(evaluations: list[EvaluationResult]) -> dict[str, float]:
    sums: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    for evaluation in evaluations:
        for category_id, result in evaluation.categories.items():
            if result.score is not None:
                sums[category_id] += result.score
                counts[category_id] += 1
    return {cat: round(sums[cat] / counts[cat], 1) for cat in sums if counts[cat] > 0}


def _group_issues(
    evaluations: list[tuple[str, EvaluationResult]],
) -> tuple[list[SitewideIssue], list[PageSpecificIssue]]:
    """Groups issues by (category, check_id) — not by title text, since two pages can fail the
    same check with slightly different titles (e.g. "HTTP 500" vs "HTTP 404") yet represent the
    same underlying site-wide problem class."""
    groups: dict[tuple[str, str], list[tuple[str, Issue]]] = defaultdict(list)
    for page_url, evaluation in evaluations:
        for category_id, result in evaluation.categories.items():
            for issue in result.issues:
                check_id = issue.evidence.extra.get("check_id") if issue.evidence.extra else None
                key = (category_id, check_id or issue.title)
                groups[key].append((page_url, issue))

    sitewide: list[SitewideIssue] = []
    page_specific: list[PageSpecificIssue] = []
    for (category_id, check_key), occurrences in groups.items():
        if len(occurrences) >= 2:
            pages = [p for p, _ in occurrences]
            worst = max((i for _, i in occurrences), key=lambda i: _PRIORITY_RANK[i.priority] * -1)
            sitewide.append(
                SitewideIssue(
                    category=category_id,  # type: ignore[arg-type]
                    check_id=check_key,
                    title=occurrences[0][1].title,
                    severity=worst.severity,
                    priority=worst.priority,
                    affected_pages=pages,
                    occurrence_count=len(occurrences),
                )
            )
        else:
            page_url, issue = occurrences[0]
            page_specific.append(PageSpecificIssue(page_url=page_url, issue=issue))

    return sitewide, page_specific


def _detect_broken_internal_links(pages_with_scans: list[tuple[str, ScanResults]]) -> list[PageSpecificIssue]:
    """A real check the single-page SEO analyzer explicitly marks unavailable (it has no way to
    know what another page returns) — now answerable because a multi-page crawl has actually
    visited some of those linked pages. Only claims a link is broken when the target was itself
    part of this crawl and returned a non-2xx status; a link to a page outside the crawl stays
    unverified (not flagged), since we have no evidence about it either way."""
    status_by_url = {
        normalize_url(scan.response.final_url or url): scan.response.status_code
        for url, scan in pages_with_scans
    }

    issues: list[PageSpecificIssue] = []
    for page_url, scan in pages_with_scans:
        if scan.extracted is None:
            continue
        for link in scan.extracted.seo.internal_link_urls:
            target_status = status_by_url.get(normalize_url(link))
            if target_status is None or 200 <= target_status < 300:
                continue
            severity = Severity.HIGH
            issue = Issue(
                issue_id=f"SEO-CROSSPAGE-{len(issues) + 1:03d}",
                category="seo",
                title=f"Internal link points to a page returning HTTP {target_status}",
                description=f"This page links to {link}, which this crawl observed returning HTTP {target_status}.",
                evidence=Evidence(
                    selector=f"a[href*='{link}']",
                    observed_value=target_status,
                    expected_value="2xx",
                    extra={"check_id": "broken_internal_link_crosspage", "target_url": link},
                ),
                affected_url=page_url,
                severity=severity,
                priority=derive_priority(severity),
                impact="Visitors following this link hit a broken or erroring page — a direct, confirmed broken link, not a guess.",
                recommendation=f"Update or remove the link to {link}, or fix why that page returns HTTP {target_status}.",
                estimated_effort=Effort.LOW,
            )
            issues.append(PageSpecificIssue(page_url=page_url, issue=verify_and_score(issue)))
    return issues


async def start_website_evaluation(root_url: str, max_pages: int) -> WebsiteEvaluationResult:
    website_evaluation_id = uuid.uuid4().hex[:16]
    started_at = _now()

    homepage_summary, homepage_evaluation, homepage_scan = await _scan_and_evaluate(root_url)
    if homepage_evaluation is None or homepage_scan is None:
        result = WebsiteEvaluationResult(
            website_evaluation_id=website_evaluation_id,
            root_url=root_url,
            status=WebsiteEvaluationStatus.FAILED,
            max_pages=max_pages,
            pages_discovered=1,
            pages_scanned=0,
            pages=[homepage_summary],
            started_at=started_at,
            completed_at=_now(),
            error=homepage_summary.error or "Homepage scan failed.",
        )
        _website_evaluations[website_evaluation_id] = result
        return result

    sitemap_urls = homepage_scan.audit_extras.robots_sitemap.sitemap_urls if homepage_scan.audit_extras else []
    internal_links = homepage_scan.extracted.seo.internal_link_urls if homepage_scan.extracted else []
    discovered = discover_pages(
        homepage_scan.response.final_url or root_url, internal_links, sitemap_urls, max_pages
    )
    additional_pages = discovered[1:]  # homepage already scanned above

    other_results = await asyncio.gather(*[_scan_and_evaluate(url) for url in additional_pages])

    all_summaries = [homepage_summary] + [s for s, _, _ in other_results]
    all_evaluations_with_url: list[tuple[str, EvaluationResult]] = [(root_url, homepage_evaluation)] + [
        (summary.url, evaluation) for summary, evaluation, _ in other_results if evaluation is not None
    ]
    evaluations_only = [e for _, e in all_evaluations_with_url]
    all_scans_with_url: list[tuple[str, ScanResults]] = [(root_url, homepage_scan)] + [
        (summary.url, scan) for summary, _, scan in other_results if scan is not None
    ]

    # Website-level overall score is the average of each page's own overall score (each of
    # which is already a correctly-renormalized weighted average) — simplest, most explainable
    # aggregate, and avoids re-deriving a second, different weighting scheme at the site level.
    page_scores = [e.overall_score for e in evaluations_only if e.overall_score is not None]
    overall_score = round(sum(page_scores) / len(page_scores), 2) if page_scores else None
    grade = scoring_engine.grade_label(overall_score) if overall_score is not None else None

    category_scores = _aggregate_category_scores(evaluations_only)
    sitewide_issues, page_specific_issues = _group_issues(all_evaluations_with_url)
    page_specific_issues += _detect_broken_internal_links(all_scans_with_url)

    all_issues_ranked = sorted(
        [si for si in sitewide_issues] + [psi.issue for psi in page_specific_issues],
        key=lambda i: _PRIORITY_RANK[i.priority],
    )
    highest_priority: list[Issue] = []
    for item in all_issues_ranked[:10]:
        if isinstance(item, SitewideIssue):
            highest_priority.append(
                verify_and_score(
                    Issue(
                        issue_id=f"SITEWIDE-{item.check_id}",
                        category=item.category,
                        title=f"{item.title} (found on {item.occurrence_count} pages)",
                        description=f"This issue recurs across {item.occurrence_count} pages: {', '.join(item.affected_pages[:5])}.",
                        evidence=Evidence(extra={"check_id": item.check_id, "affected_pages": item.affected_pages}),
                        affected_url=item.affected_pages[0],
                        severity=item.severity,
                        priority=item.priority,
                        impact="A site-wide recurring issue — fixing it once (e.g. in a shared template) likely resolves it on every affected page.",
                        recommendation="See the per-page category analysis for this check's specific fix.",
                        estimated_effort=Effort.MEDIUM,
                    )
                )
            )
        else:
            highest_priority.append(item)

    result = WebsiteEvaluationResult(
        website_evaluation_id=website_evaluation_id,
        root_url=root_url,
        status=WebsiteEvaluationStatus.COMPLETED,
        max_pages=max_pages,
        pages_discovered=len(discovered),
        pages_scanned=len(all_summaries),
        pages=all_summaries,
        overall_score=overall_score,
        grade=grade,
        category_scores=category_scores,
        sitewide_issues=sitewide_issues,
        page_specific_issues=page_specific_issues,
        highest_priority_problems=highest_priority,
        started_at=started_at,
        completed_at=_now(),
    )
    _website_evaluations[website_evaluation_id] = result
    return result
