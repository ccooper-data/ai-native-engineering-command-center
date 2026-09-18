from .contracts import (
    ChainOfCustody,
    GovernanceException,
    ManagementRunView,
    ManagementSummary,
    RunStatus,
    WorkflowRun,
)
from .governance import build_governance_evidence


def build_management_view(run: WorkflowRun) -> ManagementRunView:
    if run.approval is None:
        approval_state = "pending"
    else:
        approval_state = "approved" if run.approval.approved else "rejected"
    mutation_sha = run.verified_mutation_commit_sha
    ci_sha = run.ci_validation.commit_sha if run.ci_validation is not None else None
    approval_sha = run.approval.commit_sha if run.approval is not None else None
    present = [sha for sha in (mutation_sha, ci_sha, approval_sha) if sha is not None]
    aligned = len(set(present)) <= 1
    if not present:
        custody_state = "pending_mutation"
    elif not aligned:
        custody_state = "identity_mismatch"
    elif approval_sha is None:
        custody_state = "awaiting_approval"
    else:
        custody_state = "aligned"
    return ManagementRunView(
        id=run.id,
        status=run.status,
        original_request=run.original_request,
        provider=run.provider,
        model=run.model,
        governance_evidence=build_governance_evidence(run),
        ci_passed=run.ci_validation.passed if run.ci_validation is not None else None,
        review_passed=run.review.passed if run.review is not None else None,
        approval_state=approval_state,
        audit_events=sorted(run.audit_events, key=lambda event: event.timestamp),
        traceability=run.review.traceability if run.review is not None else [],
        chain_of_custody=ChainOfCustody(
            mutation_sha=mutation_sha,
            ci_sha=ci_sha,
            approval_sha=approval_sha,
            aligned=aligned,
            state=custody_state,
        ),
        created_at=run.created_at,
    )


def build_management_summary(runs: list[WorkflowRun]) -> ManagementSummary:
    exceptions: list[GovernanceException] = []
    for run in runs:
        if run.status == RunStatus.REMEDIATION_REQUIRED:
            exceptions.append(GovernanceException(code="REMEDIATION_REQUIRED", severity="high", message="Workflow requires remediation.", workflow_id=run.id))
        if run.ci_validation is not None and not run.ci_validation.passed:
            exceptions.append(GovernanceException(code="CI_FAILED", severity="high", message="Executable CI evidence failed.", workflow_id=run.id, evidence=[str(run.ci_validation.run_id), run.ci_validation.commit_sha]))
        if run.review is not None and not run.review.passed:
            exceptions.append(GovernanceException(code="REVIEW_BLOCKED", severity="high", message="Independent reviewer blocked progression.", workflow_id=run.id))
        if run.approval is not None and run.ci_validation is not None and run.approval.commit_sha != run.ci_validation.commit_sha:
            exceptions.append(GovernanceException(code="STALE_APPROVAL", severity="critical", message="Human approval does not match validated commit SHA.", workflow_id=run.id))
        uncovered = [item.acceptance_criterion_id for item in run.review.traceability if not item.covered] if run.review is not None else []
        if uncovered:
            exceptions.append(GovernanceException(code="TRACEABILITY_GAP", severity="high", message="Acceptance criteria lack complete evidence.", workflow_id=run.id, evidence=uncovered))
        usage = build_governance_evidence(run)
        if usage.estimated_actual_cost_usd > 0.20:
            exceptions.append(GovernanceException(code="HIGH_MODEL_COST", severity="warning", message="Estimated model cost exceeds $0.20 for this workflow.", workflow_id=run.id, evidence=[f"{usage.estimated_actual_cost_usd:.4f}"]))
    evidence = [build_governance_evidence(run) for run in runs]
    terminal = {RunStatus.APPROVED, RunStatus.REJECTED, RunStatus.FAILED}
    return ManagementSummary(
        total_workflows=len(runs),
        active_workflows=sum(run.status not in terminal for run in runs),
        blocked_workflows=sum(run.status == RunStatus.REMEDIATION_REQUIRED for run in runs),
        pending_approvals=sum(run.status == RunStatus.AWAITING_APPROVAL for run in runs),
        ci_failures=sum(run.ci_validation is not None and not run.ci_validation.passed for run in runs),
        review_failures=sum(run.review is not None and not run.review.passed for run in runs),
        total_tokens=sum(item.total_tokens for item in evidence),
        estimated_actual_cost_usd=sum(item.estimated_actual_cost_usd for item in evidence),
        exceptions=exceptions,
    )
