from app.contracts import (
    ActorIdentity,
    ApprovalArtifact,
    CIValidationArtifact,
    ModelUsageArtifact,
    ReviewArtifact,
    TraceabilityItem,
    WorkflowRun,
)
from app.evaluation import evaluate_fault_scenario

SHA = "a" * 40


def base_run() -> WorkflowRun:
    run = WorkflowRun(original_request="Evaluate governance controls with deterministic fault injection.")
    run.ci_validation = CIValidationArtifact(run_id=207, commit_sha=SHA, passed=True, jobs=[])
    run.approval = ApprovalArtifact(approved=True, approver=ActorIdentity(identity_id="human-reviewer", actor_type="human", authentication_source="github-oidc", role="workflow-approver"), rationale="validated", commit_sha=SHA)
    run.review = ReviewArtifact(passed=True, summary="ok", traceability=[], findings=[], recommendation="request_human_approval")
    return run


def test_stale_approval_fault_is_detected_and_blocked() -> None:
    result = evaluate_fault_scenario(base_run(), "stale_approval_sha")
    assert result.detected is True
    assert result.blocked is True


def test_failed_ci_fault_is_detected_and_blocked() -> None:
    run = base_run()
    run.ci_validation.passed = False
    result = evaluate_fault_scenario(run, "failed_ci")
    assert result.detected is True
    assert result.blocked is True


def test_missing_acceptance_criteria_evidence_is_detected_and_blocked() -> None:
    run = base_run()
    run.review.traceability = [TraceabilityItem(acceptance_criterion_id="AC-009", implementation_evidence=[], verification_evidence=[], covered=False)]
    result = evaluate_fault_scenario(run, "missing_ac_evidence")
    assert result.detected is True
    assert result.blocked is True
    assert result.evidence == ["AC-009"]


def test_excessive_cost_fault_is_detected_and_blocked() -> None:
    run = base_run()
    run.planning_usage = ModelUsageArtifact(provider="openai", model="test", estimated_actual_cost_usd=0.26)
    result = evaluate_fault_scenario(run, "excessive_cost")
    assert result.detected is True
    assert result.blocked is True


def test_unknown_fault_scenario_fails_closed() -> None:
    try:
        evaluate_fault_scenario(base_run(), "unknown")
        raise AssertionError("Expected unknown fault scenario to be rejected")
    except ValueError as exc:
        assert "Unknown fault-injection scenario" in str(exc)
