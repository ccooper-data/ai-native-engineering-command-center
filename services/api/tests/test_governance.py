from app.contracts import (
    AuditEvent,
    CIValidationArtifact,
    EngineeringArtifact,
    ModelUsageArtifact,
    WorkflowRun,
)
from app.governance import build_governance_evidence

SHA = "a" * 40


def test_governance_evidence_summarizes_cost_ci_branch_and_remediation() -> None:
    run = WorkflowRun(original_request="Persist governance evidence for executive observability.")
    run.engineering = EngineeringArtifact(
        branch_name="agent/governed-mutation-proof",
        commit_message="feat: evidence",
        summary="evidence",
        files=[],
        acceptance_criteria_addressed=[],
        tests_required=[],
        security_notes=[],
    )
    run.planning_usage = ModelUsageArtifact(provider="openai", model="test", total_tokens=100, estimated_actual_cost_usd=0.01)
    run.architecture_usage = ModelUsageArtifact(provider="openai", model="test", total_tokens=200, estimated_actual_cost_usd=0.02)
    run.ci_validation = CIValidationArtifact(run_id=158, commit_sha=SHA, passed=True, jobs=[])
    run.audit_events.append(AuditEvent(agent="ci", action="validation", status="failed", commit_sha=SHA))

    evidence = build_governance_evidence(run)

    assert evidence.current_commit_sha == SHA
    assert evidence.repository_branch == "agent/governed-mutation-proof"
    assert evidence.ci_run_ids == [158]
    assert evidence.remediation_cycles == 1
    assert evidence.total_tokens == 300
    assert evidence.estimated_actual_cost_usd == 0.03
