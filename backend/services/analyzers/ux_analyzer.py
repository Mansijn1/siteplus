"""User Experience Evaluation (12%) — navigation structure, form usability, content structure,
and JS runtime errors as a broken-interaction signal. Internal linking (SEO's discoverability
angle) and resource-load failures (Performance's angle) are deliberately not re-raised here to
avoid duplicate issues across modules; this module's console-error check is a distinct signal
(runtime script errors, not failed network requests) that neither other module inspects."""

from __future__ import annotations

from models.evaluation_models import CategoryResult, Effort, Evidence, Priority, Severity
from models.scan_models import ScanResults
from services.analyzers.base import CategoryBuilder
from services.severity_engine import derive_priority


def analyze(scan: ScanResults) -> CategoryResult:
    url = scan.response.final_url or scan.submitted_url
    b = CategoryBuilder("ux", url)

    if scan.extracted is None:
        b.unavailable("page_extraction", "Page content extraction", "scan_has_no_extracted_data")
        return b.build("Could not evaluate UX — this scan has no extracted page data.")

    _check_navigation_landmark(b, scan)
    _check_forms_have_inputs(b, scan)
    _check_structured_content(b, scan)
    _check_ctas_present(b, scan)
    _check_console_errors(b, scan)

    summary = (
        f"UX analysis found {b.issue_count} issue(s) across navigation, forms, and runtime behavior."
        if b.issue_count
        else "No UX issues detected across navigation, forms, and runtime behavior."
    )
    return b.build(summary)


def _check_navigation_landmark(b: CategoryBuilder, scan: ScanResults) -> None:
    nav_count = scan.extracted.ux.nav_elements
    if nav_count > 0:
        b.passed("navigation_landmark_present", "Navigation landmark present", detail=f"{nav_count} <nav> element(s)")
    else:
        b.failed(
            "navigation_landmark_present", "Navigation landmark present",
            title="No <nav> landmark found",
            description="The page has no <nav> element.",
            severity=Severity.MEDIUM,
            priority=derive_priority(Severity.MEDIUM),
            impact="Without a clear navigation landmark, both sighted users scanning the layout and assistive-technology users lose an easy way to find site-wide navigation.",
            recommendation="Wrap the primary navigation menu in a <nav> element.",
            how_to_fix=["Identify the primary navigation menu markup.", "Wrap it in a <nav> element (or add role=\"navigation\") if it isn't already."],
            expected_benefit="Gives users and assistive technology a clear, consistent place to find site navigation.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(selector="nav", observed_value=0, expected_value=">0"),
        )


def _check_forms_have_inputs(b: CategoryBuilder, scan: ScanResults) -> None:
    ux = scan.extracted.ux
    if ux.forms == 0:
        b.unavailable("forms_have_inputs", "Forms contain usable input fields", "no_forms_on_page")
        return
    if ux.input_fields > 0:
        b.passed("forms_have_inputs", "Forms contain usable input fields", detail=f"{ux.forms} form(s), {ux.input_fields} input(s)")
    else:
        b.failed(
            "forms_have_inputs", "Forms contain usable input fields",
            title=f"{ux.forms} form(s) found with no input fields",
            description="A <form> element exists on the page, but no <input>, <textarea>, or <select> elements were found.",
            severity=Severity.HIGH,
            priority=derive_priority(Severity.HIGH),
            impact="A form with no fields can't collect any data from the user — it's effectively broken.",
            recommendation="Verify the form renders its expected fields; check for a JavaScript error preventing fields from rendering.",
            how_to_fix=["Load the page and inspect the form in dev tools.", "Check the browser console for JS errors around form initialization.", "Confirm the expected <input>/<select>/<textarea> elements are present in the rendered DOM."],
            expected_benefit="Restores basic form functionality.",
            estimated_effort=Effort.MEDIUM,
            evidence=Evidence(selector="form", observed_value=0, expected_value=">0", extra={"form_count": ux.forms}),
        )


def _check_structured_content(b: CategoryBuilder, scan: ScanResults) -> None:
    main_sections = scan.extracted.content.main_sections
    if main_sections > 0:
        b.passed("structured_content_sections", "Page uses structural sectioning elements", detail=f"{main_sections} section(s)")
    else:
        b.failed(
            "structured_content_sections", "Page uses structural sectioning elements",
            title="No <main>, <section>, or <article> elements found",
            description="The page's content isn't broken into any semantic sectioning elements.",
            severity=Severity.LOW,
            priority=derive_priority(Severity.LOW),
            impact="Without semantic sections, users (and assistive technology navigating by region) have no structural way to jump between parts of the page.",
            recommendation="Wrap distinct content areas in semantic <main>/<section>/<article> elements.",
            how_to_fix=["Identify the page's distinct content areas (hero, main content, sidebar, etc.).", "Wrap the primary content in <main>, and distinct sub-areas in <section>/<article>."],
            expected_benefit="Improves structural navigation for all users and assistive technology.",
            estimated_effort=Effort.MEDIUM,
            evidence=Evidence(selector="main, section, article", observed_value=0, expected_value=">0"),
        )


def _check_ctas_present(b: CategoryBuilder, scan: ScanResults) -> None:
    ux = scan.extracted.ux
    if ux.buttons > 0 or ux.forms > 0:
        b.passed("ctas_or_forms_present", "Clear calls-to-action or forms present", detail=f"{ux.buttons} button(s), {ux.forms} form(s)")
    else:
        b.failed(
            "ctas_or_forms_present", "Clear calls-to-action or forms present",
            title="No buttons or forms found on the page",
            description="The page has zero <button>/submit-input elements and zero <form> elements.",
            severity=Severity.MEDIUM,
            priority=derive_priority(Severity.MEDIUM),
            impact="A page with no clear action elements gives visitors no obvious next step, which tends to hurt engagement and conversion.",
            recommendation="Add a clear primary call-to-action appropriate to this page's purpose (e.g. a button or a contact/signup form).",
            how_to_fix=["Decide this page's single most important next action for a visitor.", "Add a visually prominent button or form for that action."],
            expected_benefit="Gives visitors a clear next step, typically improving engagement.",
            estimated_effort=Effort.MEDIUM,
            evidence=Evidence(observed_value={"buttons": ux.buttons, "forms": ux.forms}, expected_value=">0 of either"),
        )


def _check_console_errors(b: CategoryBuilder, scan: ScanResults) -> None:
    errors = [m for m in scan.console_messages if m.type == "error"]
    if len(errors) == 0:
        b.passed("no_js_console_errors", "No JavaScript console errors on load")
    else:
        examples = [e.text[:150] for e in errors[:5]]
        severity = Severity.HIGH if len(errors) > 5 else Severity.MEDIUM
        b.failed(
            "no_js_console_errors", "No JavaScript console errors on load",
            title=f"{len(errors)} JavaScript console error(s) during page load",
            description="One or more script errors were logged to the browser console while the page loaded.",
            severity=severity,
            priority=derive_priority(severity),
            impact="Console errors often indicate broken interactive functionality (a handler that never attaches, a component that fails to render) even when the page otherwise looks fine.",
            recommendation="Investigate and fix the logged JavaScript errors.",
            how_to_fix=[f"Review these console errors: {'; '.join(examples)}.", "Reproduce each in a browser with dev tools open to find the failing script/line."],
            expected_benefit="Fixes whatever interactive functionality these errors were silently breaking.",
            estimated_effort=Effort.MEDIUM,
            evidence=Evidence(observed_value=examples, extra={"total_errors": len(errors)}),
        )
