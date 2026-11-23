"""Shared fixtures for Phase 3 tests. `make_scan_results()` builds a complete, valid
`ScanResults` tree with sensible "healthy page" defaults — individual tests override only the
specific fields they care about, so each test's intent (what evidence is different, and why
that should change the result) stays readable instead of buried in setup boilerplate."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

from models.scan_models import (  # noqa: E402
    AccessibilityAudit,
    AuditExtras,
    BasicInfo,
    ContentInfo,
    ExtractedData,
    HeadingInfo,
    ImageDiagnostics,
    LoadTiming,
    MixedContentInfo,
    PageSignalsInfo,
    ResponseInfo,
    RobotsSitemapInfo,
    ScanResults,
    SeoInfo,
    TechnicalInfo,
    TlsCertificateInfo,
    TouchTargetSignal,
    TypographySignal,
    UxInfo,
)


def make_scan_results(
    *,
    url: str = "https://example.test/",
    title: str | None = "A Reasonably Descriptive Page Title For Testing",
    meta_description: str | None = "A sufficiently detailed meta description for testing purposes, "
    "roughly in the recommended length range for search engine snippets here.",
    canonical_url: str | None = "https://example.test/",
    language: str | None = "en",
    headings: list[HeadingInfo] | None = None,
    images_total: int = 2,
    images_missing_alt: int = 0,
    meta_robots: str | None = None,
    open_graph: dict | None = None,
    internal_links: int = 5,
    external_links: int = 1,
    internal_link_urls: list[str] | None = None,
    word_count: int = 400,
    main_sections: int = 2,
    empty_headings: int = 0,
    duplicate_headings: list[str] | None = None,
    https: bool = True,
    status_code: int = 200,
    redirect_chain: list[str] | None = None,
    response_headers: dict | None = None,
    script_count: int = 5,
    stylesheet_count: int = 2,
    failed_requests: list | None = None,
    nav_elements: int = 1,
    buttons: int = 2,
    links: int = 10,
    forms: int = 1,
    input_fields: int = 3,
    has_viewport_meta: bool = True,
    viewport_content: str | None = "width=device-width, initial-scale=1",
    horizontal_overflow: bool | None = False,
    has_contact_link: bool = True,
    has_about_link: bool = True,
    has_privacy_link: bool = True,
    has_terms_link: bool = True,
    has_pricing_link: bool = False,
    social_platforms: list[str] | None = None,
    has_manifest_link: bool = True,
    has_theme_color_meta: bool = True,
    console_messages: list | None = None,
    extracted: ExtractedData | None = "default",  # type: ignore[assignment]
    audit_extras: AuditExtras | None | str = "default",
    lighthouse: dict | None = None,
) -> ScanResults:
    if headings is None:
        headings = [HeadingInfo(level=1, text="Main Heading"), HeadingInfo(level=2, text="Subheading")]
    if open_graph is None:
        open_graph = {"og:title": "Title", "og:description": "Description", "og:image": "https://example.test/img.png"}
    if duplicate_headings is None:
        duplicate_headings = []
    if redirect_chain is None:
        redirect_chain = []
    if response_headers is None:
        response_headers = {
            "content-type": "text/html; charset=utf-8",
            "strict-transport-security": "max-age=63072000",
            "content-security-policy": "default-src 'self'",
            "x-frame-options": "DENY",
            "x-content-type-options": "nosniff",
            "referrer-policy": "strict-origin-when-cross-origin",
        }
    if failed_requests is None:
        failed_requests = []
    if social_platforms is None:
        social_platforms = ["linkedin"]
    if console_messages is None:
        console_messages = []

    if extracted == "default":
        extracted = ExtractedData(
            basic=BasicInfo(
                url=url, final_url=url, title=title, meta_description=meta_description,
                canonical_url=canonical_url, language=language, html_size_bytes=10_000,
            ),
            seo=SeoInfo(
                headings=headings,
                heading_counts={f"h{i}": sum(1 for h in headings if h.level == i) for i in range(1, 7)},
                images_total=images_total, images_missing_alt=images_missing_alt,
                meta_robots=meta_robots, open_graph=open_graph,
                internal_links=internal_links, external_links=external_links,
                internal_link_urls=internal_link_urls or [],
            ),
            content=ContentInfo(
                word_count=word_count, main_sections=main_sections,
                empty_headings=empty_headings, duplicate_headings=duplicate_headings,
            ),
            technical=TechnicalInfo(
                https=https, status_code=status_code, was_redirected=len(redirect_chain) > 0,
                redirect_count=len(redirect_chain), response_headers=response_headers,
                image_count=images_total, script_count=script_count, stylesheet_count=stylesheet_count,
                failed_requests=failed_requests,
            ),
            ux=UxInfo(
                nav_elements=nav_elements, buttons=buttons, links=links, forms=forms,
                input_fields=input_fields, has_viewport_meta=has_viewport_meta,
                viewport_content=viewport_content, horizontal_overflow=horizontal_overflow,
            ),
            page_signals=PageSignalsInfo(
                has_contact_link=has_contact_link, has_about_link=has_about_link,
                has_privacy_link=has_privacy_link, has_terms_link=has_terms_link,
                has_pricing_link=has_pricing_link, social_platforms=social_platforms,
                has_manifest_link=has_manifest_link, has_theme_color_meta=has_theme_color_meta,
            ),
        )

    if audit_extras == "default":
        audit_extras = AuditExtras(
            accessibility=AccessibilityAudit(available=True, violations=[], passed_rule_ids=["image-alt", "label", "color-contrast"], passes_count=3, incomplete_count=0),
            tls=TlsCertificateInfo(available=https, protocol="TLS 1.3", issuer="Test CA", valid_from=0, valid_to=0, subject_name="example.test") if https else TlsCertificateInfo(available=False, reason="not_https_or_unavailable"),
            typography=TypographySignal(available=True, distinct_font_families=2, distinct_font_sizes=5, font_family_samples=["Inter, sans-serif"]),
            images=ImageDiagnostics(available=True, total_checked=images_total, broken_count=0, oversized_count=0),
            touch_targets=TouchTargetSignal(available=True, total_checked=5, undersized_count=0),
            robots_sitemap=RobotsSitemapInfo(available=True, robots_txt_present=True, robots_txt_status=200, robots_txt_disallow_all=False, sitemap_declared_in_robots=True, sitemap_xml_present=True, sitemap_xml_status=200),
            mixed_content=MixedContentInfo(available=True, insecure_resource_count=0),
        )

    return ScanResults(
        scan_id="test-scan",
        submitted_url=url,
        extracted=extracted,
        screenshots={},
        lighthouse=lighthouse or {},
        console_messages=console_messages,
        response=ResponseInfo(status_code=status_code, final_url=url, redirect_chain=redirect_chain, headers=response_headers, https=https),
        load_timing=LoadTiming(response_time_ms=300, dom_content_loaded_ms=500, load_event_ms=800),
        audit_extras=audit_extras,
        started_at="2026-01-01T00:00:00+00:00",
        completed_at="2026-01-01T00:00:05+00:00",
    )
