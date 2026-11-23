from __future__ import annotations

from unittest.mock import AsyncMock, patch

from config import settings
from models.evaluation_models import CheckStatus, ConfidenceLevel, VerificationStatus
from services.llm_seo_agent import LlmSeoAgentError, analyze_seo_with_llm
from tests.conftest import make_scan_results


def _check(result, check_id: str):
    return next(c for c in result.checks if c.check_id == check_id)


async def test_no_api_key_degrades_to_unavailable_with_zero_network_calls():
    assert settings.openai_api_key is None  # the default, asserted so this test fails loudly if that ever changes
    scan = make_scan_results()
    with patch("services.llm_seo_agent._call_openai", new_callable=AsyncMock) as mock_call:
        result = await analyze_seo_with_llm(scan)
        mock_call.assert_not_called()
    assert _check(result, "llm:title_quality").status == CheckStatus.UNAVAILABLE
    assert _check(result, "llm:title_quality").detail == "openai_api_key_not_configured"
    assert result.score is None  # every check unavailable -> no score, never a fabricated one


async def test_good_verdicts_produce_passed_checks():
    scan = make_scan_results()
    mock_response = {
        "title_quality": {"verdict": "good", "explanation": "Specific and relevant."},
        "content_relevance": {"verdict": "good", "explanation": "Matches the heading outline."},
        "keyword_coverage": {"verdict": "good", "explanation": "Covers the expected topics.", "missing_topics": []},
    }
    with patch("config.settings.openai_api_key", "sk-test"), \
         patch("services.llm_seo_agent._call_openai", new_callable=AsyncMock, return_value=mock_response):
        result = await analyze_seo_with_llm(scan)
    assert _check(result, "llm:title_quality").status == CheckStatus.PASSED
    assert _check(result, "llm:content_relevance").status == CheckStatus.PASSED
    assert _check(result, "llm:keyword_coverage").status == CheckStatus.PASSED
    assert result.score == 100.0


async def test_needs_improvement_verdicts_produce_low_confidence_issues():
    scan = make_scan_results()
    mock_response = {
        "title_quality": {"verdict": "needs_improvement", "explanation": "Too generic."},
        "content_relevance": {"verdict": "good", "explanation": "Fine."},
        "keyword_coverage": {
            "verdict": "needs_improvement", "explanation": "Missing a subtopic.",
            "missing_topics": ["pricing", "return policy"],
        },
    }
    with patch("config.settings.openai_api_key", "sk-test"), \
         patch("services.llm_seo_agent._call_openai", new_callable=AsyncMock, return_value=mock_response):
        result = await analyze_seo_with_llm(scan)

    title_issue = next(i for i in result.issues if i.evidence.extra.get("check_id") == "llm:title_quality")
    assert title_issue.confidence_level == ConfidenceLevel.MEDIUM
    assert title_issue.verification_status == VerificationStatus.NEEDS_REVIEW
    assert title_issue.evidence_source == "llm_assessment"

    keyword_issue = next(i for i in result.issues if i.evidence.extra.get("check_id") == "llm:keyword_coverage")
    assert keyword_issue.evidence.extra["missing_topics"] == ["pricing", "return policy"]
    assert "pricing" in keyword_issue.title


async def test_api_error_degrades_gracefully_never_fabricates():
    scan = make_scan_results()
    with patch("config.settings.openai_api_key", "sk-test"), \
         patch("services.llm_seo_agent._call_openai", new_callable=AsyncMock, side_effect=LlmSeoAgentError("rate_limited: too many requests")):
        result = await analyze_seo_with_llm(scan)
    for check_id in ("llm:title_quality", "llm:content_relevance", "llm:keyword_coverage"):
        check = _check(result, check_id)
        assert check.status == CheckStatus.UNAVAILABLE
        assert "rate_limited" in check.detail
    assert len(result.issues) == 0  # a failed API call must never be presented as a found issue


async def test_missing_extracted_data_degrades_gracefully():
    scan = make_scan_results(extracted=None)
    with patch("config.settings.openai_api_key", "sk-test"):
        result = await analyze_seo_with_llm(scan)
    assert _check(result, "llm:title_quality").status == CheckStatus.UNAVAILABLE


def test_user_prompt_includes_real_evidence_not_fabricated():
    from services.llm_seo_agent import _build_user_prompt

    scan = make_scan_results(title="Specific Real Title", word_count=50)
    prompt = _build_user_prompt(scan)
    assert "Specific Real Title" in prompt
    assert scan.extracted.content.content_excerpt in prompt


async def test_evaluation_engine_merges_llm_checks_into_seo_category():
    from services import evaluation_engine

    scan = make_scan_results()
    with patch("config.settings.openai_api_key", "sk-test"), \
         patch("services.llm_seo_agent._call_openai", new_callable=AsyncMock, return_value={
             "title_quality": {"verdict": "good", "explanation": "fine"},
             "content_relevance": {"verdict": "good", "explanation": "fine"},
             "keyword_coverage": {"verdict": "good", "explanation": "fine", "missing_topics": []},
         }):
        evaluation = await evaluation_engine.run_evaluation("eval-x", scan, "2026-01-01T00:00:00+00:00")
    seo = evaluation.categories["seo"]
    assert any(c.check_id == "llm:title_quality" for c in seo.checks)
    # rule-based SEO checks must still be present too — the agent is additive, not a replacement
    assert any(c.check_id == "title_present" for c in seo.checks)
