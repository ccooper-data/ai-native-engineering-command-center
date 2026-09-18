from datetime import UTC, datetime, timedelta

import pytest

from app.capabilities import evaluate_post_approval_capability
from app.contracts import (
    ActorIdentity,
    ApprovalArtifact,
    CIValidationArtifact,
    EngineeringArtifact,
    IncidentResolution,
    ProposedFileChange,
    WorkflowRun,
)
from app.database import create_schema
from app.identity import (
    InMemoryAssertionReplayGuard,
    AuthorizationContext,
    IdentityAssertion,
    IdentityPolicyError,
    VerificationProvenance,
    require_authorization_context,
    require_human_capability,
)
from app.repository_tools import IsolatedBranchRepositoryExecutor, RepositoryPolicyError
from app.service import EngineeringWorkflowService
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
    guard = InMemoryAssertionReplayGuard()
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


class IncidentMemoryRepository:
    def __init__(self, run: WorkflowRun) -> None:
        self.run = run

    def get(self, run_id):
        return self.run if run_id == self.run.id else None

    def save(self, run):
        self.run = run
        return run


class FailedRollbackClient:
    def __init__(self) -> None:
        self.files = {}
        self.starting_sha = "0" * 40

    def create_branch(self, branch_name: str) -> None:
        pass

    def create_file(self, branch_name, change, message) -> None:
        self.files[change.path] = "CORRUPTED"

    update_file = create_file

    def delete_file(self, branch_name, change, message) -> None:
        self.files.pop(change.path, None)

    def read_file(self, branch_name, path):
        return self.files.get(path)

    def get_branch_commit_sha(self, branch_name):
        return self.starting_sha if not self.files else "a" * 40

    def reset_branch_to_commit(self, branch_name, commit_sha) -> None:
        pass


def test_repository_corruption_to_independent_human_recovery_chain() -> None:
    create_schema()
    run = WorkflowRun(original_request="Exercise repository incident recovery across governance boundaries.")
    run.engineering = EngineeringArtifact(
        branch_name="agent/integrated-incident",
        commit_message="test: integrated incident",
        summary="integrated incident",
        files=[ProposedFileChange(path="src/proof.py", operation="create", purpose="proof", content="VALUE = 1\n")],
        acceptance_criteria_addressed=["AC-001"],
        tests_required=["unit"],
        security_notes=[],
    )
    repository = IncidentMemoryRepository(run)
    service = EngineeringWorkflowService(repository)
    executor = IsolatedBranchRepositoryExecutor(FailedRollbackClient(), "agent/integrated-incident")
    with pytest.raises(RepositoryPolicyError, match="CRITICAL: rollback verification failed"):
        service.execute_verified_mutation(run.id, executor)
    assert run.repository_incident is not None
    assert run.repository_incident.resolved is False

    now = datetime.now(UTC)
    assertion = IdentityAssertion(
        subject="github:user:independent-resolver",
        actor_type="human",
        authentication_source="github-oidc",
        role="incident-resolver",
        verification=VerificationProvenance(
            issuer="https://token.actions.githubusercontent.com",
            audience="ai-native-engineering-command-center",
            verification_method="test-verified",
            assertion_id=f"incident-recovery-{run.id}",
            authorization_context=AuthorizationContext(
                capability="resolve-repository-incident",
                workflow_id=str(run.id),
                commit_sha="a" * 40,
            ),
            issued_at=now - timedelta(minutes=1),
            expires_at=now + timedelta(minutes=5),
        ),
    )
    resolution = IncidentResolution(
        rationale="Independent human verified repository recovery.",
        restored_commit_sha="a" * 40,
        repository_state_verified=True,
    )
    recovered = service.resolve_repository_incident(run.id, resolution, assertion, "a" * 40)
    assert recovered.repository_incident.resolved is True
    assert recovered.verified_mutation_commit_sha is None
    assert recovered.ci_validation is None
    assert recovered.approval is None
