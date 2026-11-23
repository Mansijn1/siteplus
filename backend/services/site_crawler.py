"""Discovers same-domain page URLs to evaluate beyond the homepage, from two passive signals
Phase 2 already collects on the homepage scan: its sitemap.xml (preferred — a more authoritative
statement of the site's indexable pages) and its internal navigation links. Bounded to one hop
from the homepage (it does not crawl the links found ON discovered pages) — this keeps crawl
cost predictable and avoids the unbounded recursive crawling the spec explicitly doesn't ask
for ("configurable maximum pages", not "crawl the whole site"). Never discovers or returns a
cross-domain URL."""

from __future__ import annotations

from urllib.parse import urlparse


def normalize_url(url: str) -> str:
    """Collapses trivial duplicates (trailing slash, differing only in that) to the same key."""
    parsed = urlparse(url)
    path = parsed.path.rstrip("/") or "/"
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def discover_pages(
    homepage_url: str,
    internal_link_urls: list[str],
    sitemap_urls: list[str],
    max_pages: int,
) -> list[str]:
    """Returns up to `max_pages` URLs, homepage first, same-domain only, deduplicated."""
    homepage_host = urlparse(homepage_url).hostname
    discovered: list[str] = [homepage_url]
    seen = {normalize_url(homepage_url)}

    for candidates in (sitemap_urls, internal_link_urls):
        if len(discovered) >= max_pages:
            break
        for url in candidates:
            if len(discovered) >= max_pages:
                break
            if urlparse(url).hostname != homepage_host:
                continue
            normalized = normalize_url(url)
            if normalized in seen:
                continue
            seen.add(normalized)
            discovered.append(url)

    return discovered[:max_pages]
