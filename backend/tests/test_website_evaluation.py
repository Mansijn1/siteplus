from __future__ import annotations

from models.evaluation_models import CheckStatus
from services import evaluation_engine
from services.site_crawler import discover_pages
from services.website_evaluation_service import _aggregate_category_scores, _group_issues
from tests.conftest import make_scan_results


# ---- site_crawler.discover_pages (pure function) ----


def test_discover_pages_includes_homepage_first():
    pages = discover_pages("https://example.com/", [], [], max_pages=5)
    assert pages == ["https://example.com/"]


def test_discover_pages_dedupes_trailing_slash_variants():
    pages = discover_pages(
        "https://example.com/",
        internal_link_urls=["https://example.com", "https://example.com/about", "https://example.com/about/"],
        sitemap_urls=[],
        max_pages=5,
    )
    assert pages == ["https://example.com/", "https://example.com/about"]


def test_discover_pages_excludes_other_domains():
    pages = discover_pages(
        "https://example.com/",
        internal_link_urls=["https://example.com/about", "https://evil.example.net/phish"],
        sitemap_urls=[],
        max_pages=5,
    )
    assert all("evil.example.net" not in p for p in pages)


def test_discover_pages_prefers_sitemap_over_internal_links():
    pages = discover_pages(
        "https://example.com/",
        internal_link_urls=["https://example.com/from-nav"],
        sitemap_urls=["https://example.com/from-sitemap"],
        max_pages=2,
    )
    assert pages == ["https://example.com/", "https://example.com/from-sitemap"]


def test_discover_pages_respects_max_pages_cap():
    many_links = [f"https://example.com/page-{i}" for i in range(20)]
    pages = discover_pages("https://example.com/", many_links, [], max_pages=3)
    assert len(pages) == 3


# ---- website_evaluation_service aggregation (internal consistency) ----


async def _evaluate(**overrides):
    scan = make_scan_results(**overrides)
    return await evaluation_engine.run_evaluation("eval-id", scan, "2026-01-01T00:00:00+00:00")


async def test_aggregate_category_scores_averages_across_pages():
    eval_a = await _evaluate(title="Page A Title")
    eval_b = await _evaluate(title="Page B Title")
    scores = _aggregate_category_scores([eval_a, eval_b])
    # Both pages are otherwise identical "healthy" fixtures, so every category score should
    # average to exactly what either page scored alone.
    for category_id, score in eval_a.categories.items():
        if score.score is not None:
            assert scores[category_id] == score.score


async def test_group_issues_detects_sitewide_recurring_issue():
    eval_a = await _evaluate(title=None, url="https://example.test/a")
    eval_b = await _evaluate(title=None, url="https://example.test/b")
    sitewide, page_specific = _group_issues(
        [("https://example.test/a", eval_a), ("https://example.test/b", eval_b)]
    )
    missing_title_sitewide = [s for s in sitewide if s.check_id == "title_present"]
    assert len(missing_title_sitewide) == 1
    assert missing_title_sitewide[0].occurrence_count == 2
    assert set(missing_title_sitewide[0].affected_pages) == {"https://example.test/a", "https://example.test/b"}
    # The same check_id must not ALSO appear as a page-specific issue once it's grouped sitewide.
    assert not any(p.issue.evidence.extra.get("check_id") == "title_present" for p in page_specific)


async def test_group_issues_keeps_single_page_issue_as_page_specific():
    eval_a = await _evaluate(title=None, url="https://example.test/only-a")
    eval_b = await _evaluate(url="https://example.test/b")  # healthy — has a title
    sitewide, page_specific = _group_issues(
        [("https://example.test/only-a", eval_a), ("https://example.test/b", eval_b)]
    )
    assert not any(s.check_id == "title_present" for s in sitewide)
    matching = [p for p in page_specific if p.issue.evidence.extra.get("check_id") == "title_present"]
    assert len(matching) == 1
    assert matching[0].page_url == "https://example.test/only-a"


async def test_issue_check_id_is_stable_and_recoverable_from_evidence():
    evaluation = await _evaluate(title=None)
    seo = evaluation.categories["seo"]
    title_issue = next(i for i in seo.issues if i.evidence.extra.get("check_id") == "title_present")
    assert title_issue.evidence.extra["check_id"] == "title_present"


# ---- cross-page broken internal link detection ----


def test_detect_broken_internal_links_flags_a_link_to_a_crawled_404_page():
    from services.website_evaluation_service import _detect_broken_internal_links

    page_a = make_scan_results(
        url="https://example.test/a", internal_link_urls=["https://example.test/b"]
    )
    page_b = make_scan_results(url="https://example.test/b", status_code=404)
    issues = _detect_broken_internal_links(
        [("https://example.test/a", page_a), ("https://example.test/b", page_b)]
    )
    assert len(issues) == 1
    assert issues[0].page_url == "https://example.test/a"
    assert issues[0].issue.evidence.observed_value == 404


def test_detect_broken_internal_links_ignores_links_to_pages_outside_the_crawl():
    from services.website_evaluation_service import _detect_broken_internal_links

    page_a = make_scan_results(
        url="https://example.test/a", internal_link_urls=["https://example.test/not-crawled"]
    )
    issues = _detect_broken_internal_links([("https://example.test/a", page_a)])
    assert issues == []


def test_detect_broken_internal_links_ignores_healthy_links():
    from services.website_evaluation_service import _detect_broken_internal_links

    page_a = make_scan_results(
        url="https://example.test/a", internal_link_urls=["https://example.test/b"]
    )
    page_b = make_scan_results(url="https://example.test/b", status_code=200)
    issues = _detect_broken_internal_links(
        [("https://example.test/a", page_a), ("https://example.test/b", page_b)]
    )
    assert issues == []
