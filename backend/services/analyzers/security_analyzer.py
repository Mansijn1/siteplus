"""Website Security (8%) — HTTPS/TLS, security response headers, mixed content, and cookie
attributes, all from evidence Phase 2's browser session already captured passively (response
headers, TLS details via Playwright's own `security_details()`, HTML scanned for http:// resource
references). Purely passive: no exploitation, no intrusive scanning, per the spec's own
constraint — this only reads what the server and page already publicly expose."""

from __future__ import annotations

from models.evaluation_models import CategoryResult, Effort, Evidence, Priority, Severity
from models.scan_models import ScanResults
from services.analyzers.base import CategoryBuilder
from services.severity_engine import derive_priority

_SECURITY_HEADERS: list[tuple[str, Severity, str]] = [
    ("strict-transport-security", Severity.HIGH, "Forces browsers to always use HTTPS for this origin, preventing downgrade attacks."),
    ("content-security-policy", Severity.MEDIUM, "Restricts which sources of scripts/styles/etc. the browser will execute, mitigating XSS impact."),
    ("x-frame-options", Severity.MEDIUM, "Prevents the page from being embedded in a hostile iframe (clickjacking)."),
    ("x-content-type-options", Severity.LOW, "Prevents the browser from MIME-sniffing a response away from its declared content type."),
    ("referrer-policy", Severity.LOW, "Controls how much of this page's URL is leaked via the Referer header when users click outbound links."),
]


def analyze(scan: ScanResults) -> CategoryResult:
    url = scan.response.final_url or scan.submitted_url
    b = CategoryBuilder("security", url)

    _check_https(b, scan)
    _check_tls_cert(b, scan)
    _check_mixed_content(b, scan)
    _check_security_headers(b, scan)
    _check_cookie_attributes(b, scan)

    b.unavailable(
        "exposed_sensitive_info", "No sensitive information exposed in page content",
        "requires_raw_page_text_scan_not_persisted_by_phase_2_extraction",
    )

    summary = (
        f"Security analysis found {b.issue_count} issue(s) across transport security, headers, and cookies."
        if b.issue_count
        else "No security issues detected across transport security, headers, and cookies."
    )
    return b.build(summary)


def _check_https(b: CategoryBuilder, scan: ScanResults) -> None:
    if scan.response.https:
        b.passed("https_enabled", "Site served over HTTPS")
    else:
        b.failed(
            "https_enabled", "Site served over HTTPS",
            title="Site is not served over HTTPS",
            description=f"The final URL '{scan.response.final_url}' uses plain HTTP.",
            severity=Severity.CRITICAL,
            priority=derive_priority(Severity.CRITICAL),
            impact="All traffic (including any form submissions) is unencrypted and can be intercepted or modified in transit. Most browsers also flag plain-HTTP sites as 'Not Secure'.",
            recommendation="Obtain a TLS certificate and serve the entire site over HTTPS, redirecting HTTP to HTTPS.",
            how_to_fix=["Provision a TLS certificate (e.g. via Let's Encrypt or your host/CDN).", "Configure the server to redirect all HTTP requests to HTTPS.", "Add HSTS once HTTPS is confirmed working site-wide."],
            expected_benefit="Encrypts all traffic and removes browser 'Not Secure' warnings.",
            estimated_effort=Effort.MEDIUM,
            evidence=Evidence(observed_value="http", expected_value="https"),
        )


def _check_tls_cert(b: CategoryBuilder, scan: ScanResults) -> None:
    extras = scan.audit_extras
    if extras is None or not extras.tls.available:
        if scan.response.https:
            reason = "scan_predates_phase3_evidence_capture" if extras is None else (extras.tls.reason or "unavailable")
            b.unavailable("tls_certificate_valid", "TLS certificate details available", reason)
        else:
            b.unavailable("tls_certificate_valid", "TLS certificate details available", "site_not_https")
        return
    # Playwright having returned security details at all means the connection completed a
    # successful TLS handshake — an actually-invalid/expired cert fails navigation outright
    # (surfaced instead as a navigation_failed scan error), so reaching here is itself the pass.
    b.passed("tls_certificate_valid", "TLS certificate details available", detail=f"{extras.tls.protocol}, issuer: {extras.tls.issuer}")


