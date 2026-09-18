from .contracts import ManagementRunView, ManagementSummary, RunStatus, WorkflowRun
from .governance import build_governance_evidence


def build_management_view(run: WorkflowRun) -> ManagementRunView:
    if run.approval is None:
        approval_state = "pending"
    else:
        approval_state = "approved" if run.approval.approved else "rejected"
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
        created_at=run.created_at,
    )


def build_management_summary(runs: list[WorkflowRun]) -> ManagementSummary:
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
    )
