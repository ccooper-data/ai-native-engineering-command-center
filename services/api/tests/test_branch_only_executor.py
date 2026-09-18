from app.contracts import EngineeringArtifact, ProposedFileChange
from app.repository_tools import BranchOnlyRepositoryExecutor


class RecordingClient:
    def __init__(self) -> None:
        self.calls = []

    def create_branch(self, branch_name: str) -> None:
        self.calls.append(("create_branch", branch_name))

    def create_file(self, *args) -> None:
        raise AssertionError("file mutation must not occur")

    def update_file(self, *args) -> None:
        raise AssertionError("file mutation must not occur")

    def delete_file(self, *args) -> None:
        raise AssertionError("file mutation must not occur")


def test_branch_only_stage_cannot_mutate_files() -> None:
    artifact = EngineeringArtifact(
        branch_name="agent/churn-forecast",
        commit_message="feat: propose churn forecast",
        summary="proposal",
        files=[
            ProposedFileChange(
                path="src/churn.py",
                operation="create",
                purpose="feature",
                content="value = 1\n",
            )
        ],
        acceptance_criteria_addressed=["AC-001"],
        tests_required=["unit"],
        security_notes=["authorized access"],
    )
    client = RecordingClient()

    result = BranchOnlyRepositoryExecutor(client).apply(artifact)

    assert client.calls == [("create_branch", "agent/churn-forecast")]
    assert result.applied_paths == []
    assert result.branch_name == "agent/churn-forecast"
