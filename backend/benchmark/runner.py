"""Runs the real scan + evaluation pipeline against every benchmark fixture and compares actual
check results to hand-verified ground truth (benchmark/ground_truth.py), computing precision,
recall, F1, false-positive/negative rates, confidence calibration, and coverage — overall and
per category. This is the ONLY place in the codebase that bypasses `validate_public_url` (via
calling `run_browser_scan` directly) — appropriate here because the target is this benchmark's
own local fixture server, not a public API route a user could point anywhere.

Usage: `python -m benchmark.runner` from the `backend/` directory (venv activated), with no
other scan in flight. Writes benchmark/results/latest.json and prints a summary."""

from __future__ import annotations

import asyncio
import json
import sys
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import httpx
import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from benchmark.ground_truth import GROUND_TRUTH  # noqa: E402
from models.evaluation_models import CheckStatus  # noqa: E402
from models.scan_models import ScanResults  # noqa: E402
from scanner.browser import run_browser_scan  # noqa: E402
from services import evaluation_engine  # noqa: E402
from services.scan_service import _build_extracted_data  # noqa: E402

PORT = 8991
BASE_URL = f"http://127.0.0.1:{PORT}"
RESULTS_PATH = Path(__file__).resolve().parent / "results" / "latest.json"


@dataclass
class Confusion:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0
    tp_confidences: list[float] = field(default_factory=list)
    fp_confidences: list[float] = field(default_factory=list)

    def precision(self) -> float | None:
        denom = self.tp + self.fp
        return round(self.tp / denom, 3) if denom > 0 else None

    def recall(self) -> float | None:
        denom = self.tp + self.fn
        return round(self.tp / denom, 3) if denom > 0 else None

    def f1(self) -> float | None:
        p, r = self.precision(), self.recall()
        if p is None or r is None or (p + r) == 0:
            return None
        return round(2 * p * r / (p + r), 3)

    def false_positive_rate(self) -> float | None:
        denom = self.fp + self.tn
        return round(self.fp / denom, 3) if denom > 0 else None

    def false_negative_rate(self) -> float | None:
        denom = self.fn + self.tp
        return round(self.fn / denom, 3) if denom > 0 else None


