from app.ci_evidence import build_ci_validation


def job(name: str, conclusion: str = "success") -> dict:
    return {
        "name": name,
        "conclusion": conclusion,
        "steps": [
            {"name": "checkout", "conclusion": "success"},
            {"name": f"{name}-gate", "conclusion": conclusion},
        ],
    }


def test_ci_evidence_requires_backend_frontend_and_security() -> None:
    artifact = build_ci_validation(
        123,
        "abc123",
        [job("backend"), job("frontend"), job("security")],
    )
    assert artifact.passed is True
    assert artifact.source == "github-actions"
    assert {item.name for item in artifact.jobs} == {"backend", "frontend", "security"}


def test_ci_evidence_blocks_when_security_fails() -> None:
    artifact = build_ci_validation(
        123,
        "abc123",
        [job("backend"), job("frontend"), job("security", "failure")],
    )
    assert artifact.passed is False


def test_ci_evidence_blocks_when_required_job_is_missing() -> None:
    artifact = build_ci_validation(123, "abc123", [job("backend"), job("frontend")])
    assert artifact.passed is False
