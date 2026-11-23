"""Optional, LLM-assisted SEO judgment — strictly additive to the rule-based `seo_analyzer.py`,
never a replacement for it: the core evaluation works fully without this (per the spec's own
"core evaluation must work without an external LLM API" requirement). It judges things the rule
-based checks structurally can't: whether the title/meta description actually read as compelling
and specific (not just present and the right length), whether the visible content seems to
substantively cover its apparent topic, and what obviously-related subtopics/keywords seem
missing. Every judgment is grounded in real evidence (title, meta description, headings, a
content excerpt) handed to the model in the prompt — never a fact invented about the page — and
the model is never allowed to override or contradict the rule-based analyzer's own findings; it
only adds new, separately-tagged checks (`llm:*`) at a lower confidence tier (see
confidence_engine.py's `llm_assessment` source) and `needs_review` verification status, since an
LLM's qualitative judgment is never independently verified the way a DOM fact is.

Uses OpenAI (model configurable via `settings.llm_seo_agent_model`). Activates only when
`OPENAI_API_KEY` is set in the environment — with no key (the default, and always true in CI/
the benchmark), every check here reports `unavailable` with zero network calls, exactly like
Lighthouse's "cli not found" path. Any API error, timeout, or malformed response degrades the
same way — this module never fabricates a finding from a failed or unparseable call."""

from __future__ import annotations

import json

from config import settings
from models.evaluation_models import CategoryResult, Effort, Evidence, Priority, Severity
from models.scan_models import ScanResults
from services.analyzers.base import CategoryBuilder
from services.severity_engine import derive_priority
from services.validation_engine import validate_category_result

_SYSTEM_PROMPT = """You are an SEO content reviewer. You will be given a web page's title, meta \
description, heading outline, and an excerpt of its visible text. Judge ONLY what is given to \
you — never assume or invent facts about the page, its business, or content you were not shown. \
If the excerpt is too short or unclear to judge something, say so honestly rather than guessing.

Respond with ONLY a JSON object in exactly this shape, no other text:
{
  "title_quality": {"verdict": "good" | "needs_improvement", "explanation": "one or two sentences, citing the actual title text"},
  "content_relevance": {"verdict": "good" | "needs_improvement", "explanation": "one or two sentences, citing specifics from the excerpt"},
  "keyword_coverage": {"verdict": "good" | "needs_improvement", "explanation": "one or two sentences", "missing_topics": ["short phrase", "..."]}
}

"needs_improvement" on title_quality means the title is generic, keyword-stuffed, or doesn't \
specifically reflect the page's content. "needs_improvement" on content_relevance means the \
visible text doesn't clearly or substantively address what the title/headings promise. \
"missing_topics" should only list topics a reader would reasonably expect given the title/\
headings but that the excerpt doesn't address — leave it empty if you're not confident."""


class LlmSeoAgentError(Exception):
    pass


def _build_user_prompt(scan: ScanResults) -> str:
    basic = scan.extracted.basic
    headings = [f"H{h.level}: {h.text}" for h in scan.extracted.seo.headings[:20]]
    excerpt = scan.extracted.content.content_excerpt or "(no visible text extracted)"
    return (
        f"Title: {basic.title or '(none)'}\n"
        f"Meta description: {basic.meta_description or '(none)'}\n"
        f"Heading outline:\n" + "\n".join(headings) + "\n\n"
        f"Visible text excerpt (first ~1500 characters):\n{excerpt}"
    )


async def _call_openai(scan: ScanResults) -> dict:
    from openai import APIError, APITimeoutError, AsyncOpenAI, AuthenticationError, RateLimitError

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    try:
        response = await client.chat.completions.create(
            model=settings.llm_seo_agent_model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(scan)},
            ],
            response_format={"type": "json_object"},
            temperature=0,
            timeout=settings.llm_seo_agent_timeout_s,
        )
    except AuthenticationError as exc:
        raise LlmSeoAgentError(f"invalid_api_key: {exc}") from exc
    except RateLimitError as exc:
        raise LlmSeoAgentError(f"rate_limited: {exc}") from exc
    except APITimeoutError as exc:
        raise LlmSeoAgentError(f"timed_out: {exc}") from exc
    except APIError as exc:
        raise LlmSeoAgentError(f"api_error: {exc}") from exc

    content = response.choices[0].message.content if response.choices else None
    if not content:
        raise LlmSeoAgentError("empty_response")
    try:
        parsed = json.loads(content)
    except (ValueError, TypeError) as exc:
        raise LlmSeoAgentError(f"response_not_valid_json: {exc}") from exc

    for key in ("title_quality", "content_relevance", "keyword_coverage"):
        if key not in parsed or "verdict" not in parsed[key]:
            raise LlmSeoAgentError(f"response_missing_expected_field: {key}")
    return parsed


