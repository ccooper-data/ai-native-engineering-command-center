from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_product_request_creates_traceable_plan() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/runs",
            json={
                "request": "Add customer churn forecasting to our SaaS product and expose the results through the mobile app."
            },
        )

        assert response.status_code == 201
        run = response.json()
        assert run["status"] == "planned"
        assert run["provider"] == "mock"
        assert run["planning"]["acceptance_criteria"]
        assert run["planning"]["acceptance_criteria"][0]["id"] == "AC-001"
        assert any(event["agent"] == "planning" for event in run["audit_events"])

        retrieved = client.get(f'/api/v1/runs/{run["id"]}')
        assert retrieved.status_code == 200
        assert retrieved.json()["original_request"] == run["original_request"]


def test_short_request_is_rejected() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/runs", json={"request": "too short"})
    assert response.status_code == 422
