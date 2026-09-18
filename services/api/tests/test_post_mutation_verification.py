import pytest

from app.contracts import EngineeringArtifact, ProposedFileChange
from app.repository_tools import IsolatedBranchRepositoryExecutor, RepositoryPolicyError


class VerifyingClient:
    def __init__(self, corrupt: bool = False) -> None:
        self.files: dict[str, str] = {}
        self.corrupt = corrupt

    def create_branch(self, branch_name: str) -> None:
        pass

    def create_file(self, branch_name: str, change: ProposedFileChange, message: str) -> None:
        self.files[change.path] = "CORRUPTED" if self.corrupt else (change.content or "")

    def update_file(self, branch_name: str, change: ProposedFileChange, message: str) -> None:
        self.create_file(branch_name, change, message)

    def delete_file(self, branch_name: str, change: ProposedFileChange, message: str) -> None:
        self.files.pop(change.path, None)

    def read_file(self, branch_name: str, path: str) -> str | None:
        return self.files.get(path)


def artifact() -> EngineeringArtifact:
    return EngineeringArtifact(
        branch_name="agent/verified-change",
        commit_message="feat: verified mutation",
        summary="verify stored repository content",
        files=[ProposedFileChange(path="src/proof.py", operation="create", purpose="proof", content="VALUE = 1\n")],
        acceptance_criteria_addressed=["AC-001"],
        tests_required=["unit"],
        security_notes=[],
    )


def test_isolated_executor_verifies_stored_content_after_write() -> None:
    result = IsolatedBranchRepositoryExecutor(VerifyingClient(), "agent/verified-change").apply(artifact())
    assert result.verification_performed is True
    assert result.verified_paths == ["src/proof.py"]


def test_isolated_executor_fails_closed_when_stored_content_differs() -> None:
    with pytest.raises(RepositoryPolicyError, match="content verification failed"):
        IsolatedBranchRepositoryExecutor(VerifyingClient(corrupt=True), "agent/verified-change").apply(artifact())
