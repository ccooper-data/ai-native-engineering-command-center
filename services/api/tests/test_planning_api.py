from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_product_request_persists_independent_quality_evidence() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/runs",
            json={"request": "Add customer churn forecasting to our SaaS product and expose the results through the mobile app."},
        )
        assert response.status_code == 201
        run = response.json()
        assert run["status"] == "quality_passed"
        assert run["qa"]["passed"] is True
        assert run["security"]["passed"] is True
        assert run["quality_gate"]["passed"] is True
        assert run["quality_gate"]["decision"] == "continue_to_review"
        retrieved = client.get(f'/api/v1/runs/{run["id"]}')
        assert retrieved.status_code == 200
        assert retrieved.json()["quality_gate"] == run["quality_gate"]


def test_short_request_is_rejected() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/runs", json={"request": "too short"})
    assert response.status_code == 422
