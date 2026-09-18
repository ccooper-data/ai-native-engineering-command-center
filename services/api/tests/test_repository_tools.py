import pytest

from app.contracts import EngineeringArtifact, ProposedFileChange
from app.repository_tools import (
    DryRunRepositoryExecutor,
    GovernedRepositoryExecutor,
    RepositoryPolicyError,
)


def artifact(
    path: str = "src/capability/service.py", branch: str = "agent/test-change"
) -> EngineeringArtifact:
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


class RecordingMutationClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def create_branch(self, branch_name: str) -> None:
        self.calls.append(("branch", branch_name))

    def create_file(self, branch_name: str, change: ProposedFileChange, message: str) -> None:
        self.calls.append(("create", f"{branch_name}:{change.path}:{message}"))

    def update_file(self, branch_name: str, change: ProposedFileChange, message: str) -> None:
        self.calls.append(("update", f"{branch_name}:{change.path}:{message}"))

    def delete_file(self, branch_name: str, change: ProposedFileChange, message: str) -> None:
        self.calls.append(("delete", f"{branch_name}:{change.path}:{message}"))


def test_dry_run_accepts_bounded_agent_change() -> None:
    result = DryRunRepositoryExecutor().apply(artifact())
    assert result.dry_run is True
    assert result.branch_name == "agent/test-change"
    assert result.applied_paths == ["src/capability/service.py"]


def test_governed_executor_delegates_only_after_policy_validation() -> None:
    client = RecordingMutationClient()
    result = GovernedRepositoryExecutor(client).apply(artifact())
    assert result.dry_run is False
    assert result.applied_paths == ["src/capability/service.py"]
    assert client.calls[0] == ("branch", "agent/test-change")
    assert client.calls[1][0] == "create"


@pytest.mark.parametrize(
    ("path", "branch"),
    [
        ("../escape.py", "agent/test"),
        (".github/workflows/ci.yml", "agent/test"),
        ("src/ok.py", "main"),
        ("src/ok.py", "agent/main"),
    ],
)
def test_repository_policy_blocks_unsafe_authority(path: str, branch: str) -> None:
    client = RecordingMutationClient()
    with pytest.raises(RepositoryPolicyError):
        GovernedRepositoryExecutor(client).apply(artifact(path=path, branch=branch))
    assert client.calls == []
