from app.contracts import (
    ApprovalArtifact,
    CIValidationArtifact,
    ReviewArtifact,
    WorkflowRun,
)
from app.management import build_management_view

SHA = "a" * 40


def ready_run() -> WorkflowRun:
    run = WorkflowRun(original_request="Prove benchmark regression blocks governance readiness.")
    run.verified_mutation_commit_sha = SHA
    run.ci_validation = CIValidationArtifact(run_id=222, commit_sha=SHA, passed=True, jobs=[])
    run.review = ReviewArtifact(
        passed=True,
        summary="approved by independent review",
        traceability=[],
        findings=[],
        recommendation="request_human_approval",
    )
    run.approval = ApprovalArtifact(
        approved=True,
        approver="Human Reviewer",
        rationale="Reviewed exact validated commit.",
        commit_sha=SHA,
    )
    return run


def test_ready_workflow_remains_ready_without_control_regression() -> None:
    view = build_management_view(ready_run(), control_regression=False)
    assert view.readiness.state == "READY_FOR_DRAFT_PR"


def test_control_regression_blocks_otherwise_ready_workflow() -> None:
    view = build_management_view(ready_run(), control_regression=True)
    assert view.readiness.state == "BLOCKED"
    assert any("benchmark regressed" in reason for reason in view.readiness.reasons)
