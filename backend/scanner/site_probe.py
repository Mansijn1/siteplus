"""Two small, passive same-origin HTTP GETs for robots.txt and sitemap.xml — plain HTTP
requests to paths any visitor's browser (or crawler) can also fetch, not browser automation.
Run independently of the Playwright scan so a slow/unavailable robots.txt can't block it."""

from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse

import httpx

from config import settings
from models.scan_models import RobotsSitemapInfo

_SITEMAP_RE = re.compile(r"(?im)^\s*sitemap:\s*(\S+)")
_DISALLOW_ALL_RE = re.compile(r"(?im)^\s*disallow:\s*/\s*$")


async def probe_robots_and_sitemap(final_url: str) -> RobotsSitemapInfo:
    parsed = urlparse(final_url)
    if not parsed.scheme or not parsed.netloc:
        return RobotsSitemapInfo(available=False, reason="invalid_final_url")

    origin = f"{parsed.scheme}://{parsed.netloc}"
    robots_url = urljoin(origin + "/", "robots.txt")

    robots_present = False
    robots_status: int | None = None
    disallow_all = False
    sitemap_declared = False
    declared_sitemap_url: str | None = None

    try:
        async with httpx.AsyncClient(
            timeout=settings.site_probe_timeout_s, follow_redirects=True, verify=True
        ) as client:
            try:
                resp = await client.get(robots_url)
                robots_status = resp.status_code
                if resp.status_code == 200:
                    robots_present = True
                    body = resp.text[:20_000]
                    disallow_all = bool(_DISALLOW_ALL_RE.search(body))
                    sitemap_match = _SITEMAP_RE.search(body)
                    if sitemap_match:
                        sitemap_declared = True
                        declared_sitemap_url = sitemap_match.group(1).strip()
            except httpx.HTTPError:
                pass  # robots.txt unreachable — reported as not present, not a scan failure

            sitemap_url = declared_sitemap_url or urljoin(origin + "/", "sitemap.xml")
            sitemap_present = False
            sitemap_status: int | None = None
            try:
                resp = await client.head(sitemap_url)
                if resp.status_code == 405:  # some servers reject HEAD; fall back to GET
                    resp = await client.get(sitemap_url)
                sitemap_status = resp.status_code
                sitemap_present = resp.status_code == 200
            except httpx.HTTPError:
                pass
    except Exception as exc:  # noqa: BLE001 — this probe degrades, it never fails the evaluation
        return RobotsSitemapInfo(available=False, reason=f"probe_error: {exc}"[:300])

    return RobotsSitemapInfo(
        available=True,
        robots_txt_present=robots_present,
        robots_txt_status=robots_status,
        robots_txt_disallow_all=disallow_all,
        sitemap_declared_in_robots=sitemap_declared,
        sitemap_xml_present=sitemap_present,
        sitemap_xml_status=sitemap_status,
    )
