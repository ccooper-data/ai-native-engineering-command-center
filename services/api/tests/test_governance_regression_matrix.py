import pytest

from app.capabilities import evaluate_post_approval_capability
from app.contracts import (
    ActorIdentity,
    ApprovalArtifact,
    CIValidationArtifact,
    WorkflowRun,
)
from app.identity import (
    AssertionReplayGuard,
    AuthorizationContext,
    IdentityAssertion,
    IdentityPolicyError,
    VerificationProvenance,
    require_authorization_context,
    require_human_capability,
)
from app.source_preflight import engineering_artifact_digest, validate_source_preflight

SHA = "a" * 40


def test_governance_regression_matrix_blocks_cross_control_attacks() -> None:
    actor = ActorIdentity(
        identity_id="service-attacker",
        actor_type="service",
        authentication_source="internal-capability",
        role="workflow-approver",
    )
    with pytest.raises(IdentityPolicyError, match="human identity"):
        require_human_capability(actor, "approve-workflow")

    run = WorkflowRun(original_request="Exercise the integrated governance regression matrix.")
    run.ci_validation = CIValidationArtifact(run_id=1, commit_sha=SHA, passed=True, jobs=[])
    run.approval = ApprovalArtifact(
        approved=True,
        approver=ActorIdentity(
            identity_id="github:user:approver",
            actor_type="human",
            authentication_source="github-oidc",
            role="workflow-approver",
        ),
        rationale="Approved exact validated commit.",
        commit_sha=SHA,
    )
    assert evaluate_post_approval_capability(run, "b" * 40, "draft_pr").allowed is False
    assert evaluate_post_approval_capability(run, SHA, "merge").allowed is False
    assert evaluate_post_approval_capability(run, SHA, "deploy").allowed is False


def test_context_replay_and_preflight_staleness_fail_closed() -> None:
    from datetime import UTC, datetime, timedelta

    now = datetime.now(UTC)
    assertion = IdentityAssertion(
        subject="github:user:approver",
        actor_type="human",
        authentication_source="github-oidc",
        role="workflow-approver",
        verification=VerificationProvenance(
            issuer="https://token.actions.githubusercontent.com",
            audience="ai-native-engineering-command-center",
            verification_method="test-verified",
            assertion_id="regression-replay-1",
            authorization_context=AuthorizationContext(
                capability="approve-workflow",
                workflow_id="workflow-a",
                commit_sha=SHA,
            ),
            issued_at=now - timedelta(minutes=1),
            expires_at=now + timedelta(minutes=5),
        ),
    )
    with pytest.raises(IdentityPolicyError, match="does not match"):
        require_authorization_context(
            assertion,
            capability="approve-workflow",
            workflow_id="workflow-b",
            commit_sha=SHA,
        )
    guard = AssertionReplayGuard()
    guard.consume(assertion)
    with pytest.raises(IdentityPolicyError, match="already been consumed"):
        guard.consume(assertion)


def test_preflight_digest_cannot_follow_modified_source() -> None:
    from app.contracts import EngineeringArtifact, ProposedFileChange

    artifact = EngineeringArtifact(
        branch_name="agent/regression",
        commit_message="test: regression",
        summary="regression",
        files=[
            ProposedFileChange(
                path="src/example.py",
                operation="create",
                purpose="regression",
                content="VALUE = 1\n",
            )
        ],
        acceptance_criteria_addressed=["AC-001"],
        tests_required=["regression"],
        security_notes=[],
    )
    result = validate_source_preflight(artifact)
    artifact.files[0].content = "VALUE = 2\n"
    assert result.artifact_digest != engineering_artifact_digest(artifact)
