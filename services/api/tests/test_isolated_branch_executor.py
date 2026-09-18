import pytest

from app.contracts import EngineeringArtifact, ProposedFileChange
from app.repository_tools import IsolatedBranchRepositoryExecutor, RepositoryPolicyError


class RecordingClient:
    def __init__(self) -> None:
        self.calls = []

    def create_branch(self, branch_name: str) -> None:
        raise AssertionError("branch creation is a separate authority stage")

    def create_file(self, branch_name, change, message) -> None:
        self.calls.append(("create", branch_name, change.path))

    def update_file(self, branch_name, change, message) -> None:
        self.calls.append(("update", branch_name, change.path))

    def delete_file(self, branch_name, change, message) -> None:
        self.calls.append(("delete", branch_name, change.path))


def artifact(branch: str, path: str = "src/feature.py") -> EngineeringArtifact:
    return EngineeringArtifact(
        branch_name=branch,
        commit_message="feat: bounded change",
        summary="proposal",
        files=[
            ProposedFileChange(
                path=path,
                operation="create",
                purpose="feature",
                content="value = 1\n",
            )
        ],
        acceptance_criteria_addressed=["AC-001"],
        tests_required=["unit"],
        security_notes=["authorized"],
    )


def test_isolated_executor_writes_only_to_exact_authorized_branch() -> None:
    client = RecordingClient()
    executor = IsolatedBranchRepositoryExecutor(client, "agent/governed-mutation-proof")
    result = executor.apply(artifact("agent/governed-mutation-proof"))
    assert client.calls == [("create", "agent/governed-mutation-proof", "src/feature.py")]
    assert result.branch_name == "agent/governed-mutation-proof"


def test_isolated_executor_rejects_branch_substitution() -> None:
    executor = IsolatedBranchRepositoryExecutor(
        RecordingClient(), "agent/governed-mutation-proof"
    )
    with pytest.raises(RepositoryPolicyError, match="does not match"):
        executor.apply(artifact("agent/other-branch"))


def test_isolated_executor_still_rejects_protected_path() -> None:
    executor = IsolatedBranchRepositoryExecutor(
        RecordingClient(), "agent/governed-mutation-proof"
    )
    with pytest.raises(RepositoryPolicyError, match="Protected repository path"):
        executor.apply(
            artifact("agent/governed-mutation-proof", ".github/workflows/ci.yml")
        )
