from uuid import UUID

from fastapi.testclient import TestClient

from app.contracts import CIJobEvidence, CIValidationArtifact
from app.main import app, workflow_service


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200


def test_workflow_requires_ci_evidence_before_explicit_human_approval() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/runs",
            json={
                "request": "Add customer churn forecasting to our SaaS product and expose the results through the mobile app."
            },
        )
        assert response.status_code == 201
        run = response.json()
        assert run["status"] == "awaiting_approval"
        assert run["review"]["passed"] is True
        assert all(item["covered"] for item in run["review"]["traceability"])
        assert run["approval"] is None

        blocked = client.post(
            f'/api/v1/runs/{run["id"]}/approval',
            json={
                "approved": True,
                "approver": "Cory Cooper",
                "rationale": "Quality and traceability evidence reviewed.",
            },
        )
        assert blocked.status_code == 409

        validation = CIValidationArtifact(
            run_id=123,
            commit_sha="abc123",
            passed=True,
            jobs=[
                CIJobEvidence(name="backend", conclusion="success", passed=True),
                CIJobEvidence(name="frontend", conclusion="success", passed=True),
                CIJobEvidence(name="security", conclusion="success", passed=True),
            ],
        )
        persisted = workflow_service.record_ci_validation(
            run_id=UUID(run["id"]),
            validation=validation,
            expected_commit_sha="abc123",
        )
        assert persisted is not None
        assert persisted.ci_validation is not None
        assert persisted.ci_validation.passed is True

        approval = client.post(
            f'/api/v1/runs/{run["id"]}/approval',
            json={
                "approved": True,
                "approver": "Cory Cooper",
                "rationale": "Quality, traceability, and executable CI evidence reviewed.",
            },
        )
        assert approval.status_code == 200
        approved = approval.json()
        assert approved["status"] == "approved"
        assert approved["approval"]["approved"] is True
        assert approved["approval"]["approver"] == "Cory Cooper"
        assert approved["audit_events"][-1]["agent"] == "human"


def test_short_request_is_rejected() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/runs", json={"request": "too short"})
    assert response.status_code == 422
