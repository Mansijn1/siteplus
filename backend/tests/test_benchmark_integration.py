"""Runs the actual benchmark (real Playwright scans against the local fixture server) and
asserts it stays healthy — this IS "regression testing for benchmark calculations": if a future
analyzer change regresses precision/recall on the known fixtures, this test catches it. Slower
than the rest of the suite (real browser automation across 6 pages), so it's kept in its own
file rather than mixed into the fast unit tests."""

from __future__ import annotations

from benchmark.runner import run_benchmark
from services.calibration import analyze_calibration


async def test_benchmark_stays_healthy():
    # One combined test, not two — run_benchmark() starts the fixture server on a fixed port,
    # and a second call in the same process would fail to rebind it.
    report = await run_benchmark()
    overall = report["overall"]
    assert overall["precision"] == 1.0, f"Precision regressed: {report['fixtures']}"
    assert overall["recall"] == 1.0, f"Recall regressed: {report['fixtures']}"

    calibration = analyze_calibration(report)
    assert calibration["healthy"], calibration["flags"]
