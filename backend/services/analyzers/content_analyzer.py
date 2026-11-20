"""Content Quality (7%) — content length, duplicate/empty headings (real, from Phase 2's
extraction, unused by any other module). Grammar checking and "missing important information"
have no automatable, evidence-based check available without an NLP dependency or business-
specific rules this project doesn't have, and are reported as unavailable rather than guessed."""

from __future__ import annotations

from models.evaluation_models import CategoryResult, Effort, Evidence, Priority, Severity
from models.scan_models import ScanResults
from services.analyzers.base import CategoryBuilder
from services.severity_engine import derive_priority

_MIN_WORD_COUNT = 150


def analyze(scan: ScanResults) -> CategoryResult:
    url = scan.response.final_url or scan.submitted_url
    b = CategoryBuilder("content", url)

    if scan.extracted is None:
        b.unavailable("page_extraction", "Page content extraction", "scan_has_no_extracted_data")
        return b.build("Could not evaluate content — this scan has no extracted page data.")

    _check_content_length(b, scan)
    _check_empty_headings(b, scan)
    _check_duplicate_headings(b, scan)
    b.unavailable("grammar_quality", "No grammar issues detected", "requires_nlp_grammar_checking_not_integrated")
    b.unavailable("missing_important_info", "No obviously missing required information", "requires_business_specific_content_rules_not_automatable")

    summary = (
        f"Content analysis found {b.issue_count} issue(s) across length and heading quality."
        if b.issue_count
        else "No content issues detected across length and heading quality."
    )
    return b.build(summary)


def _check_content_length(b: CategoryBuilder, scan: ScanResults) -> None:
    word_count = scan.extracted.content.word_count
    if word_count >= _MIN_WORD_COUNT:
        b.passed("sufficient_content_length", "Page has substantive text content", detail=f"{word_count} words")
    else:
        b.failed(
            "sufficient_content_length", "Page has substantive text content",
            title=f"Low word count ({word_count} words)",
            description=f"The page's visible text content is {word_count} words, below the {_MIN_WORD_COUNT}-word reference point used here.",
            severity=Severity.LOW,
            priority=derive_priority(Severity.LOW),
            impact="Very thin content gives search engines and visitors little to evaluate the page on, though this is a soft signal — some pages (e.g. a single-purpose landing page) are legitimately short.",
            recommendation="If this page is meant to be a substantive content page, expand it with genuinely useful detail rather than padding.",
            how_to_fix=["Confirm whether this page is intended to be a content/informational page.", "If so, add genuinely useful detail — specifics, examples, or answers to likely visitor questions."],
            expected_benefit="Gives visitors and search engines more substance to evaluate the page on.",
            estimated_effort=Effort.MEDIUM,
            evidence=Evidence(observed_value=word_count, expected_value=f">={_MIN_WORD_COUNT}"),
        )


def _check_empty_headings(b: CategoryBuilder, scan: ScanResults) -> None:
    empty = scan.extracted.content.empty_headings
    if empty == 0:
        b.passed("no_empty_headings", "No empty heading elements")
    else:
        b.failed(
            "no_empty_headings", "No empty heading elements",
            title=f"{empty} empty heading element(s) found",
            description="One or more heading tags (h1-h6) contain no text content.",
            severity=Severity.LOW,
            priority=derive_priority(Severity.LOW),
            impact="An empty heading is a broken or leftover element that provides no value and can confuse screen-reader users navigating by heading.",
            recommendation="Remove empty heading elements, or fill them with their intended content.",
            how_to_fix=["Find the empty heading tag(s) in the markup.", "Either populate them with real text or remove the element if it's unused."],
            expected_benefit="Cleans up the document outline for all users.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(selector="h1, h2, h3, h4, h5, h6", observed_value=empty, expected_value=0),
        )


def _check_duplicate_headings(b: CategoryBuilder, scan: ScanResults) -> None:
    duplicates = scan.extracted.content.duplicate_headings
    if not duplicates:
        b.passed("no_duplicate_headings", "No duplicate heading text")
    else:
        b.failed(
            "no_duplicate_headings", "No duplicate heading text",
            title=f"{len(duplicates)} heading text value(s) repeated on the page",
            description=f"These heading texts appear more than once: {', '.join(duplicates[:5])}.",
            severity=Severity.LOW,
            priority=derive_priority(Severity.LOW),
            impact="Repeated heading text makes it harder for users navigating by heading (including screen-reader users) to tell sections apart.",
            recommendation="Make each heading's text distinct and specific to its section.",
            how_to_fix=[f"Review these repeated headings: {', '.join(duplicates[:5])}.", "Rewrite each to be specific to its own section's content."],
            expected_benefit="Makes heading-based navigation meaningfully distinguish each section.",
            estimated_effort=Effort.LOW,
            evidence=Evidence(selector="h1, h2, h3, h4, h5, h6", observed_value=duplicates[:10]),
        )
