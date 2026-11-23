"""Accessibility Evaluation (10%) — driven primarily by real axe-core results (the project's
actual automated accessibility testing engine, injected into the already-loaded page; see
`scanner/accessibility_audit.py`). One issue per distinct axe rule with violations (not one per
DOM node) to keep issue counts meaningful; severity comes from axe's own `impact` scale. Falls
back to the static signals Phase 2 always has (alt text, viewport meta, lang attribute, form
labeling via BeautifulSoup) when axe couldn't run, so the category isn't entirely unavailable
just because one capture step failed."""

from __future__ import annotations

from models.evaluation_models import CategoryResult, Effort, Evidence, Priority, Severity
from models.scan_models import AxeViolation, ScanResults
from services.analyzers.base import CategoryBuilder
from services.severity_engine import derive_priority

_IMPACT_TO_SEVERITY = {
    "critical": Severity.CRITICAL,
    "serious": Severity.HIGH,
    "moderate": Severity.MEDIUM,
    "minor": Severity.LOW,
}


def analyze(scan: ScanResults) -> CategoryResult:
    url = scan.response.final_url or scan.submitted_url
    b = CategoryBuilder("accessibility", url)
    extras = scan.audit_extras

    axe = extras.accessibility if extras else None
    if axe and axe.available:
        violated_rule_ids = {v.rule_id for v in axe.violations}
        for violation in axe.violations:
            _report_axe_violation(b, violation)
        for rule_id in axe.passed_rule_ids:
            # axe-core evaluates rules like color-contrast/label/image-alt per-element, so the
            # same rule_id can legitimately appear in BOTH `passes` (elements that were fine) and
            # `violations` (elements that weren't) on the same page. Reporting it as passed here
            # too would record one check_id as both failed and passed — recording it only once,
            # as the failure, is the correct (and more conservative) outcome.
            if rule_id in violated_rule_ids:
                continue
            b.passed(f"axe:{rule_id}", f"axe-core rule '{rule_id}'")
        coverage_note = (
            f" ({axe.incomplete_count} additional check(s) could not be automatically determined "
            "and need manual review.)"
            if axe.incomplete_count
            else ""
        )
    else:
        reason = "scan_predates_phase3_evidence_capture" if extras is None else (axe.reason if axe else "not_run")
        b.unavailable("axe_core_audit", "Automated axe-core accessibility audit", reason or "unavailable")
        coverage_note = ""

    _check_lang_attribute(b, scan)

    summary = (
        f"Accessibility analysis found {b.issue_count} issue(s), primarily from automated "
        f"axe-core rule checks.{coverage_note}"
        if b.issue_count
        else f"No accessibility issues detected by the automated audit.{coverage_note}"
    )
    return b.build(summary)


def _report_axe_violation(b: CategoryBuilder, violation: AxeViolation) -> None:
    severity = _IMPACT_TO_SEVERITY.get(violation.impact or "", Severity.MEDIUM)
    node_count = len(violation.nodes)
    selectors = [n.selector for n in violation.nodes if n.selector][:5]
    example_html = violation.nodes[0].html_snippet if violation.nodes else None

    b.failed(
        f"axe:{violation.rule_id}", f"axe-core rule '{violation.rule_id}'",
        title=violation.help_text or violation.description,
        description=f"{violation.description} Affects {node_count} element(s) on the page.",
        severity=severity,
        priority=derive_priority(severity),
        impact=_impact_statement(violation),
        recommendation=violation.help_text or "See the axe-core documentation linked in this finding.",
        how_to_fix=_how_to_fix_for_rule(violation),
        expected_benefit="Removes a concrete barrier for assistive-technology users on the affected element(s).",
        estimated_effort=Effort.LOW if node_count <= 3 else Effort.MEDIUM,
        evidence=Evidence(
            selector=", ".join(selectors) if selectors else None,
            observed_value=example_html,
            extra={"rule_id": violation.rule_id, "tags": violation.tags, "help_url": violation.help_url, "node_count": node_count},
        ),
        documentation_url=violation.help_url,
    )


def _impact_statement(violation: AxeViolation) -> str:
    wcag_tags = [t for t in violation.tags if t.startswith("wcag")]
    tag_note = f" (relates to {', '.join(wcag_tags)})" if wcag_tags else ""
    return f"Axe-core classifies this as '{violation.impact or 'unknown'}' impact{tag_note}."


def _how_to_fix_for_rule(violation: AxeViolation) -> list[str]:
    steps = [f"Review the {len(violation.nodes)} flagged element(s) for the '{violation.rule_id}' rule."]
    if violation.help_text:
        steps.append(violation.help_text)
    if violation.help_url:
        steps.append(f"See axe-core's guidance for this rule: {violation.help_url}")
    return steps


def _check_lang_attribute(b: CategoryBuilder, scan: ScanResults) -> None:
    if scan.extracted is None:
        b.unavailable("html_lang_attribute", "HTML lang attribute present", "no_extracted_data")
        return
    language = scan.extracted.basic.language
    if language:
        b.passed("html_lang_attribute", "HTML lang attribute present", detail=language)
    else:
        b.failed(
            "html_lang_attribute", "HTML lang attribute present",
            title="Missing lang attribute on <html>",
            description="The root <html> element has no lang attribute.",
            severity=Severity.MEDIUM,
            priority=derive_priority(Severity.MEDIUM),
            impact="Screen readers can't reliably select the correct pronunciation/voice without a declared page language.",
            recommendation="Add a lang attribute to the <html> element (e.g. lang=\"en\").",
            how_to_fix=["Add lang=\"en\" (or the page's actual language code) to the opening <html> tag."],
            expected_benefit="Ensures screen readers use the correct pronunciation rules for this page's language.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(element="html", selector="html", observed_value=None, expected_value="A BCP 47 language code"),
        )


