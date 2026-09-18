from app.contracts import ApprovalArtifact, ProductRequest
from app.database import SqlRunRepository, create_schema
from app.pull_requests import build_pull_request_draft
from app.repository_tools import RepositoryExecutionResult
from app.service import EngineeringWorkflowService


def approved_run():
    create_schema()
    service = EngineeringWorkflowService(SqlRunRepository())
    run = service.create_and_run(
        ProductRequest(request="Add churn forecasting to the SaaS product and expose results in mobile.")
    )
    run.approval = ApprovalArtifact(
        approved=True,
        approver="Cory Cooper",
        rationale="Reviewed quality, security, and traceability evidence.",
        commit_sha="a" * 40,
    )
    return run


def test_pr_draft_contains_end_to_end_governance_evidence() -> None:
    run = approved_run()
    execution = RepositoryExecutionResult(
        branch_name=run.engineering.branch_name,
        applied_paths=[change.path for change in run.engineering.files],
        commit_message=run.engineering.commit_message,
        dry_run=False,
    )
    draft = build_pull_request_draft(run, execution)
    assert draft.draft is True
    assert draft.base == "main"
    assert "## Acceptance criteria" in draft.body
    assert "## Architecture decisions" in draft.body
    assert "QA passed: **True**" in draft.body
    assert "Security passed: **True**" in draft.body
    assert "Approver: **Cory Cooper**" in draft.body
    assert "AC-001: covered" in draft.body


def test_pr_draft_rejects_unapproved_work() -> None:
    run = approved_run()
    run.approval = None
    execution = RepositoryExecutionResult(
        branch_name=run.engineering.branch_name,
        applied_paths=[change.path for change in run.engineering.files],
        commit_message=run.engineering.commit_message,
        dry_run=False,
    )
    try:
        build_pull_request_draft(run, execution)
        raise AssertionError("Expected unapproved PR publication to be rejected")
    except ValueError as exc:
        assert "human approval" in str(exc)
