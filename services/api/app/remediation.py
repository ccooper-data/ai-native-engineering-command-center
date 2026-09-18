from pydantic import BaseModel, Field


class FailureEvidence(BaseModel):
    source: str
    command: str
    exit_code: int
    commit_sha: str = Field(min_length=40, max_length=40)
    diagnostic: str = Field(min_length=1)
    affected_paths: list[str] = Field(default_factory=list)


class RemediationRequest(BaseModel):
    commit_sha: str = Field(min_length=40, max_length=40)
    evidence: list[FailureEvidence]
    allowed_paths: list[str]
    instruction: str


def build_remediation_request(
    commit_sha: str,
    evidence: list[FailureEvidence],
) -> RemediationRequest:
    """Convert executable failures into a bounded Engineering remediation request."""
    if not evidence:
        raise ValueError("Remediation requires executable failure evidence")
    if any(item.exit_code == 0 for item in evidence):
        raise ValueError("Successful checks are not remediation evidence")
    if any(item.commit_sha != commit_sha for item in evidence):
        raise ValueError("Failure evidence must match the failed commit SHA")

    paths = sorted({path for item in evidence for path in item.affected_paths})
    if not paths:
        raise ValueError("Remediation evidence must identify at least one affected path")

    diagnostics = "\n".join(
        f"- {item.source}: {item.command} exited {item.exit_code}: {item.diagnostic}"
        for item in evidence
    )
    return RemediationRequest(
        commit_sha=commit_sha,
        evidence=evidence,
        allowed_paths=paths,
        instruction=(
            "Correct only the failures demonstrated by the executable evidence below. "
            "Do not broaden scope, bypass checks, or modify paths outside allowed_paths.\n"
            f"{diagnostics}"
        ),
    )
