from app.capabilities import evaluate_post_approval_capability
from app.contracts import ApprovalArtifact, CIValidationArtifact, WorkflowRun


SHA = "a" * 40


def approved_run() -> WorkflowRun:
    run = WorkflowRun(original_request="Prove capability separation for governed autonomous engineering.")
    run.ci_validation = CIValidationArtifact(run_id=151, commit_sha=SHA, passed=True, jobs=[])
    run.approval = ApprovalArtifact(
        approved=True,
        approver="Human Reviewer",
        rationale="Reviewed exact validated commit.",
        commit_sha=SHA,
    )
    return run


def test_approved_commit_may_create_draft_pr_capability() -> None:
    decision = evaluate_post_approval_capability(approved_run(), SHA, "draft_pr")
    assert decision.allowed is True


def test_human_approval_does_not_grant_merge_authority() -> None:
    decision = evaluate_post_approval_capability(approved_run(), SHA, "merge")
    assert decision.allowed is False
    assert "not granted" in decision.reason


def test_human_approval_does_not_grant_deployment_authority() -> None:
    decision = evaluate_post_approval_capability(approved_run(), SHA, "deploy")
    assert decision.allowed is False
    assert "not granted" in decision.reason


def test_stale_sha_blocks_every_post_approval_capability() -> None:
    for capability in ("draft_pr", "merge", "deploy"):
        decision = evaluate_post_approval_capability(approved_run(), "b" * 40, capability)
        assert decision.allowed is False
        assert "current commit SHA" in decision.reason
