import pytest

from app.contracts import (
    ActorIdentity,
    ApprovalArtifact,
    CIValidationArtifact,
    IncidentResolution,
    RepositoryIncident,
    ReviewArtifact,
    RunStatus,
    WorkflowRun,
)
from app.service import EngineeringWorkflowService

SHA = "a" * 40


class MemoryRepository:
    def __init__(self, run: WorkflowRun) -> None:
        self.run = run

    def get(self, run_id):
        return self.run if run_id == self.run.id else None

    def save(self, run):
        self.run = run
        return run


def incident_run() -> WorkflowRun:
    run = WorkflowRun(original_request="Resolve uncertain repository state.")
    run.repository_incident = RepositoryIncident(
        severity="critical",
        category="rollback_verification_failed",
        message="state uncertain",
        branch_name="agent/test",
        starting_commit_sha="0" * 40,
        observed_commit_sha=SHA,
        mutation_actor=ActorIdentity(identity_id="repository-executor", actor_type="service", authentication_source="internal-capability", role="repository-mutation"),
    )
    run.verified_mutation_commit_sha = SHA
    run.ci_validation = CIValidationArtifact(run_id=1, commit_sha=SHA, passed=True, jobs=[])
    run.review = ReviewArtifact(passed=True, summary="old", traceability=[], findings=[], recommendation="request_human_approval")
    run.approval = ApprovalArtifact(approved=True, approver="old", rationale="old", commit_sha=SHA)
    return run


def test_verified_human_resolution_invalidates_preincident_evidence() -> None:
    run = incident_run()
    service = EngineeringWorkflowService(MemoryRepository(run))
    resolution = IncidentResolution(resolver=ActorIdentity(identity_id="human-operator", actor_type="human", authentication_source="test-auth", role="incident-resolver"), rationale="Repository inspected and restored.", restored_commit_sha=SHA, repository_state_verified=True)
    updated = service.resolve_repository_incident(run.id, resolution, SHA)
    assert updated.repository_incident.resolved is True
    assert updated.verified_mutation_commit_sha is None
    assert updated.ci_validation is None
    assert updated.review is None
    assert updated.approval is None
    assert updated.status == RunStatus.REMEDIATION_REQUIRED


def test_resolution_rejects_unverified_repository_state() -> None:
    run = incident_run()
    service = EngineeringWorkflowService(MemoryRepository(run))
    resolution = IncidentResolution(resolver=ActorIdentity(identity_id="human-operator", actor_type="human", authentication_source="test-auth", role="incident-resolver"), rationale="Not verified.", restored_commit_sha=SHA, repository_state_verified=False)
    with pytest.raises(ValueError, match="verified repository state"):
        service.resolve_repository_incident(run.id, resolution, SHA)


def test_resolution_rejects_sha_mismatch() -> None:
    run = incident_run()
    service = EngineeringWorkflowService(MemoryRepository(run))
    resolution = IncidentResolution(resolver=ActorIdentity(identity_id="human-operator", actor_type="human", authentication_source="test-auth", role="incident-resolver"), rationale="Checked.", restored_commit_sha=SHA, repository_state_verified=True)
    with pytest.raises(ValueError, match="currently observed"):
        service.resolve_repository_incident(run.id, resolution, "b" * 40)


def test_incident_actor_cannot_self_resolve_critical_incident() -> None:
    run = incident_run()
    service = EngineeringWorkflowService(MemoryRepository(run))
    resolution = IncidentResolution(
        resolver=ActorIdentity(identity_id="repository-executor", actor_type="service", authentication_source="internal-capability", role="repository-mutation"),
        rationale="Self-resolution must not be sufficient.",
        restored_commit_sha=SHA,
        repository_state_verified=True,
    )
    with pytest.raises(ValueError, match="independent resolver"):
        service.resolve_repository_incident(run.id, resolution, SHA)