def _check_mixed_content(b: CategoryBuilder, scan: ScanResults) -> None:
    extras = scan.audit_extras
    if extras is None or not extras.mixed_content.available:
        b.unavailable("no_mixed_content", "No insecure (http://) resources on an HTTPS page", "scan_predates_phase3_evidence_capture" if extras is None else "unavailable")
        return
    mc = extras.mixed_content
    if mc.insecure_resource_count == 0:
        b.passed("no_mixed_content", "No insecure (http://) resources on an HTTPS page")
    else:
        b.failed(
            "no_mixed_content", "No insecure (http://) resources on an HTTPS page",
            title=f"{mc.insecure_resource_count} insecure (http://) resource reference(s) found on an HTTPS page",
            description="The page is served over HTTPS but references one or more resources via plain http://.",
            severity=Severity.MEDIUM,
            priority=derive_priority(Severity.MEDIUM),
            impact="Browsers may block or warn about mixed content, and insecure subresources can be tampered with in transit even though the main page is encrypted.",
            recommendation="Update all resource references to use https:// (or protocol-relative URLs).",
            how_to_fix=[f"Find and update these references: {', '.join(mc.insecure_resource_examples) or 'see evidence'}.", "Change their src/href from http:// to https://."],
            expected_benefit="Removes mixed-content browser warnings and closes a tampering vector on those subresources.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(observed_value=mc.insecure_resource_examples, extra={"count": mc.insecure_resource_count}),
        )


def _check_security_headers(b: CategoryBuilder, scan: ScanResults) -> None:
    if scan.extracted is None:
        for header_name, _sev, _why in _SECURITY_HEADERS:
            b.unavailable(f"header:{header_name}", f"'{header_name}' header present", "no_extracted_data")
        return

    headers = {k.lower(): v for k, v in scan.extracted.technical.response_headers.items()}
    for header_name, severity, why in _SECURITY_HEADERS:
        if header_name in headers:
            b.passed(f"header:{header_name}", f"'{header_name}' header present", detail=headers[header_name][:100])
        else:
            b.failed(
                f"header:{header_name}", f"'{header_name}' header present",
                title=f"Missing '{header_name}' response header",
                description=f"The response for this page does not include a '{header_name}' header.",
                severity=severity,
                priority=derive_priority(severity),
                impact=why,
                recommendation=f"Add the '{header_name}' header to the server's response configuration.",
                how_to_fix=[f"Configure the web server or application framework to send a '{header_name}' header on every response.", "Verify the header is present using browser dev tools or curl -I."],
                expected_benefit=why,
                estimated_effort=Effort.LOW,
                evidence=Evidence(selector=f"response header: {header_name}", observed_value=None),
            )


def _check_cookie_attributes(b: CategoryBuilder, scan: ScanResults) -> None:
    if scan.extracted is None:
        b.unavailable("cookie_security_attributes", "Cookies set with Secure/HttpOnly/SameSite attributes", "no_extracted_data")
        return
    headers = {k.lower(): v for k, v in scan.extracted.technical.response_headers.items()}
    set_cookie = headers.get("set-cookie")
    if not set_cookie:
        b.unavailable("cookie_security_attributes", "Cookies set with Secure/HttpOnly/SameSite attributes", "no_cookies_set_on_this_response")
        return
    lowered = set_cookie.lower()
    missing = [attr for attr in ("secure", "httponly", "samesite") if attr not in lowered]
    if not missing:
        b.passed("cookie_security_attributes", "Cookies set with Secure/HttpOnly/SameSite attributes")
    else:
        b.failed(
            "cookie_security_attributes", "Cookies set with Secure/HttpOnly/SameSite attributes",
            title=f"Cookie missing recommended attribute(s): {', '.join(missing)}",
            description=f"The Set-Cookie header observed on this response is missing: {', '.join(missing)}. Note: only the main document response's cookie header was inspected.",
            severity=Severity.MEDIUM,
            priority=derive_priority(Severity.MEDIUM),
            impact="Missing Secure/HttpOnly/SameSite attributes increase exposure to cookie theft via XSS or cross-site request forgery.",
            recommendation=f"Add the missing attribute(s) ({', '.join(missing)}) to the cookie's Set-Cookie header.",
            how_to_fix=[f"Update the server/application's cookie-setting code to include: {', '.join(missing)}.", "Re-check the Set-Cookie header with browser dev tools after the change."],
            expected_benefit="Reduces cookie theft risk from XSS and cross-site request forgery.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(selector="response header: set-cookie", observed_value=set_cookie[:200], extra={"missing": missing}),
        )
