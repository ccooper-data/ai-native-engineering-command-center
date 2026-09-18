from typing import Protocol

from pydantic import BaseModel

from .contracts import WorkflowRun


class CapabilityDecision(BaseModel):
    allowed: bool
    capability: str
    commit_sha: str
    reason: str


class MergeClient(Protocol):
    def merge(self, commit_sha: str) -> str: ...


class DeploymentClient(Protocol):
    def deploy(self, commit_sha: str) -> str: ...


def evaluate_post_approval_capability(
    run: WorkflowRun,
    current_commit_sha: str,
    capability: str,
) -> CapabilityDecision:
    """Fail-closed authorization boundary for capabilities after human approval."""
    if capability not in {"draft_pr", "merge", "deploy"}:
        raise ValueError("Unknown post-approval capability")
    if run.ci_validation is None or not run.ci_validation.passed:
        return CapabilityDecision(allowed=False, capability=capability, commit_sha=current_commit_sha, reason="successful CI evidence required")
    if run.approval is None or not run.approval.approved:
        return CapabilityDecision(allowed=False, capability=capability, commit_sha=current_commit_sha, reason="human approval required")
    if run.approval.commit_sha != current_commit_sha or run.ci_validation.commit_sha != current_commit_sha:
        return CapabilityDecision(allowed=False, capability=capability, commit_sha=current_commit_sha, reason="approval and CI must match current commit SHA")
    if capability == "draft_pr":
        return CapabilityDecision(allowed=True, capability=capability, commit_sha=current_commit_sha, reason="validated and approved commit may produce a draft PR")
    return CapabilityDecision(
        allowed=False,
        capability=capability,
        commit_sha=current_commit_sha,
        reason=f"{capability} authority is not granted by human approval",
    )
