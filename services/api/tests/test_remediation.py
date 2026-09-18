import pytest

from app.remediation import FailureEvidence, build_remediation_request

SHA = "a" * 40


def failure(sha: str = SHA, exit_code: int = 1) -> FailureEvidence:
    return FailureEvidence(
        source="ruff",
        command="ruff check .",
        exit_code=exit_code,
        commit_sha=sha,
        diagnostic="I001 import block is un-sorted or un-formatted",
        affected_paths=["services/api/tests/test_capabilities.py"],
    )


def test_remediation_is_bounded_to_failure_evidence_paths() -> None:
    request = build_remediation_request(SHA, [failure()])
    assert request.allowed_paths == ["services/api/tests/test_capabilities.py"]
    assert "I001" in request.instruction
    assert "Do not broaden scope" in request.instruction


def test_remediation_rejects_evidence_from_different_sha() -> None:
    with pytest.raises(ValueError, match="failed commit SHA"):
        build_remediation_request(SHA, [failure("b" * 40)])


def test_remediation_rejects_successful_check_as_failure_evidence() -> None:
    with pytest.raises(ValueError, match="Successful checks"):
        build_remediation_request(SHA, [failure(exit_code=0)])


def test_remediation_requires_concrete_affected_path() -> None:
    item = failure()
    item.affected_paths = []
    with pytest.raises(ValueError, match="affected path"):
        build_remediation_request(SHA, [item])
