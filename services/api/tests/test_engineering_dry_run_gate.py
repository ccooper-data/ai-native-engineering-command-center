import pytest

from app.contracts import EngineeringArtifact, ProposedFileChange
from app.repository_tools import DryRunRepositoryExecutor, RepositoryPolicyError


def artifact(path: str) -> EngineeringArtifact:
    return EngineeringArtifact(
        branch_name="agent/generated-change",
        commit_message="feat: generated bounded change",
        summary="proposal",
        files=[
            ProposedFileChange(
                path=path,
                operation="create",
                purpose="test",
                content="value = 1\n",
            )
        ],
        acceptance_criteria_addressed=["AC-001"],
        tests_required=["unit"],
        security_notes=["no secrets"],
    )


def test_dry_run_accepts_normal_agent_change_without_mutation() -> None:
    result = DryRunRepositoryExecutor().apply(artifact("src/feature.py"))
    assert result.dry_run is True
    assert result.applied_paths == ["src/feature.py"]


@pytest.mark.parametrize(
    "path",
    [".github/workflows/ci.yml", ".github/dependabot.yml", "../escape.py"],
)
def test_dry_run_rejects_protected_or_unsafe_generated_paths(path: str) -> None:
    with pytest.raises(RepositoryPolicyError):
        DryRunRepositoryExecutor().apply(artifact(path))
