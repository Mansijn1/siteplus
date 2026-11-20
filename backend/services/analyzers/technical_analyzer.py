"""Technical SEO & Architecture (5%) — HTTP-level implementation: status code, redirect chain
length, Content-Type correctness, and the X-Robots-Tag HTTP header (a genuinely distinct
indexability control from the SEO module's <meta name="robots"> check — same intent, different
mechanism, so checking both isn't a duplicate). Canonical configuration and meta-robots are
explicitly left to the SEO module (not re-derived here) per the spec's own instruction not to
duplicate SEO's findings; those checks are marked unavailable with that reasoning stated plainly
rather than silently omitted."""

from __future__ import annotations

from models.evaluation_models import CategoryResult, Effort, Evidence, Priority, Severity
from models.scan_models import ScanResults
from services.analyzers.base import CategoryBuilder
from services.severity_engine import derive_priority


def analyze(scan: ScanResults) -> CategoryResult:
    url = scan.response.final_url or scan.submitted_url
    b = CategoryBuilder("technical", url)

    _check_http_status(b, scan)
    _check_redirect_chain(b, scan)
    _check_content_type(b, scan)
    _check_x_robots_tag(b, scan)

    b.unavailable("canonical_configuration", "Canonical URL correctly configured", "owned_by_seo_module_to_avoid_duplicate_issues")
    b.unavailable("duplicate_page_indicators", "No duplicate-page indicators", "requires_crawl_based_duplicate_detection_out_of_scope_for_a_single_page_scan")

    summary = (
        f"Technical analysis found {b.issue_count} issue(s) in HTTP-level implementation."
        if b.issue_count
        else "No technical implementation issues detected at the HTTP level."
    )
    return b.build(summary)


def _check_http_status(b: CategoryBuilder, scan: ScanResults) -> None:
    status = scan.response.status_code
    if status is not None and 200 <= status < 300:
        b.passed("http_status_ok", "Page returns a successful (2xx) HTTP status", detail=str(status))
    else:
        b.failed(
            "http_status_ok", "Page returns a successful (2xx) HTTP status",
            title=f"Page returned HTTP {status}",
            description=f"The final response for this page returned status code {status}, not a 2xx success.",
            severity=Severity.CRITICAL,
            priority=derive_priority(Severity.CRITICAL),
            impact="A non-2xx status on the canonical URL for this page can prevent indexing and signals an error state to both users and crawlers.",
            recommendation="Investigate why this page isn't returning a 2xx status and fix the underlying routing/server issue.",
            how_to_fix=["Check server/application logs for this specific route.", "Confirm the route/page handler is correctly configured."],
            expected_benefit="Restores normal access and indexability for this page.",
            estimated_effort=Effort.MEDIUM,
            evidence=Evidence(observed_value=status, expected_value="2xx"),
        )


def _check_redirect_chain(b: CategoryBuilder, scan: ScanResults) -> None:
    count = len(scan.response.redirect_chain)
    if count <= 1:
        b.passed("redirect_chain_minimal", "Redirect chain is short (0-1 hops)", detail=f"{count} hop(s)")
    else:
        b.failed(
            "redirect_chain_minimal", "Redirect chain is short (0-1 hops)",
            title=f"Submitted URL required {count} redirect hops to reach its final destination",
            description=f"Redirect chain: {' -> '.join(scan.response.redirect_chain)}" if scan.response.redirect_chain else f"{count} redirect hops observed.",
            severity=Severity.MEDIUM,
            priority=derive_priority(Severity.MEDIUM),
            impact="Each redirect hop adds a round trip before the page can load, and long chains are more fragile (one broken hop breaks the whole chain).",
            recommendation="Update the originally-linked/submitted URL to point directly at the final destination, removing intermediate hops.",
            how_to_fix=["Identify the full redirect chain.", "Update internal links, bookmarks, or canonical references to point straight at the final URL.", "Remove unnecessary intermediate redirect rules."],
            expected_benefit="Reduces latency and fragility from unnecessary redirect hops.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(observed_value=scan.response.redirect_chain, expected_value="<=1 hop"),
        )


def _check_content_type(b: CategoryBuilder, scan: ScanResults) -> None:
    if scan.extracted is None:
        b.unavailable("content_type_header_correct", "Content-Type header correctly declares text/html", "no_extracted_data")
        return
    headers = {k.lower(): v for k, v in scan.extracted.technical.response_headers.items()}
    content_type = headers.get("content-type", "")
    if "text/html" in content_type.lower():
        b.passed("content_type_header_correct", "Content-Type header correctly declares text/html", detail=content_type)
    else:
        b.failed(
            "content_type_header_correct", "Content-Type header correctly declares text/html",
            title=f"Content-Type header is '{content_type or 'missing'}', not text/html",
            description="An HTML page should be served with a Content-Type header that includes text/html.",
            severity=Severity.MEDIUM,
            priority=derive_priority(Severity.MEDIUM),
            impact="An incorrect Content-Type can cause browsers to misinterpret or refuse to render the page correctly.",
            recommendation="Configure the server to serve this route with 'Content-Type: text/html; charset=utf-8'.",
            how_to_fix=["Check the server/framework's response header configuration for this route.", "Set Content-Type explicitly to text/html; charset=utf-8."],
            expected_benefit="Ensures browsers interpret and render the page as intended.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(selector="response header: content-type", observed_value=content_type, expected_value="text/html"),
        )


def _check_x_robots_tag(b: CategoryBuilder, scan: ScanResults) -> None:
    if scan.extracted is None:
        b.unavailable("x_robots_tag_not_blocking", "X-Robots-Tag HTTP header not blocking indexing", "no_extracted_data")
        return
    headers = {k.lower(): v for k, v in scan.extracted.technical.response_headers.items()}
    x_robots = headers.get("x-robots-tag")
    if x_robots and "noindex" in x_robots.lower():
        b.failed(
            "x_robots_tag_not_blocking", "X-Robots-Tag HTTP header not blocking indexing",
            title="X-Robots-Tag HTTP header contains noindex",
            description=f"The response includes 'X-Robots-Tag: {x_robots}'.",
            severity=Severity.CRITICAL,
            priority=derive_priority(Severity.CRITICAL),
            impact="This is a server-level indexing block that applies regardless of the page's own <meta name=\"robots\"> tag — search engines will not index this page.",
            recommendation="Remove the noindex directive from the X-Robots-Tag response header if this page should be indexable.",
            how_to_fix=["Confirm whether this page is intentionally excluded from search at the server level.", "If not, remove or update the X-Robots-Tag header configuration."],
            expected_benefit="Allows the page to be indexed by search engines.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(selector="response header: x-robots-tag", observed_value=x_robots),
        )
    else:
        b.passed("x_robots_tag_not_blocking", "X-Robots-Tag HTTP header not blocking indexing")
