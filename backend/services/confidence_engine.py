"""Evidence verification + confidence scoring — the layer between the 12 analyzers' raw issues
and the final issue list the API/dashboard sees. Confidence is a rule-based estimate of how
directly the underlying evidence supports a finding (a missing HTML attribute is a fact; a
2.5x image-size ratio is a judgment call) — NOT severity, and NOT the website score. These are
explicitly seed values, not statistically calibrated ones: Stage H's benchmark framework is what
actually checks whether e.g. "axe-core violations deserve 0.90" holds up against ground truth.
Per the spec, these bands must be configurable and are not claimed as validated accuracy until
that benchmark says so.

Confidence is keyed by `check_id` (stable across every analyzer run and every page — see
services/analyzers/base.py's docstring on why check_id, not issue_id, is the stable identifier)
rather than guessed from the issue text, so this mapping is exhaustive and auditable in one place
instead of inferred by fragile string matching."""

from __future__ import annotations

from models.evaluation_models import ConfidenceLevel, Evidence, Issue, VerificationStatus

# Evidence source -> confidence. Ordered from most to least direct:
#   rendered_dom / http_response / site_probe: a directly observed fact (an attribute is there
#     or it isn't; a header was sent or it wasn't) — as close to "ground truth" as this system
#     gets without a second human reviewer.
#   external_tool: axe-core / Lighthouse — mature, independently-maintained tools, but their own
#     docs acknowledge false positives/incompletes exist, so not quite "fact" tier.
#   heuristic_threshold: a numeric judgment call this project made up (44px touch targets, 2.5x
#     oversized-image ratio, a word-count floor) — a real signal, but the threshold itself is
#     debatable, which is exactly why it's lower confidence rather than lower severity.
#   structural_proxy: an indirect signal standing in for something we can't directly observe
#     (e.g. a JS console error as evidence of "broken interaction").
_SOURCE_CONFIDENCE: dict[str, float] = {
    "rendered_dom": 0.97,
    "http_response": 0.96,
    "site_probe": 0.95,
    "external_tool": 0.90,
    "heuristic_threshold": 0.65,
    "structural_proxy": 0.55,
}

_CHECK_ID_SOURCE: dict[str, str] = {
    # SEO
    "title_present": "rendered_dom",
    "title_length": "rendered_dom",
    "meta_description_present": "rendered_dom",
    "meta_description_length": "rendered_dom",
    "single_h1": "rendered_dom",
    "heading_hierarchy": "rendered_dom",
    "canonical_present": "rendered_dom",
    "robots_meta_not_blocking": "rendered_dom",
    "open_graph_present": "rendered_dom",
    "images_alt_text": "rendered_dom",
    "internal_linking": "rendered_dom",
    "robots_txt_present": "site_probe",
    "robots_txt_not_disallow_all": "site_probe",
    "sitemap_present": "site_probe",
    "structured_data_present": "rendered_dom",
    # Accessibility
    "html_lang_attribute": "rendered_dom",
    # Mobile
    "viewport_meta": "rendered_dom",
    "horizontal_overflow": "rendered_dom",
    "touch_target_size": "heuristic_threshold",
    "mobile_render": "http_response",
    # Security
    "https_enabled": "http_response",
    "tls_certificate_valid": "http_response",
    "no_mixed_content": "rendered_dom",
    "cookie_security_attributes": "http_response",
    # Performance
    "lighthouse_performance_score": "external_tool",
    "response_time": "http_response",
    "resource_count": "heuristic_threshold",
    "no_failed_resource_requests": "http_response",
    # Content
    "sufficient_content_length": "heuristic_threshold",
    "no_empty_headings": "rendered_dom",
    "no_duplicate_headings": "rendered_dom",
    # UX
    "navigation_landmark_present": "rendered_dom",
    "forms_have_inputs": "rendered_dom",
    "structured_content_sections": "rendered_dom",
    "ctas_or_forms_present": "rendered_dom",
    "no_js_console_errors": "structural_proxy",
    # UI
    "font_family_consistency": "heuristic_threshold",
    "font_size_consistency": "heuristic_threshold",
    "no_broken_images": "rendered_dom",
    "images_not_oversized": "heuristic_threshold",
    "heading_size_hierarchy": "rendered_dom",
    "alignment_consistency": "heuristic_threshold",
    # Conversion
    "lead_capture_mechanism_present": "rendered_dom",
    "contact_info_discoverable": "rendered_dom",
    # Trust
    "about_page_linked": "rendered_dom",
    "privacy_policy_linked": "rendered_dom",
    "terms_linked": "rendered_dom",
    "social_links_present": "rendered_dom",
    # Cross-page (website-level evaluation only)
    "broken_internal_link_crosspage": "http_response",
    # Technical
    "http_status_ok": "http_response",
    "redirect_chain_minimal": "http_response",
    "content_type_header_correct": "http_response",
    "x_robots_tag_not_blocking": "http_response",
    # Innovation
    "pwa_manifest_present": "rendered_dom",
    "theme_color_configured": "rendered_dom",
}

_PREFIX_SOURCE: list[tuple[str, str]] = [
    ("axe:", "external_tool"),
    ("metric:", "external_tool"),
    ("header:", "http_response"),
]


def _evidence_source_for(check_id: str) -> str:
    if check_id in _CHECK_ID_SOURCE:
        return _CHECK_ID_SOURCE[check_id]
    for prefix, source in _PREFIX_SOURCE:
        if check_id.startswith(prefix):
            return source
    return "heuristic_threshold"  # unmapped check_id — default to a conservative mid confidence


def _confidence_level(confidence: float) -> ConfidenceLevel:
    if confidence >= 0.90:
        return ConfidenceLevel.VERY_HIGH
    if confidence >= 0.75:
        return ConfidenceLevel.HIGH
    if confidence >= 0.50:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


def _has_concrete_evidence(evidence: Evidence) -> bool:
    # `extra["check_id"]` is injected onto every issue automatically (services/analyzers/base.py)
    # and so is always present — it doesn't count as "concrete evidence" on its own, or this
    # check would never fire. Any OTHER extra key (e.g. axe's rule_id/tags/node_count) does.
    extra_beyond_check_id = {k: v for k, v in evidence.extra.items() if k != "check_id"}
    return bool(evidence.observed_value is not None or evidence.selector or evidence.element or extra_beyond_check_id)


def verify_and_score(issue: Issue) -> Issue:
    """Applied once per issue, right after an analyzer produces it (see evaluation_engine.py).
    Never mutates severity/priority/score — only adds the confidence/verification metadata."""
    check_id = issue.evidence.extra.get("check_id") if issue.evidence.extra else None
    source = _evidence_source_for(check_id) if check_id else "heuristic_threshold"
    confidence = _SOURCE_CONFIDENCE[source]

    if not _has_concrete_evidence(issue.evidence):
        # An issue with no concrete evidence attached is a real gap regardless of its source's
        # usual confidence — it can't be verified against anything, so it's marked down rather
        # than trusted at the source's normal level.
        confidence = min(confidence, 0.6)
        verification = VerificationStatus.NEEDS_REVIEW
    elif source in ("heuristic_threshold", "structural_proxy"):
        verification = VerificationStatus.NEEDS_REVIEW
    else:
        verification = VerificationStatus.VERIFIED

    return issue.model_copy(
        update={
            "confidence": confidence,
            "confidence_level": _confidence_level(confidence),
            "verification_status": verification,
            "evidence_source": source,
        }
    )
