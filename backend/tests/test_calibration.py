from __future__ import annotations

from services.calibration import analyze_calibration


def _report(**overrides) -> dict:
    base = {
        "by_category": {"seo": {"tp": 10, "fp": 0, "fn": 0, "tn": 10}},
        "confidence_calibration": {"avg_confidence_of_true_positives": 0.95, "avg_confidence_of_false_positives": None},
        "evaluation_coverage": {"coverage_percent": 100.0},
    }
    base.update(overrides)
    return base


def test_healthy_report_has_no_flags():
    result = analyze_calibration(_report())
    assert result["healthy"] is True
    assert result["flags"] == []


def test_high_false_positive_rate_is_flagged():
    report = _report(by_category={"ui": {"tp": 2, "fp": 8, "fn": 0, "tn": 5}})
    result = analyze_calibration(report)
    assert result["healthy"] is False
    assert any("false-positive rate" in f and "ui" in f for f in result["flags"])


def test_high_false_negative_rate_is_flagged():
    report = _report(by_category={"mobile": {"tp": 2, "fp": 0, "fn": 8, "tn": 5}})
    result = analyze_calibration(report)
    assert any("false-negative rate" in f and "mobile" in f for f in result["flags"])


def test_inverted_confidence_bands_are_flagged():
    report = _report(confidence_calibration={"avg_confidence_of_true_positives": 0.6, "avg_confidence_of_false_positives": 0.9})
    result = analyze_calibration(report)
    assert any("inverted" in f for f in result["flags"])


def test_low_coverage_is_flagged():
    report = _report(evaluation_coverage={"coverage_percent": 50.0})
    result = analyze_calibration(report)
    assert any("coverage" in f.lower() for f in result["flags"])


def test_current_benchmark_result_is_healthy():
    import json
    from pathlib import Path

    results_path = Path(__file__).resolve().parent.parent / "benchmark" / "results" / "latest.json"
    if not results_path.exists():
        import pytest

        pytest.skip("benchmark/results/latest.json not present — run `python -m benchmark.runner` first")
    report = json.loads(results_path.read_text(encoding="utf-8"))
    result = analyze_calibration(report)
    assert result["healthy"], f"Calibration flags found: {result['flags']}"