def _start_server() -> threading.Thread:
    config = uvicorn.Config("benchmark.server:app", host="127.0.0.1", port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    return thread


async def _wait_for_server() -> None:
    async with httpx.AsyncClient() as client:
        for _ in range(50):
            try:
                resp = await client.get(f"{BASE_URL}/clean.html", timeout=1.0)
                if resp.status_code == 200:
                    return
            except httpx.HTTPError:
                pass
            await asyncio.sleep(0.2)
    raise RuntimeError("Benchmark fixture server did not start in time.")


async def _scan_fixture(fixture_name: str) -> ScanResults:
    url = f"{BASE_URL}/{fixture_name}"
    scan_id = f"bench-{fixture_name.replace('.html', '')}"
    nav, screenshots, audit_extras = await run_browser_scan(scan_id, url, allow_loopback_for_benchmark=True)
    extracted = _build_extracted_data(nav, url)
    now = datetime.now(timezone.utc).isoformat()
    return ScanResults(
        scan_id=scan_id, submitted_url=url, extracted=extracted, screenshots=screenshots,
        lighthouse={}, console_messages=nav.console_messages, response=nav.response_info,
        load_timing=nav.load_timing, audit_extras=audit_extras, started_at=now, completed_at=now,
    )


async def run_benchmark() -> dict:
    _start_server()
    await _wait_for_server()

    overall = Confusion()
    by_category: dict[str, Confusion] = defaultdict(Confusion)
    per_fixture_reports: list[dict] = []
    coverage_checked = 0
    coverage_unavailable = 0

    for fixture_name, expectations in GROUND_TRUTH.items():
        scan = await _scan_fixture(fixture_name)
        evaluation = await evaluation_engine.run_evaluation(f"bench-eval-{fixture_name}", scan, datetime.now(timezone.utc).isoformat())

        actual_status: dict[str, CheckStatus] = {}
        confidence_by_check: dict[str, float] = {}
        for category_id, result in evaluation.categories.items():
            for check in result.checks:
                actual_status[check.check_id] = check.status
            for issue in result.issues:
                check_id = issue.evidence.extra.get("check_id")
                if check_id:
                    confidence_by_check[check_id] = issue.confidence

        fixture_detail = []
        for check_id, expected in expectations.items():
            coverage_checked += 1
            actual = actual_status.get(check_id)
            if actual is None:
                fixture_detail.append({"check_id": check_id, "expected": expected, "actual": "not_run", "verdict": "missing"})
                continue
            if actual == CheckStatus.UNAVAILABLE:
                coverage_unavailable += 1
                fixture_detail.append({"check_id": check_id, "expected": expected, "actual": "unavailable", "verdict": "excluded"})
                continue

            actual_str = actual.value
            category_id = next((c for c, r in evaluation.categories.items() if any(ch.check_id == check_id for ch in r.checks)), "unknown")
            confusion = by_category[category_id]
            confidence = confidence_by_check.get(check_id)

            if expected == "failed" and actual_str == "failed":
                verdict = "TP"
                overall.tp += 1
                confusion.tp += 1
                if confidence is not None:
                    overall.tp_confidences.append(confidence)
                    confusion.tp_confidences.append(confidence)
            elif expected == "passed" and actual_str == "passed":
                verdict = "TN"
                overall.tn += 1
                confusion.tn += 1
            elif expected == "passed" and actual_str == "failed":
                verdict = "FP"
                overall.fp += 1
                confusion.fp += 1
                if confidence is not None:
                    overall.fp_confidences.append(confidence)
                    confusion.fp_confidences.append(confidence)
            else:  # expected == "failed" and actual_str == "passed"
                verdict = "FN"
                overall.fn += 1
                confusion.fn += 1

            fixture_detail.append({"check_id": check_id, "expected": expected, "actual": actual_str, "verdict": verdict})

        per_fixture_reports.append({"fixture": fixture_name, "checks": fixture_detail})

    avg_tp_conf = round(sum(overall.tp_confidences) / len(overall.tp_confidences), 3) if overall.tp_confidences else None
    avg_fp_conf = round(sum(overall.fp_confidences) / len(overall.fp_confidences), 3) if overall.fp_confidences else None

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall": {
            "tp": overall.tp, "fp": overall.fp, "fn": overall.fn, "tn": overall.tn,
            "precision": overall.precision(), "recall": overall.recall(), "f1": overall.f1(),
            "false_positive_rate": overall.false_positive_rate(), "false_negative_rate": overall.false_negative_rate(),
        },
        "confidence_calibration": {
            "avg_confidence_of_true_positives": avg_tp_conf,
            "avg_confidence_of_false_positives": avg_fp_conf,
            "note": (
                "A well-calibrated system should show avg_confidence_of_true_positives clearly "
                "higher than avg_confidence_of_false_positives. If they're close or inverted, "
                "the confidence bands in services/confidence_engine.py need recalibrating."
            ),
        },
        "evaluation_coverage": {
            "ground_truth_checks_defined": coverage_checked,
            "unavailable_at_scan_time": coverage_unavailable,
            "coverage_percent": round((coverage_checked - coverage_unavailable) / coverage_checked * 100, 1) if coverage_checked else None,
        },
        "by_category": {
            cat: {
                "tp": c.tp, "fp": c.fp, "fn": c.fn, "tn": c.tn,
                "precision": c.precision(), "recall": c.recall(), "f1": c.f1(),
            }
            for cat, c in by_category.items()
        },
        "fixtures": per_fixture_reports,
        "scope_note": (
            "Benchmark runs against 6 local, hand-authored fixture pages with known defects — "
            "not the live, diverse (React/Next.js/e-commerce/SaaS/etc.) sites the spec lists, "
            "which would require external targets this project can't keep reproducible or "
            "manually re-verify on demand. HTTPS-dependent checks (https_enabled, "
            "tls_certificate_valid, no_mixed_content) and checks that depend on the test "
            "environment rather than detector logic (robots_txt_present, sitemap_present, "
            "cookie_security_attributes) are excluded from ground truth for the reasons "
            "documented in ground_truth.py's module docstring."
        ),
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _print_summary(report: dict) -> None:
    o = report["overall"]
    print(f"Overall: precision={o['precision']} recall={o['recall']} f1={o['f1']} "
          f"(TP={o['tp']} FP={o['fp']} FN={o['fn']} TN={o['tn']})")
    print(f"False positive rate: {o['false_positive_rate']}  False negative rate: {o['false_negative_rate']}")
    cc = report["confidence_calibration"]
    print(f"Confidence calibration: avg TP confidence={cc['avg_confidence_of_true_positives']} "
          f"avg FP confidence={cc['avg_confidence_of_false_positives']}")
    cov = report["evaluation_coverage"]
    print(f"Coverage: {cov['coverage_percent']}% ({cov['ground_truth_checks_defined'] - cov['unavailable_at_scan_time']} "
          f"of {cov['ground_truth_checks_defined']} ground-truth checks were actually evaluable)")
    print("\nBy category:")
    for cat, stats in sorted(report["by_category"].items()):
        print(f"  {cat:14s} precision={stats['precision']} recall={stats['recall']} f1={stats['f1']} "
              f"(TP={stats['tp']} FP={stats['fp']} FN={stats['fn']} TN={stats['tn']})")
    print("\nMismatches (FP/FN) by fixture:")
    for fixture in report["fixtures"]:
        mismatches = [c for c in fixture["checks"] if c["verdict"] in ("FP", "FN", "missing")]
        if mismatches:
            print(f"  {fixture['fixture']}:")
            for m in mismatches:
                print(f"    {m['verdict']:8s} {m['check_id']:30s} expected={m['expected']:7s} actual={m['actual']}")


if __name__ == "__main__":
    result = asyncio.run(run_benchmark())
    _print_summary(result)
    print(f"\nFull report written to {RESULTS_PATH}")
