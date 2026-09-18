from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi.testclient import TestClient

from app.api_identity import verified_approval_assertion
from app.contracts import CIJobEvidence, CIValidationArtifact
from app.identity import AuthorizationContext, IdentityAssertion, VerificationProvenance
from app.main import app, workflow_service


def approval_assertion(workflow_id: str, commit_sha: str) -> IdentityAssertion:
    now = datetime.now(UTC)
    return IdentityAssertion(
        subject="github:user:approver",
        actor_type="human",
        authentication_source="github-oidc",
        role="workflow-approver",
        verification=VerificationProvenance(
            issuer="https://token.actions.githubusercontent.com",
            audience="ai-native-engineering-command-center",
            verification_method="test-verified",
            assertion_id=f"api-approval-{workflow_id}-{commit_sha}",
            authorization_context=AuthorizationContext(capability="approve-workflow", workflow_id=workflow_id, commit_sha=commit_sha),
            issued_at=now - timedelta(minutes=1),
            expires_at=now + timedelta(minutes=5),
        ),
    )


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

        app.dependency_overrides[verified_approval_assertion] = lambda: approval_assertion(run["id"], "0" * 40)
        blocked = client.post(
            f'/api/v1/runs/{run["id"]}/approval?commit_sha={"0" * 40}',
            json={
                "approved": True,
                "rationale": "Quality and traceability evidence reviewed.",
            },
        )
        assert blocked.status_code == 409

        validation = CIValidationArtifact(
            run_id=123,
            commit_sha="a" * 40,
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
            expected_commit_sha="a" * 40,
        )
        assert persisted is not None
        assert persisted.ci_validation is not None
        assert persisted.ci_validation.passed is True

        app.dependency_overrides[verified_approval_assertion] = lambda: approval_assertion(run["id"], "b" * 40)
        stale = client.post(
            f'/api/v1/runs/{run["id"]}/approval?commit_sha={"b" * 40}',
            json={
                "approved": True,
                "rationale": "Attempt approval against stale commit.",
            },
        )
        assert stale.status_code == 409

        app.dependency_overrides[verified_approval_assertion] = lambda: approval_assertion(run["id"], "a" * 40)
        approval = client.post(
            f'/api/v1/runs/{run["id"]}/approval?commit_sha={"a" * 40}',
            json={
                "approved": True,
                "rationale": "Quality, traceability, and executable CI evidence reviewed.",
            },
        )
        assert approval.status_code == 200
        approved = approval.json()
        assert approved["status"] == "approved"
        assert approved["approval"]["approved"] is True
        assert approved["approval"]["approver"]["identity_id"] == "github:user:approver"
        assert approved["approval"]["commit_sha"] == "a" * 40
        assert approved["audit_events"][-1]["agent"] == "human"
        app.dependency_overrides.clear()


def test_short_request_is_rejected() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/runs", json={"request": "too short"})
    assert response.status_code == 422
