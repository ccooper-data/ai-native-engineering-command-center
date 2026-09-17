import pytest

from app.contracts import EngineeringArtifact, ProposedFileChange
from app.repository_tools import DryRunRepositoryExecutor, RepositoryPolicyError


def artifact(path: str = "src/capability/service.py", branch: str = "agent/test-change") -> EngineeringArtifact:
    return EngineeringArtifact(
        branch_name=branch,
        commit_message="feat: bounded change",
        summary="Test change set",
        files=[
            ProposedFileChange(
                path=path,
                operation="create",
                purpose="Exercise bounded repository policy",
                content="VALUE = 1\n",
            )
        ],
        acceptance_criteria_addressed=["AC-001"],
        tests_required=["unit"],
        security_notes=[],
    )


def test_dry_run_accepts_bounded_agent_change() -> None:
    result = DryRunRepositoryExecutor().apply(artifact())
    assert result.dry_run is True
    assert result.branch_name == "agent/test-change"
    assert result.applied_paths == ["src/capability/service.py"]


@pytest.mark.parametrize(
    ("path", "branch"),
    [
        ("../escape.py", "agent/test"),
        (".github/workflows/ci.yml", "agent/test"),
        ("src/ok.py", "main"),
    ],
)
def test_repository_policy_blocks_unsafe_authority(path: str, branch: str) -> None:
    with pytest.raises(RepositoryPolicyError):
        DryRunRepositoryExecutor().apply(artifact(path=path, branch=branch))
