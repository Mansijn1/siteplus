"""SEO Evaluation (10%) — discoverability and metadata, using Phase 2's real extracted page
data plus the robots.txt/sitemap probe. Deliberately does NOT check subresource/link breakage
(that's Technical's job, module 11) to avoid double-penalizing the same evidence twice."""

from __future__ import annotations

from models.evaluation_models import CategoryResult, Effort, Evidence, Priority, Severity
from models.scan_models import ScanResults
from services.analyzers.base import CategoryBuilder
from services.severity_engine import derive_priority


def analyze(scan: ScanResults) -> CategoryResult:
    url = scan.response.final_url or scan.submitted_url
    b = CategoryBuilder("seo", url)

    if scan.extracted is None:
        b.unavailable("page_extraction", "Page content extraction", "scan_has_no_extracted_data")
        return b.build("Could not evaluate SEO — this scan has no extracted page data.")

    basic = scan.extracted.basic
    seo = scan.extracted.seo

    _check_title(b, basic)
    _check_meta_description(b, basic)
    _check_heading_structure(b, seo)
    _check_canonical(b, basic)
    _check_robots_meta(b, seo)
    _check_open_graph(b, seo)
    _check_image_alt(b, seo)
    _check_internal_linking(b, seo)
    _check_robots_sitemap(b, scan)

    b.unavailable(
        "broken_outbound_links", "Outbound link validity",
        "requires_crawling_every_linked_page_not_in_scope_for_a_single_page_scan",
    )

    summary = (
        f"SEO analysis found {b.issue_count} issue(s) across title, metadata, headings, and "
        "crawlability signals."
        if b.issue_count
        else "No SEO issues detected across title, metadata, headings, and crawlability signals."
    )
    return b.build(summary)


def _check_title(b: CategoryBuilder, basic) -> None:
    if not basic.title:
        b.failed(
            "title_present", "Page title present",
            title="Missing page title",
            description="The page has no <title> element, or it is empty.",
            severity=Severity.HIGH,
            priority=derive_priority(Severity.HIGH),
            impact="Search engines fall back to an auto-generated title, and the browser tab/share links show nothing useful.",
            recommendation="Add a unique, descriptive <title> tag of roughly 50-60 characters.",
            how_to_fix=[
                "Add a <title> tag inside <head> if one is missing.",
                "Write a unique title describing this specific page (avoid reusing the site name alone).",
                "Keep it to roughly 50-60 characters so it doesn't truncate in search results.",
            ],
            expected_benefit="Improves click-through rate from search results and correct browser-tab/share-link labeling.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(element="title", selector="head > title", observed_value=None, expected_value="A unique, descriptive title"),
        )
        return
    b.passed("title_present", "Page title present", detail=basic.title)
    length = len(basic.title)
    if length < 10 or length > 70:
        b.failed(
            "title_length", "Title length within recommended range",
            title=f"Page title length ({length} characters) is outside the recommended range",
            description=f"The title '{basic.title}' is {length} characters long. Titles under ~10 or over ~70 characters either lack context or get truncated in search results.",
            severity=Severity.LOW,
            priority=derive_priority(Severity.LOW),
            impact="Search engines may truncate or rewrite an overly long title; a very short title may lack enough context to earn clicks.",
            recommendation="Rewrite the title to roughly 50-60 characters, keeping the primary keyword near the front.",
            how_to_fix=[
                f"Review the current title: '{basic.title}'.",
                "Trim or expand it to land in the 50-60 character range.",
                "Keep the most important keyword/phrase within the first ~30 characters.",
            ],
            expected_benefit="Reduces truncation in search results and improves click-through rate.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(element="title", selector="head > title", observed_value=basic.title, expected_value="~50-60 characters"),
        )
    else:
        b.passed("title_length", "Title length within recommended range", detail=f"{length} characters")


