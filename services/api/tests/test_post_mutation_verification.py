import pytest

from app.contracts import EngineeringArtifact, ProposedFileChange
from app.repository_tools import IsolatedBranchRepositoryExecutor, RepositoryPolicyError


class VerifyingClient:
    def __init__(self, corrupt: bool = False, rollback_fails: bool = False) -> None:
        self.files: dict[str, str] = {}
        self.corrupt = corrupt
        self.rollback_fails = rollback_fails
        self.starting_sha = "0" * 40
        self.reset_calls: list[str] = []

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

    def get_branch_commit_sha(self, branch_name: str) -> str:
        return self.starting_sha if not self.files else "a" * 40

    def reset_branch_to_commit(self, branch_name: str, commit_sha: str) -> None:
        if not self.rollback_fails:
            self.files.clear()
        self.reset_calls.append(commit_sha)


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
    assert result.commit_sha == "a" * 40


def test_isolated_executor_fails_closed_when_stored_content_differs() -> None:
    client = VerifyingClient(corrupt=True)
    with pytest.raises(RepositoryPolicyError, match="content verification failed"):
        IsolatedBranchRepositoryExecutor(client, "agent/verified-change").apply(artifact())
    assert client.files == {}
    assert client.reset_calls == ["0" * 40]


def test_failed_source_preflight_performs_zero_repository_writes() -> None:
    client = VerifyingClient()
    bad = artifact()
    bad.files[0].path = "src/broken.py"
    bad.files[0].content = "def broken(:\n    pass\n"
    with pytest.raises(RepositoryPolicyError, match="Source preflight failed"):
        IsolatedBranchRepositoryExecutor(client, "agent/verified-change").apply(bad)
    assert client.files == {}


def test_failed_rollback_is_reported_as_critical_uncertain_state() -> None:
    client = VerifyingClient(corrupt=True, rollback_fails=True)
    with pytest.raises(RepositoryPolicyError, match="CRITICAL: rollback verification failed"):
        IsolatedBranchRepositoryExecutor(client, "agent/verified-change").apply(artifact())
    assert client.files != {}
    assert client.reset_calls == ["0" * 40]
