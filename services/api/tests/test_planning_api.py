from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_product_request_creates_persisted_three_agent_change_set() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/runs",
            json={
                "request": "Add customer churn forecasting to our SaaS product and expose the results through the mobile app."
            },
        )

        assert response.status_code == 201
        run = response.json()
        assert run["status"] == "implemented"
        assert run["provider"] == "mock"
        assert run["planning"]["acceptance_criteria"][0]["id"] == "AC-001"
        assert run["architecture"]["decisions"][0]["id"] == "ADR-AGENT-001"
        assert run["engineering"]["branch_name"] == "agent/churn-capability"
        assert len(run["engineering"]["files"]) == 2
        assert [event["agent"] for event in run["audit_events"]] == [
            "system",
            "planning",
            "architecture",
            "engineering",
        ]

        retrieved = client.get(f'/api/v1/runs/{run["id"]}')
        assert retrieved.status_code == 200
        assert retrieved.json()["engineering"] == run["engineering"]


def test_short_request_is_rejected() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/runs", json={"request": "too short"})
    assert response.status_code == 422
