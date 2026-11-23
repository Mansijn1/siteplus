from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app
from models.scan_models import ScanStatus
from services.scan_service import ScanRecord, _scans
from tests.conftest import make_scan_results

client = TestClient(app)


@pytest.fixture
def seeded_scan():
    scan_id = "api-test-scan"
    record = ScanRecord(scan_id=scan_id, submitted_url="https://example.test/")
    record.status = ScanStatus.COMPLETED
    record.results = make_scan_results(url="https://example.test/")
    _scans[scan_id] = record
    yield scan_id
    _scans.pop(scan_id, None)


def test_evaluate_unknown_scan_returns_404():
    resp = client.post("/api/evaluate", json={"scan_id": "does-not-exist"})
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "scan_not_found"


def test_evaluate_scan_not_completed_returns_409():
    scan_id = "running-scan"
    record = ScanRecord(scan_id=scan_id, submitted_url="https://example.test/")
    record.status = ScanStatus.RUNNING
    _scans[scan_id] = record
    try:
        resp = client.post("/api/evaluate", json={"scan_id": scan_id})
        assert resp.status_code == 409
        assert resp.json()["detail"]["code"] == "scan_not_completed"
    finally:
        _scans.pop(scan_id, None)


def test_evaluate_happy_path_and_full_endpoint_set(seeded_scan):
    resp = client.post("/api/evaluate", json={"scan_id": seeded_scan})
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "completed"
    assert body["overall_score"] is not None
    assert len(body["categories"]) == 12
    evaluation_id = body["evaluation_id"]

    resp = client.get(f"/api/evaluation/{evaluation_id}")
    assert resp.status_code == 200
    assert resp.json()["evaluation_id"] == evaluation_id

    resp = client.get(f"/api/evaluation/{evaluation_id}/issues")
    assert resp.status_code == 200
    issues_body = resp.json()
    assert issues_body["total"] == len(issues_body["issues"])

    resp = client.get(f"/api/evaluation/{evaluation_id}/issues", params={"severity": "critical"})
    assert resp.status_code == 200
    assert all(i["severity"] == "critical" for i in resp.json()["issues"])

    resp = client.get(f"/api/evaluation/{evaluation_id}/recommendations")
    assert resp.status_code == 200
    recs_body = resp.json()
    assert recs_body["total"] == len(recs_body["recommendations"])
    # Every recommendation must trace back to a real issue_id from the evaluation's own issues.
    all_issue_ids = {i["issue_id"] for i in issues_body["issues"]}
    assert all(r["issue_id"] in all_issue_ids for r in recs_body["recommendations"])

    resp = client.get(f"/api/evaluation/{evaluation_id}/categories")
    assert resp.status_code == 200
    categories_body = resp.json()
    assert len(categories_body["categories"]) == 12
    assert categories_body["overall_score"] == body["overall_score"]


def test_unknown_evaluation_id_returns_404():
    for path in ["", "/issues", "/recommendations", "/categories"]:
        resp = client.get(f"/api/evaluation/does-not-exist{path}")
        assert resp.status_code == 404


def test_health_check_still_works():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_evaluation_service_runs_the_real_async_engine():
    from services import evaluation_service

    scan_id = "async-direct-scan"
    record = ScanRecord(scan_id=scan_id, submitted_url="https://example.test/")
    record.status = ScanStatus.COMPLETED
    record.results = make_scan_results(url="https://example.test/", title=None)  # force at least one real failure
    _scans[scan_id] = record
    try:
        result = await evaluation_service.start_evaluation(scan_id)
        assert result.status.value == "completed"
        assert result.overall_score is not None
        assert any(issue.category == "seo" for cat in result.categories.values() for issue in cat.issues)
    finally:
        _scans.pop(scan_id, None)


def test_benchmark_latest_endpoint_returns_real_results_when_present():
    resp = client.get("/api/benchmark/latest")
    # Either the benchmark has been run in this environment (200, real data) or it hasn't (404)
    # — both are valid states; what must never happen is fabricated data on a 200.
    assert resp.status_code in (200, 404)
    if resp.status_code == 200:
        body = resp.json()
        assert "overall" in body
        assert "precision" in body["overall"]
