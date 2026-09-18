import pytest

from app.contracts import EngineeringArtifact, ProposedFileChange
from app.repository_tools import RepositoryPolicyError, validate_change_set


def change(index: int, content: str = "x") -> ProposedFileChange:
    return ProposedFileChange(
        path=f"src/generated_{index}.py",
        operation="create",
        purpose="bounded generated change",
        content=content,
    )


def artifact(files: list[ProposedFileChange]) -> EngineeringArtifact:
    return EngineeringArtifact(
        branch_name="agent/governed-mutation-proof",
        commit_message="feat: bounded mutation",
        summary="proposal",
        files=files,
        acceptance_criteria_addressed=["AC-001"],
        tests_required=["unit"],
        security_notes=["no secrets"],
    )


def test_repository_policy_rejects_more_than_six_generated_files() -> None:
    with pytest.raises(RepositoryPolicyError, match="six-file limit"):
        validate_change_set(artifact([change(i) for i in range(7)]))


def test_repository_policy_rejects_generated_file_over_100kb() -> None:
    with pytest.raises(RepositoryPolicyError, match="100 KB limit"):
        validate_change_set(artifact([change(1, "x" * 100_001)]))


def test_repository_policy_accepts_six_small_generated_files() -> None:
    validate_change_set(artifact([change(i) for i in range(6)]))
