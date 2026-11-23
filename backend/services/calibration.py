"""Reads a benchmark report (benchmark/results/latest.json) and flags signs of miscalibration —
the data-driven half of Stage F's scoring calibration that Phase 3/4's scoring code deliberately
didn't attempt blind: the spec is explicit that scoring weights and confidence bands must not
change without benchmark evidence to justify the change, so this module is where that evidence
gets turned into an actionable (but still human-reviewed) flag list, not an automatic rewrite of
CATEGORY_WEIGHTS or confidence_engine's bands."""

from __future__ import annotations

_FALSE_POSITIVE_RATE_THRESHOLD = 0.2
_FALSE_NEGATIVE_RATE_THRESHOLD = 0.2


def analyze_calibration(report: dict) -> dict:
    flags: list[str] = []

    for category, stats in report.get("by_category", {}).items():
        tp, fp, fn = stats.get("tp", 0), stats.get("fp", 0), stats.get("fn", 0)
        if (tp + fp) > 0 and fp / (tp + fp) > _FALSE_POSITIVE_RATE_THRESHOLD:
            flags.append(
                f"{category}: false-positive rate {fp / (tp + fp):.0%} exceeds "
                f"{_FALSE_POSITIVE_RATE_THRESHOLD:.0%} — rules in this category may be too strict."
            )
        if (tp + fn) > 0 and fn / (tp + fn) > _FALSE_NEGATIVE_RATE_THRESHOLD:
            flags.append(
                f"{category}: false-negative rate {fn / (tp + fn):.0%} exceeds "
                f"{_FALSE_NEGATIVE_RATE_THRESHOLD:.0%} — rules in this category may be missing real issues."
            )

    cc = report.get("confidence_calibration", {})
    tp_conf, fp_conf = cc.get("avg_confidence_of_true_positives"), cc.get("avg_confidence_of_false_positives")
    if tp_conf is not None and fp_conf is not None and fp_conf >= tp_conf:
        flags.append(
            f"Confidence bands look inverted: false positives average {fp_conf} confidence, "
            f"true positives average {tp_conf} — services/confidence_engine.py's source bands "
            "need review, since confident findings should be the reliable ones."
        )

    coverage = report.get("evaluation_coverage", {}).get("coverage_percent")
    if coverage is not None and coverage < 80:
        flags.append(
            f"Evaluation coverage is only {coverage}% — more than a fifth of ground-truth checks "
            "came back unavailable rather than confirmable; investigate why before trusting precision/recall here."
        )

    return {"healthy": len(flags) == 0, "flags": flags}