async def analyze_seo_with_llm(scan: ScanResults) -> CategoryResult:
    url = scan.response.final_url or scan.submitted_url
    b = CategoryBuilder("seo", url)

    if not settings.openai_api_key:
        b.unavailable("llm:title_quality", "AI-assessed title quality", "openai_api_key_not_configured")
        b.unavailable("llm:content_relevance", "AI-assessed content relevance", "openai_api_key_not_configured")
        b.unavailable("llm:keyword_coverage", "AI-assessed keyword coverage", "openai_api_key_not_configured")
        return b.build("LLM-assisted SEO judgment is not configured (no OPENAI_API_KEY).")

    if scan.extracted is None:
        reason = "scan_has_no_extracted_data"
        b.unavailable("llm:title_quality", "AI-assessed title quality", reason)
        b.unavailable("llm:content_relevance", "AI-assessed content relevance", reason)
        b.unavailable("llm:keyword_coverage", "AI-assessed keyword coverage", reason)
        return b.build("Could not run LLM-assisted SEO judgment — this scan has no extracted page data.")

    try:
        result = await _call_openai(scan)
    except LlmSeoAgentError as exc:
        reason = str(exc)[:200]
        b.unavailable("llm:title_quality", "AI-assessed title quality", reason)
        b.unavailable("llm:content_relevance", "AI-assessed content relevance", reason)
        b.unavailable("llm:keyword_coverage", "AI-assessed keyword coverage", reason)
        return b.build(f"LLM-assisted SEO judgment failed: {reason}")

    _apply_verdict(
        b, "llm:title_quality", "AI-assessed title quality", result["title_quality"],
        title_if_failed="Title doesn't read as specific or compelling",
        impact="A generic or keyword-stuffed title is less likely to earn clicks in search results, even if it technically passes length checks.",
        recommendation="Rewrite the title to be specific to this page's actual content and value, not just keyword-present.",
        effort=Effort.LOW,
    )
    _apply_verdict(
        b, "llm:content_relevance", "AI-assessed content relevance", result["content_relevance"],
        title_if_failed="Visible content doesn't clearly address what the title/headings promise",
        impact="Search engines and visitors alike judge relevance from the actual body content — a mismatch between what's promised and what's delivered hurts both rankings and engagement.",
        recommendation="Revise the content so it substantively delivers on what the title and headings promise.",
        effort=Effort.MEDIUM,
    )
    keyword_result = result["keyword_coverage"]
    missing_topics = keyword_result.get("missing_topics") or []
    _apply_verdict(
        b, "llm:keyword_coverage", "AI-assessed keyword/topic coverage", keyword_result,
        title_if_failed=f"Possibly missing coverage of: {', '.join(missing_topics[:5])}" if missing_topics else "Possible gaps in topic coverage",
        impact="Missing coverage of closely related subtopics can mean losing search traffic to competitors who address them.",
        recommendation="Consider adding sections addressing the listed subtopics, if they're genuinely relevant to this page's purpose.",
        effort=Effort.MEDIUM,
        extra={"missing_topics": missing_topics},
    )

    summary = (
        f"AI-assisted SEO judgment found {b.issue_count} area(s) for improvement, based on the "
        "page's title, meta description, headings, and a content excerpt. These are qualitative "
        "judgments (lower confidence, flagged for review), not deterministic facts."
        if b.issue_count
        else "AI-assisted SEO judgment found no issues with title quality, content relevance, or keyword coverage."
    )
    return validate_category_result(b.build(summary))


def _apply_verdict(
    b: CategoryBuilder, check_id: str, label: str, verdict_obj: dict, *,
    title_if_failed: str, impact: str, recommendation: str, effort: Effort, extra: dict | None = None,
) -> None:
    explanation = verdict_obj.get("explanation", "")
    if verdict_obj.get("verdict") == "good":
        b.passed(check_id, label, detail=explanation[:200])
        return
    severity = Severity.LOW
    b.failed(
        check_id, label,
        title=title_if_failed,
        description=explanation or "The model flagged this as needing improvement.",
        severity=severity,
        priority=derive_priority(severity),
        impact=impact,
        recommendation=recommendation,
        how_to_fix=[explanation] if explanation else [recommendation],
        expected_benefit=impact,
        estimated_effort=effort,
        evidence=Evidence(observed_value=explanation, extra=extra or {}),
    )
