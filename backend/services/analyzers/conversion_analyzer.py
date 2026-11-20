"""Conversion Optimization (7%) — lead-capture mechanism and contact-info discoverability, from
real form counts and link-presence signals. Deliberately narrower than UX's broader "is there
any clickable action" check: this module asks the business-outcome-specific question of whether
a visitor can actually leave contact details or start an inquiry. Trust-elements-near-CTA,
value-proposition clarity, and multi-step signup friction all require either DOM-proximity
layout analysis or content/NLP understanding this project doesn't have — reported unavailable."""

from __future__ import annotations

from models.evaluation_models import CategoryResult, Effort, Evidence, Priority, Severity
from models.scan_models import ScanResults
from services.analyzers.base import CategoryBuilder
from services.severity_engine import derive_priority


def analyze(scan: ScanResults) -> CategoryResult:
    url = scan.response.final_url or scan.submitted_url
    b = CategoryBuilder("conversion", url)

    if scan.extracted is None:
        b.unavailable("page_extraction", "Page content extraction", "scan_has_no_extracted_data")
        return b.build("Could not evaluate conversion signals — this scan has no extracted page data.")

    _check_lead_capture(b, scan)
    _check_contact_discoverable(b, scan)
    b.unavailable("trust_elements_near_cta", "Trust elements present near calls-to-action", "requires_dom_proximity_layout_analysis_not_automated")
    b.unavailable("value_proposition_clarity", "Value proposition is clearly stated", "requires_nlp_content_understanding_not_automatable")
    b.unavailable("signup_flow_frictionless", "Signup/inquiry flow has low friction", "requires_multi_step_flow_testing_out_of_scope_for_a_passive_single_page_scan")

    summary = (
        f"Conversion analysis found {b.issue_count} issue(s) in lead-capture and contact discoverability."
        if b.issue_count
        else "No issues detected in lead-capture and contact discoverability; several deeper conversion checks require manual review."
    )
    return b.build(summary)


def _check_lead_capture(b: CategoryBuilder, scan: ScanResults) -> None:
    forms = scan.extracted.ux.forms
    if forms > 0:
        b.passed("lead_capture_mechanism_present", "A lead-capture or inquiry form is present", detail=f"{forms} form(s)")
    else:
        b.failed(
            "lead_capture_mechanism_present", "A lead-capture or inquiry form is present",
            title="No lead-capture or inquiry form found on this page",
            description="The scanned page has zero <form> elements.",
            severity=Severity.MEDIUM,
            priority=derive_priority(Severity.MEDIUM),
            impact="Without a form (contact, signup, quote request, etc.), interested visitors on this page have no direct way to convert into a lead.",
            recommendation="Add a lead-capture mechanism appropriate to this page — a contact form, newsletter signup, or inquiry form.",
            how_to_fix=["Decide what conversion action makes sense for this specific page.", "Add a short, low-friction form for that action (name + contact method is often enough to start)."],
            expected_benefit="Gives interested visitors a direct path to convert, rather than relying on them finding contact info elsewhere.",
            estimated_effort=Effort.MEDIUM,
            evidence=Evidence(selector="form", observed_value=0, expected_value=">0"),
        )


def _check_contact_discoverable(b: CategoryBuilder, scan: ScanResults) -> None:
    signals = scan.extracted.page_signals
    if signals.has_contact_link or scan.extracted.ux.forms > 0:
        b.passed("contact_info_discoverable", "Contact information or a contact path is discoverable")
    else:
        b.failed(
            "contact_info_discoverable", "Contact information or a contact path is discoverable",
            title="No contact link or form found on this page",
            description="No link with 'contact'-like href/text, and no form, was found on the scanned page.",
            severity=Severity.MEDIUM,
            priority=derive_priority(Severity.MEDIUM),
            impact="A visitor who wants to reach the business from this page has no obvious path to do so.",
            recommendation="Add a visible link to a contact page, or contact details/a form directly on this page.",
            how_to_fix=["Add a 'Contact' link in the navigation or footer if one doesn't already exist.", "Alternatively, add direct contact details or a short inquiry form on this page itself."],
            expected_benefit="Gives visitors a clear way to get in touch, supporting conversion.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(observed_value=False, expected_value=True),
        )