def _check_meta_description(b: CategoryBuilder, basic) -> None:
    if not basic.meta_description:
        b.failed(
            "meta_description_present", "Meta description present",
            title="Missing meta description",
            description="The page has no <meta name=\"description\"> tag.",
            severity=Severity.HIGH,
            priority=derive_priority(Severity.HIGH),
            impact="Search engines generate an uncontrolled snippet from page content, which is often less compelling than an authored one.",
            recommendation="Add a unique meta description of roughly 120-160 characters summarizing the page.",
            how_to_fix=[
                "Add <meta name=\"description\" content=\"...\"> inside <head>.",
                "Summarize the page's specific value in 120-160 characters.",
                "Include the primary keyword naturally, without keyword-stuffing.",
            ],
            expected_benefit="Gives you control over the search-result snippet, typically improving click-through rate.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(element="meta[name=description]", observed_value=None, expected_value="A 120-160 character description"),
        )
        return
    b.passed("meta_description_present", "Meta description present", detail=basic.meta_description)
    length = len(basic.meta_description)
    if length < 50 or length > 170:
        b.failed(
            "meta_description_length", "Meta description length within recommended range",
            title=f"Meta description length ({length} characters) is outside the recommended range",
            description=f"The current description is {length} characters; the commonly recommended range is roughly 120-160.",
            severity=Severity.LOW,
            priority=derive_priority(Severity.LOW),
            impact="Too short wastes an opportunity to summarize the page; too long gets truncated in search results.",
            recommendation="Rewrite the meta description to roughly 120-160 characters.",
            how_to_fix=[
                f"Current description is {length} characters.",
                "Rewrite to land in the 120-160 character range.",
                "Lead with the most compelling, specific detail about this page.",
            ],
            expected_benefit="Improves how the page's snippet reads in search results.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(element="meta[name=description]", observed_value=basic.meta_description, expected_value="~120-160 characters"),
        )
    else:
        b.passed("meta_description_length", "Meta description length within recommended range", detail=f"{length} characters")


def _check_heading_structure(b: CategoryBuilder, seo) -> None:
    h1_count = seo.heading_counts.get("h1", 0)
    if h1_count == 0:
        b.failed(
            "single_h1", "Exactly one H1 heading",
            title="No H1 heading found",
            description="The page has zero <h1> elements.",
            severity=Severity.MEDIUM,
            priority=derive_priority(Severity.MEDIUM),
            impact="Search engines and assistive technology use the H1 as the page's primary topic signal; without one, that signal is missing.",
            recommendation="Add exactly one <h1> describing the page's main topic.",
            how_to_fix=["Identify the page's single main heading.", "Mark it up as an <h1>, not a styled <div> or <span>."],
            expected_benefit="Restores a clear primary-topic signal for search engines and screen readers.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(selector="h1", observed_value=0, expected_value=1),
        )
    elif h1_count > 1:
        b.failed(
            "single_h1", "Exactly one H1 heading",
            title=f"Multiple H1 headings found ({h1_count})",
            description=f"The page has {h1_count} <h1> elements; exactly one is recommended.",
            severity=Severity.LOW,
            priority=derive_priority(Severity.LOW),
            impact="Multiple H1s dilute the page's primary-topic signal.",
            recommendation="Keep one <h1> for the main topic and demote the others to <h2> or lower.",
            how_to_fix=["Identify which H1 best represents the page's main topic.", "Change the remaining H1 elements to H2 or lower."],
            expected_benefit="Restores a single, clear primary-topic signal.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(selector="h1", observed_value=h1_count, expected_value=1),
        )
    else:
        b.passed("single_h1", "Exactly one H1 heading", detail="1 H1 found")

    skipped = _find_heading_skip(seo.headings)
    if skipped:
        b.failed(
            "heading_hierarchy", "Heading levels do not skip",
            title=f"Heading hierarchy skips a level (H{skipped[0]} to H{skipped[1]})",
            description=f"A heading jumps from H{skipped[0]} directly to H{skipped[1]} without an intermediate level.",
            severity=Severity.LOW,
            priority=derive_priority(Severity.LOW),
            impact="Skipped heading levels make the document outline harder to follow for screen-reader users navigating by heading.",
            recommendation="Adjust heading levels so each step down the hierarchy is sequential.",
            how_to_fix=["Review the heading sequence on the page.", f"Insert or relabel headings so H{skipped[0]} is followed by H{skipped[0]+1}, not H{skipped[1]}."],
            expected_benefit="Improves document-outline navigation for assistive technology.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(selector="h1, h2, h3, h4, h5, h6", observed_value=f"H{skipped[0]} -> H{skipped[1]}"),
        )
    else:
        b.passed("heading_hierarchy", "Heading levels do not skip")


def _find_heading_skip(headings) -> tuple[int, int] | None:
    prev_level: int | None = None
    for h in headings:
        if prev_level is not None and h.level > prev_level + 1:
            return (prev_level, h.level)
        prev_level = h.level
    return None


