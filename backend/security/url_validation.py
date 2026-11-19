"""
URL validation and SSRF defense.

The scanner's whole job is "fetch whatever URL a stranger gives us" — that is
the textbook SSRF shape. This module is the single gate every URL must pass
through before a browser ever navigates to it, and `is_request_allowed` is
re-applied to every main-frame navigation (including redirects) from inside
the browser via Playwright route interception in `scanner/browser.py`, so a
hostname that resolves safely at submission time but redirects to an
internal address later is still caught.

Residual risk, stated honestly rather than silently assumed away: this
validates the DNS resolution *before* each navigation, not the live TCP
connection's peer address. A sufficiently time-boxed DNS-rebinding attack
(the DNS record changing between our check and Chromium's own connect) is a
known, hard-to-fully-close gap for any scanner built on a full browser engine
rather than a hand-rolled HTTP client with IP pinning — this module closes
the common case (direct submission of a private/loopback/link-local target,
and redirects to one) without claiming to be a formally proven SSRF-proof
system. No active/intrusive probing of any kind is performed here or
anywhere in the scanner — only passive inspection of what the target
willingly serves.
"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

_BLOCKED_HOSTNAME_SUFFIXES = (".localhost",)
_BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "ip6-localhost",
    "ip6-loopback",
    "metadata.google.internal",  # cloud metadata endpoints — never legitimate scan targets
}
_ALLOWED_SCHEMES = {"http", "https"}


class URLValidationError(ValueError):
    """Raised for any URL that must not be scanned. `code` is machine-readable for the API layer."""

    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(message)


@dataclass(frozen=True)
class ValidatedTarget:
    url: str
    hostname: str
    resolved_ips: tuple[str, ...]


def _is_blocked_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True  # unparsable address — fail closed
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def _resolve(hostname: str) -> tuple[str, ...]:
    try:
        addrinfo = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise URLValidationError(f"Could not resolve hostname: {hostname}", "dns_resolution_failed") from exc
    ips = tuple(sorted({info[4][0] for info in addrinfo}))
    if not ips:
        raise URLValidationError(f"Could not resolve hostname: {hostname}", "dns_resolution_failed")
    return ips


def validate_public_url(raw_url: str) -> ValidatedTarget:
    """Full validation for a user-submitted scan target. Raises URLValidationError on any failure."""
    raw_url = (raw_url or "").strip()
    if not raw_url:
        raise URLValidationError("Please provide a website URL.", "empty_url")

    try:
        parsed = urlparse(raw_url)
    except ValueError as exc:
        raise URLValidationError("That doesn't look like a valid URL.", "malformed_url") from exc

    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        raise URLValidationError("Only http and https URLs are supported.", "invalid_scheme")

    hostname = parsed.hostname
    if not hostname:
        raise URLValidationError("That doesn't look like a valid URL.", "malformed_url")

    return validate_hostname(hostname, context_url=raw_url)


def validate_hostname(hostname: str, *, context_url: str) -> ValidatedTarget:
    """Validates a bare hostname (used both for the initial URL and for every redirect hop)."""
    lowered = hostname.lower().rstrip(".")

    if lowered in _BLOCKED_HOSTNAMES or any(lowered.endswith(s) for s in _BLOCKED_HOSTNAME_SUFFIXES):
        raise URLValidationError("Scanning local or internal hosts is not allowed.", "blocked_host")

    # A bare IP literal in the URL — validate it directly, no DNS involved.
    try:
        literal_ip = ipaddress.ip_address(lowered)
    except ValueError:
        literal_ip = None

    if literal_ip is not None:
        if _is_blocked_ip(str(literal_ip)):
            raise URLValidationError(
                f"{literal_ip} is not a public address and cannot be scanned.", "private_address_blocked"
            )
        return ValidatedTarget(url=context_url, hostname=lowered, resolved_ips=(str(literal_ip),))

    resolved_ips = _resolve(lowered)
    for ip_str in resolved_ips:
        if _is_blocked_ip(ip_str):
            raise URLValidationError(
                f"'{hostname}' resolves to a private or internal address and cannot be scanned.",
                "private_address_blocked",
            )

    return ValidatedTarget(url=context_url, hostname=lowered, resolved_ips=resolved_ips)


_NON_NETWORK_SCHEMES = {"data", "blob", "about"}


def is_request_allowed(url: str) -> bool:
    """Lightweight boolean check for route-interception use (every in-browser navigation).

    Non-network schemes (data:/blob:/about:) carry no hostname to validate and pose no SSRF
    risk — they never leave the renderer process — so they pass through untouched. Everything
    else must be http(s) to a resolved, non-internal address.
    """
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        if scheme in _NON_NETWORK_SCHEMES:
            return True
        if scheme not in _ALLOWED_SCHEMES:
            return False
        if not parsed.hostname:
            return False
        validate_hostname(parsed.hostname, context_url=url)
        return True
    except URLValidationError:
        return False
    except Exception:
        return False
