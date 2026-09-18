from app.contracts import EngineeringArtifact, ProposedFileChange
from app.repository_tools import DryRunRepositoryExecutor


def test_engineering_artifact_can_only_reach_zero_mutation_executor_in_dry_run() -> None:
    artifact = EngineeringArtifact(
        branch_name="agent/churn-forecast",
        commit_message="feat: add churn forecast",
        summary="bounded proposal",
        files=[
            ProposedFileChange(
                path="src/churn.py",
                operation="create",
                purpose="forecast service",
                content="def forecast():\n    return 0.5\n",
            ),
            ProposedFileChange(
                path="tests/test_churn.py",
                operation="create",
                purpose="forecast test",
                content="def test_forecast():\n    assert True\n",
            ),
        ],
        acceptance_criteria_addressed=["AC-001"],
        tests_required=["unit"],
        security_notes=["tenant authorization required"],
    )

    result = DryRunRepositoryExecutor().apply(artifact)

    assert result.dry_run is True
    assert result.branch_name == "agent/churn-forecast"
    assert result.applied_paths == ["src/churn.py", "tests/test_churn.py"]