def _check_canonical(b: CategoryBuilder, basic) -> None:
    if not basic.canonical_url:
        b.failed(
            "canonical_present", "Canonical URL present",
            title="Missing canonical URL",
            description="The page has no <link rel=\"canonical\"> tag.",
            severity=Severity.MEDIUM,
            priority=derive_priority(Severity.MEDIUM),
            impact="Without a canonical tag, search engines must guess which URL variant to index, risking duplicate-content splitting.",
            recommendation="Add a self-referencing canonical tag pointing to this page's preferred URL.",
            how_to_fix=["Add <link rel=\"canonical\" href=\"...\"> inside <head>.", "Point it at the preferred (e.g. non-trailing-slash, https, www or non-www) version of this URL."],
            expected_benefit="Consolidates ranking signals onto a single preferred URL.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(element="link[rel=canonical]", observed_value=None),
        )
    else:
        b.passed("canonical_present", "Canonical URL present", detail=basic.canonical_url)


def _check_robots_meta(b: CategoryBuilder, seo) -> None:
    robots = (seo.meta_robots or "").lower()
    if "noindex" in robots:
        b.failed(
            "robots_meta_not_blocking", "Page not blocked from indexing",
            title="Page has a noindex directive",
            description=f"The meta robots tag contains '{seo.meta_robots}'.",
            severity=Severity.CRITICAL,
            priority=derive_priority(Severity.CRITICAL),
            impact="This page is explicitly telling search engines not to index it — it will not appear in search results at all.",
            recommendation="Remove the noindex directive if this page is meant to be publicly discoverable.",
            how_to_fix=["Confirm whether this page is intentionally excluded from search.", "If not, remove or change the <meta name=\"robots\"> content to remove 'noindex'."],
            expected_benefit="Allows the page to be indexed and appear in search results.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(element="meta[name=robots]", observed_value=seo.meta_robots),
        )
    else:
        b.passed("robots_meta_not_blocking", "Page not blocked from indexing")


def _check_open_graph(b: CategoryBuilder, seo) -> None:
    has_title = "og:title" in seo.open_graph
    has_description = "og:description" in seo.open_graph
    has_image = "og:image" in seo.open_graph
    if has_title and has_description and has_image:
        b.passed("open_graph_present", "Open Graph tags present", detail="title, description, image all present")
        return
    missing = [k for k, present in (("og:title", has_title), ("og:description", has_description), ("og:image", has_image)) if not present]
    b.failed(
        "open_graph_present", "Open Graph tags present",
        title=f"Missing Open Graph tag(s): {', '.join(missing)}",
        description=f"The page is missing {', '.join(missing)} Open Graph meta tags.",
        severity=Severity.MEDIUM,
        priority=derive_priority(Severity.MEDIUM),
        impact="Links shared on social platforms (and some chat apps) will render with a generic or blank preview card.",
        recommendation=f"Add the missing Open Graph tag(s): {', '.join(missing)}.",
        how_to_fix=[
            f"Add <meta property=\"...\" content=\"...\"> for the missing tag(s): {', '.join(missing)}.",
            "Use a representative image at least 1200x630px for og:image.",
        ],
        expected_benefit="Social shares render with an accurate title, description, and preview image.",
        estimated_effort=Effort.LOW,
        evidence=Evidence(selector="meta[property^='og:']", observed_value=list(seo.open_graph.keys()), expected_value=["og:title", "og:description", "og:image"]),
    )


def _check_image_alt(b: CategoryBuilder, seo) -> None:
    if seo.images_total == 0:
        b.passed("images_alt_text", "Images have alt text", detail="no images on page")
        return
    if seo.images_missing_alt == 0:
        b.passed("images_alt_text", "Images have alt text", detail=f"0 of {seo.images_total} missing alt")
        return
    ratio = seo.images_missing_alt / seo.images_total
    severity = Severity.HIGH if ratio > 0.5 else Severity.MEDIUM
    b.failed(
        "images_alt_text", "Images have alt text",
        title=f"{seo.images_missing_alt} of {seo.images_total} images are missing alt text",
        description="Images without an alt attribute provide no textual context to search engines for image search indexing.",
        severity=severity,
        priority=derive_priority(severity),
        impact="Reduces image-search discoverability and (separately) hurts accessibility for screen-reader users.",
        recommendation="Add descriptive alt text to every content image; use alt=\"\" only for purely decorative images.",
        how_to_fix=[
            f"Find the {seo.images_missing_alt} <img> elements missing an alt attribute.",
            "For content images, write a concise description of what the image shows.",
            "For purely decorative images, use alt=\"\" (empty, not omitted) so screen readers skip them.",
        ],
        expected_benefit="Improves image-search visibility and screen-reader experience.",
        estimated_effort=Effort.MEDIUM,
        evidence=Evidence(selector="img:not([alt])", observed_value=seo.images_missing_alt, expected_value=0),
    )


