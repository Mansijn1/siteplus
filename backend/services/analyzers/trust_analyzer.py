"""Trust & Credibility (5%) — presence of about/privacy/terms links and social profile links,
from the same page-signal extraction Conversion uses, but asked as a credibility question
("does this site show its identity and policies") rather than a conversion-path question.
HTTPS is deliberately not re-checked here — Security already owns that finding. Testimonials/
reviews presence and structured business-identity info would need content classification this
project doesn't have, and are reported unavailable rather than guessed from link presence alone."""

from __future__ import annotations

from models.evaluation_models import CategoryResult, Effort, Evidence, Priority, Severity
from models.scan_models import ScanResults
from services.analyzers.base import CategoryBuilder
from services.severity_engine import derive_priority


def analyze(scan: ScanResults) -> CategoryResult:
    url = scan.response.final_url or scan.submitted_url
    b = CategoryBuilder("trust", url)

    if scan.extracted is None:
        b.unavailable("page_extraction", "Page content extraction", "scan_has_no_extracted_data")
        return b.build("Could not evaluate trust signals — this scan has no extracted page data.")

    signals = scan.extracted.page_signals

    _check_link_signal(b, "about_page_linked", "A link to an About page is present", signals.has_about_link,
                        "No link to an About page was found",
                        "Visitors and search engines commonly look for an About page to understand who runs the site.",
                        "Add a visible link to an About/Company page.")
    _check_link_signal(b, "privacy_policy_linked", "A link to a Privacy Policy is present", signals.has_privacy_link,
                        "No link to a Privacy Policy was found",
                        "A missing privacy policy is both a trust gap for visitors and, depending on jurisdiction, a compliance gap.",
                        "Add a Privacy Policy page and link to it (commonly in the footer).")
    _check_link_signal(b, "terms_linked", "A link to Terms & Conditions is present", signals.has_terms_link,
                        "No link to Terms & Conditions was found",
                        "Terms & Conditions set expectations for site/service use and are a standard credibility signal.",
                        "Add a Terms & Conditions page and link to it (commonly in the footer).")

    if signals.social_platforms:
        b.passed("social_links_present", "Social media profile links present", detail=", ".join(signals.social_platforms))
    else:
        b.failed(
            "social_links_present", "Social media profile links present",
            title="No social media profile links found",
            description="No links to known social platforms (Facebook, X/Twitter, Instagram, LinkedIn, YouTube, TikTok) were found.",
            severity=Severity.LOW,
            priority=derive_priority(Severity.LOW),
            impact="Social links are a common, low-effort credibility signal for visitors evaluating whether a business is active and legitimate.",
            recommendation="Add links to the business's active social media profiles, commonly in the header or footer.",
            how_to_fix=["Identify the business's active social profiles.", "Add linked icons/text in the footer or header."],
            expected_benefit="Gives visitors an additional, low-effort credibility signal.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(observed_value=[]),
        )

    b.unavailable("testimonials_or_reviews_present", "Testimonials or reviews present", "requires_content_classification_not_automatable_from_structural_evidence_alone")
    b.unavailable("business_identity_info", "Structured business identity information present", "requires_structured_business_data_detection_beyond_current_scope")

    summary = (
        f"Trust analysis found {b.issue_count} issue(s) in credibility-related page links."
        if b.issue_count
        else "No issues detected in credibility-related page links; some trust signals (testimonials, structured business info) require manual review."
    )
    return b.build(summary)


def _check_link_signal(
    b: CategoryBuilder, check_id: str, label: str, present: bool,
    title: str, impact: str, recommendation: str,
) -> None:
    if present:
        b.passed(check_id, label)
    else:
        b.failed(
            check_id, label,
            title=title,
            description=f"{title} on the scanned page (checked by link href/anchor-text pattern).",
            severity=Severity.LOW,
            priority=derive_priority(Severity.LOW),
            impact=impact,
            recommendation=recommendation,
            how_to_fix=[recommendation],
            expected_benefit="Improves visitor trust and site credibility.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(observed_value=False, expected_value=True),
        )
