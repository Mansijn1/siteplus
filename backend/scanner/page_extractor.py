"""Static content/SEO extraction from the page's rendered HTML (post-JavaScript DOM, taken
from Playwright's `page.content()` — not a second raw fetch) via BeautifulSoup. Purely passive
parsing: no requests, no form submission, no execution of anything on the page."""

from __future__ import annotations

import json
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

from models.scan_models import (
    BasicInfo,
    ContentInfo,
    HeadingInfo,
    PageSignalsInfo,
    SeoInfo,
    StructuredDataInfo,
    UxInfo,
)

_WORD_RE = re.compile(r"[A-Za-z0-9']+")

_SOCIAL_HOSTS = {
    "facebook.com": "facebook",
    "twitter.com": "twitter",
    "x.com": "twitter",
    "instagram.com": "instagram",
    "linkedin.com": "linkedin",
    "youtube.com": "youtube",
    "tiktok.com": "tiktok",
}

_LINK_PATTERNS: dict[str, re.Pattern] = {
    "contact": re.compile(r"contact", re.I),
    "about": re.compile(r"/about|^about$", re.I),
    "privacy": re.compile(r"privacy", re.I),
    "terms": re.compile(r"terms", re.I),
    "pricing": re.compile(r"pricing|/plans", re.I),
}


def extract_basic_info(html: str, submitted_url: str, final_url: str) -> BasicInfo:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title and soup.title.string else None
    description_tag = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
    canonical_tag = soup.find("link", rel=re.compile("^canonical$", re.I))
    html_tag = soup.find("html")

    return BasicInfo(
        url=submitted_url,
        final_url=final_url,
        title=title,
        meta_description=(description_tag.get("content") or "").strip() if description_tag else None,
        canonical_url=(canonical_tag.get("href") or "").strip() if canonical_tag else None,
        language=html_tag.get("lang") if html_tag else None,
        html_size_bytes=len(html.encode("utf-8")),
    )


def extract_seo_info(html: str, final_url: str) -> SeoInfo:
    soup = BeautifulSoup(html, "html.parser")
    parsed_final = urlparse(final_url)

    headings: list[HeadingInfo] = []
    heading_counts = {f"h{i}": 0 for i in range(1, 7)}
    for level in range(1, 7):
        for tag in soup.find_all(f"h{level}"):
            text = tag.get_text(strip=True)
            headings.append(HeadingInfo(level=level, text=text))
            heading_counts[f"h{level}"] += 1

    images = soup.find_all("img")
    images_missing_alt = sum(1 for img in images if not (img.get("alt") or "").strip())

    robots_tag = soup.find("meta", attrs={"name": re.compile("^robots$", re.I)})

    og_tags: dict[str, str] = {}
    for tag in soup.find_all("meta", property=re.compile("^og:", re.I)):
        prop = tag.get("property")
        content = tag.get("content")
        if prop and content:
            og_tags[prop] = content

    internal_links = 0
    external_links = 0
    internal_link_urls: list[str] = []
    seen_internal: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith("#") or href.startswith("mailto:") or href.startswith("tel:"):
            continue
        link_host = urlparse(href).hostname
        if link_host is None or link_host == parsed_final.hostname:
            internal_links += 1
            absolute = urljoin(final_url, href).split("#", 1)[0]
            if absolute not in seen_internal and len(internal_link_urls) < 25:
                seen_internal.add(absolute)
                internal_link_urls.append(absolute)
        else:
            external_links += 1

    return SeoInfo(
        headings=headings,
        heading_counts=heading_counts,
        images_total=len(images),
        images_missing_alt=images_missing_alt,
        meta_robots=(robots_tag.get("content") or "").strip() if robots_tag else None,
        open_graph=og_tags,
        internal_links=internal_links,
        external_links=external_links,
        internal_link_urls=internal_link_urls,
        structured_data=_extract_structured_data(soup),
    )


def _extract_structured_data(soup: BeautifulSoup) -> StructuredDataInfo:
    scripts = soup.find_all("script", attrs={"type": re.compile("^application/ld\\+json$", re.I)})
    types: list[str] = []
    for script in scripts:
        try:
            payload = json.loads(script.string or "")
        except (ValueError, TypeError):
            continue
        entries = payload if isinstance(payload, list) else [payload]
        for entry in entries:
            if isinstance(entry, dict) and entry.get("@type"):
                type_value = entry["@type"]
                types.append(type_value if isinstance(type_value, str) else str(type_value))
    return StructuredDataInfo(has_json_ld=len(scripts) > 0, json_ld_types=types[:10], count=len(scripts))


def extract_content_info(html: str, seo: SeoInfo) -> ContentInfo:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    visible_text = soup.get_text(separator=" ")
    word_count = len(_WORD_RE.findall(visible_text))

    main_sections = len(soup.find_all(["main", "article", "section"])) or len(
        BeautifulSoup(html, "html.parser").find_all(["section", "article"])
    )

    empty_headings = sum(1 for h in seo.headings if not h.text)
    seen: dict[str, int] = {}
    for h in seo.headings:
        key = h.text.strip().lower()
        if key:
            seen[key] = seen.get(key, 0) + 1
    duplicate_headings = [text for text, count in seen.items() if count > 1]

    return ContentInfo(
        word_count=word_count,
        main_sections=main_sections,
        empty_headings=empty_headings,
        duplicate_headings=duplicate_headings[:20],
    )


def extract_page_signals(html: str) -> PageSignalsInfo:
    """Single pass over the same <a href> elements `extract_seo_info` already iterates —
    detects presence of key page links by href/anchor-text pattern. This is a presence signal
    only: it does not verify the linked destination page's content."""
    soup = BeautifulSoup(html, "html.parser")
    found: dict[str, bool] = {key: False for key in _LINK_PATTERNS}
    social_platforms: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(strip=True)
        haystack = f"{href} {text}".lower()
        if not href:
            continue

        for key, pattern in _LINK_PATTERNS.items():
            if not found[key] and pattern.search(haystack):
                found[key] = True

        host = urlparse(href).hostname or ""
        for social_host, platform in _SOCIAL_HOSTS.items():
            if host == social_host or host.endswith(f".{social_host}"):
                social_platforms.add(platform)

    manifest_tag = soup.find("link", rel=re.compile("^manifest$", re.I))
    theme_color_tag = soup.find("meta", attrs={"name": re.compile("^theme-color$", re.I)})

    return PageSignalsInfo(
        has_contact_link=found["contact"],
        has_about_link=found["about"],
        has_privacy_link=found["privacy"],
        has_terms_link=found["terms"],
        has_pricing_link=found["pricing"],
        social_platforms=sorted(social_platforms),
        has_manifest_link=manifest_tag is not None,
        has_theme_color_meta=theme_color_tag is not None,
    )


def extract_ux_info(html: str, viewport_overflow: bool | None) -> UxInfo:
    soup = BeautifulSoup(html, "html.parser")
    viewport_tag = soup.find("meta", attrs={"name": re.compile("^viewport$", re.I)})

    return UxInfo(
        nav_elements=len(soup.find_all("nav")),
        buttons=len(soup.find_all("button")) + len(soup.find_all("input", attrs={"type": "submit"})),
        links=len(soup.find_all("a", href=True)),
        forms=len(soup.find_all("form")),
        input_fields=len(soup.find_all("input")) + len(soup.find_all("textarea")) + len(soup.find_all("select")),
        has_viewport_meta=viewport_tag is not None,
        viewport_content=(viewport_tag.get("content") or "").strip() if viewport_tag else None,
        horizontal_overflow=viewport_overflow,
    )
