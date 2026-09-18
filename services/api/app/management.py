from .contracts import ManagementRunView, WorkflowRun
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
        created_at=run.created_at,
    )