def _check_internal_linking(b: CategoryBuilder, seo) -> None:
    if seo.internal_links == 0:
        b.failed(
            "internal_linking", "Page has internal links",
            title="No internal links found on this page",
            description="The scanned page contains zero links to other pages on the same site.",
            severity=Severity.MEDIUM,
            priority=derive_priority(Severity.MEDIUM),
            impact="Internal links help search engines discover and understand the relationship between pages; a page with none is a dead end for crawlers and users.",
            recommendation="Add contextual internal links to related pages (navigation, footer, or in-content links).",
            how_to_fix=["Identify related pages this page should link to.", "Add in-content or navigational links to them with descriptive anchor text."],
            expected_benefit="Improves crawl discovery of other pages and gives users a path to continue browsing.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(observed_value=0, expected_value=">0"),
        )
    else:
        b.passed("internal_linking", "Page has internal links", detail=f"{seo.internal_links} internal links")


def _check_robots_sitemap(b: CategoryBuilder, scan: ScanResults) -> None:
    extras = scan.audit_extras
    if extras is None or not extras.robots_sitemap.available:
        reason = "scan_predates_phase3_evidence_capture" if extras is None else (extras.robots_sitemap.reason or "probe_unavailable")
        b.unavailable("robots_txt_present", "robots.txt present", reason)
        b.unavailable("sitemap_present", "Sitemap declared or reachable", reason)
        return

    rs = extras.robots_sitemap
    if rs.robots_txt_present:
        b.passed("robots_txt_present", "robots.txt present", detail=f"HTTP {rs.robots_txt_status}")
        if rs.robots_txt_disallow_all:
            b.failed(
                "robots_txt_not_disallow_all", "robots.txt does not block all crawling",
                title="robots.txt disallows all crawling (Disallow: /)",
                description="robots.txt contains a blanket 'Disallow: /' rule.",
                severity=Severity.CRITICAL,
                priority=derive_priority(Severity.CRITICAL),
                impact="This blocks every compliant search engine crawler from the entire site.",
                recommendation="Remove the blanket disallow rule unless the entire site is intentionally meant to stay out of search results.",
                how_to_fix=["Open robots.txt.", "Confirm whether blocking the whole site is intentional.", "If not, remove or scope down the 'Disallow: /' rule."],
                expected_benefit="Allows the site to be crawled and indexed.",
                estimated_effort=Effort.LOW,
                evidence=Evidence(selector="robots.txt", observed_value="Disallow: /"),
            )
        else:
            b.passed("robots_txt_not_disallow_all", "robots.txt does not block all crawling")
    else:
        b.failed(
            "robots_txt_present", "robots.txt present",
            title="No robots.txt found",
            description=f"robots.txt returned HTTP {rs.robots_txt_status}.",
            severity=Severity.LOW,
            priority=derive_priority(Severity.LOW),
            impact="robots.txt is optional, but its absence means there's no explicit crawl guidance or sitemap pointer for search engines.",
            recommendation="Add a robots.txt file at the site root, even a minimal one that allows all crawling and points to the sitemap.",
            how_to_fix=["Create /robots.txt at the site root.", "Add 'User-agent: *' and 'Allow: /' (or specific disallow rules as needed).", "Add a 'Sitemap: <url>' line pointing to sitemap.xml."],
            expected_benefit="Gives search engines explicit crawl guidance and a sitemap location.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(selector="/robots.txt", observed_value=rs.robots_txt_status),
        )
        b.unavailable("robots_txt_not_disallow_all", "robots.txt does not block all crawling", "robots_txt_not_present")

    if rs.sitemap_xml_present or rs.sitemap_declared_in_robots:
        b.passed("sitemap_present", "Sitemap declared or reachable", detail="sitemap.xml reachable or declared in robots.txt")
    else:
        b.failed(
            "sitemap_present", "Sitemap declared or reachable",
            title="No sitemap.xml found",
            description="Neither /sitemap.xml nor a Sitemap: directive in robots.txt was found.",
            severity=Severity.LOW,
            priority=derive_priority(Severity.LOW),
            impact="A sitemap helps search engines discover all pages efficiently, especially on larger sites.",
            recommendation="Generate a sitemap.xml and reference it from robots.txt.",
            how_to_fix=["Generate a sitemap.xml listing the site's indexable pages.", "Publish it at /sitemap.xml.", "Add a 'Sitemap: https://.../sitemap.xml' line to robots.txt."],
            expected_benefit="Improves crawl efficiency and discovery of all site pages.",
            estimated_effort=Effort.MEDIUM,
            evidence=Evidence(selector="/sitemap.xml", observed_value=rs.sitemap_xml_status),
        )
