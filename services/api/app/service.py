from typing import Protocol
from uuid import UUID

from .authorization import authorize_sensitive_action
from .config import Settings, settings
from .contracts import (
    ActorIdentity,
    ApprovalArtifact,
    ApprovalDecision,
    AuditEvent,
    CIValidationArtifact,
    IncidentResolution,
    ModelUsageArtifact,
    ProductRequest,
    RepositoryDryRunArtifact,
    RepositoryIncident,
    RunStatus,
    SourcePreflightEvidence,
    SourcePreflightFindingEvidence,
    WorkflowRun,
)
from .graph import build_engineering_graph
from .identity import IdentityAssertion
from .llm import build_structured_llm
from .preflight import RunCostBudget
from .providers import (
    LLMArchitectureProvider,
    LLMEngineeringProvider,
    LLMPlanningProvider,
    MockArchitectureProvider,
    MockEngineeringProvider,
    MockPlanningProvider,
    PlanningProvider,
)
from .quality import MockQAProvider, MockSecurityProvider
from .replay_store import SqlAssertionReplayGuard
from .repository_tools import (
    DryRunRepositoryExecutor,
    RepositoryExecutionResult,
    RepositoryExecutor,
    RepositoryPolicyError,
)
from .source_preflight import validate_source_preflight


class RunRepository(Protocol):
    def save(self, run: WorkflowRun) -> WorkflowRun: ...

    def get(self, run_id: UUID) -> WorkflowRun | None: ...


def build_planning_provider(runtime_settings: Settings) -> PlanningProvider:
    llm = build_structured_llm(runtime_settings)
    if llm is None:
        return MockPlanningProvider()
    return LLMPlanningProvider(llm)


class EngineeringWorkflowService:
    def __init__(
        self,
        repository: RunRepository,
        runtime_settings: Settings | None = None,
    ) -> None:
        self.repository = repository
        self.settings = runtime_settings or settings
        self.run_cost_budget = RunCostBudget(
            max_run_cost_usd=self.settings.llm_max_cost_per_run_usd
        )
        planning_llm = build_structured_llm(self.settings, self.run_cost_budget)
        self.planning_provider = (
            MockPlanningProvider() if planning_llm is None else LLMPlanningProvider(planning_llm)
        )
        if self.settings.architecture_llm_enabled and planning_llm is not None:
            architecture_llm = build_structured_llm(self.settings, self.run_cost_budget)
            assert architecture_llm is not None
            self.architecture_provider = LLMArchitectureProvider(architecture_llm)
        else:
            self.architecture_provider = MockArchitectureProvider()
        if self.settings.engineering_llm_enabled and planning_llm is not None:
            engineering_llm = build_structured_llm(self.settings, self.run_cost_budget)
            assert engineering_llm is not None
            self.engineering_provider = LLMEngineeringProvider(engineering_llm)
        else:
            self.engineering_provider = MockEngineeringProvider()
        self.qa_provider = MockQAProvider()
        self.security_provider = MockSecurityProvider()
        self.graph = build_engineering_graph(
            self.planning_provider,
            self.architecture_provider,
            self.engineering_provider,
            self.qa_provider,
            self.security_provider,
        )

    def create_and_run(self, product_request: ProductRequest) -> WorkflowRun:
        run = WorkflowRun(
            original_request=product_request.request,
            provider=self.planning_provider.name,
            model=self.planning_provider.model,
            status=RunStatus.PLANNING,
            audit_events=[AuditEvent(agent="system", action="workflow_created", status="success")],
        )
        self.repository.save(run)
        result = self.graph.invoke(
            {
                "original_request": run.original_request,
                "status": run.status,
                "planning": None,
                "architecture": None,
                "engineering": None,
                "qa": None,
                "security": None,
                "quality_gate": None,
                "review": None,
                "audit_events": run.audit_events,
            }
        )
        fields = (
            "status",
            "planning",
            "architecture",
            "engineering",
            "qa",
            "security",
            "quality_gate",
            "review",
            "audit_events",
        )
        for field in fields:
            setattr(run, field, result[field])

        llm = getattr(self.planning_provider, "llm", None)
        generation = getattr(llm, "last_generation", None)
        if generation is not None:
            run.planning_usage = ModelUsageArtifact(
                provider=generation.provider,
                model=generation.model,
                response_id=generation.response_id,
                input_tokens=generation.usage.input_tokens,
                output_tokens=generation.usage.output_tokens,
                total_tokens=generation.usage.total_tokens,
                reserved_cost_usd=generation.reserved_cost_usd,
                estimated_actual_cost_usd=generation.actual_cost_usd,
            )
            run.audit_events.append(
                AuditEvent(agent="planning", action="record_model_usage", status="success")
            )
        if run.engineering is not None:
            preflight = validate_source_preflight(run.engineering)
            run.source_preflight = SourcePreflightEvidence(
                artifact_digest=preflight.artifact_digest,
                passed=preflight.passed,
                findings=[
                    SourcePreflightFindingEvidence(
                        path=finding.path,
                        check=finding.check,
                        passed=finding.passed,
                        message=finding.message,
                    )
                    for finding in preflight.findings
                ],
                checks=[finding.check for finding in preflight.findings],
                paths=sorted({finding.path for finding in preflight.findings}),
                tool_evidence=[finding.message for finding in preflight.findings],
            )
            run.audit_events.append(
                AuditEvent(
                    agent="source-preflight",
                    action="validate_engineering_source",
                    status="success" if preflight.passed else "blocked",
                    evidence_refs=[finding.check for finding in preflight.findings],
                )
            )
            try:
                dry_run = DryRunRepositoryExecutor().apply(run.engineering)
                run.repository_dry_run = RepositoryDryRunArtifact(
                    passed=True,
                    branch_name=dry_run.branch_name,
                    proposed_paths=dry_run.applied_paths,
                    commit_message=dry_run.commit_message,
                    mutation_performed=False,
                )
                run.audit_events.append(
                    AuditEvent(
                        agent="repository-policy",
                        action="engineering_dry_run",
                        status="success",
                    )
                )
            except RepositoryPolicyError:
                run.repository_dry_run = RepositoryDryRunArtifact(
                    passed=False,
                    branch_name=run.engineering.branch_name,
                    proposed_paths=[change.path for change in run.engineering.files],
                    commit_message=run.engineering.commit_message,
                    mutation_performed=False,
                )
                run.audit_events.append(
                    AuditEvent(
                        agent="repository-policy",
                        action="engineering_dry_run",
                        status="blocked",
                    )
                )
                run.status = RunStatus.REMEDIATION_REQUIRED

        engineering_llm = getattr(self.engineering_provider, "llm", None)
        engineering_generation = getattr(engineering_llm, "last_generation", None)
        if engineering_generation is not None:
            run.engineering_usage = ModelUsageArtifact(
                provider=engineering_generation.provider,
                model=engineering_generation.model,
                response_id=engineering_generation.response_id,
                input_tokens=engineering_generation.usage.input_tokens,
                output_tokens=engineering_generation.usage.output_tokens,
                total_tokens=engineering_generation.usage.total_tokens,
                reserved_cost_usd=engineering_generation.reserved_cost_usd,
                estimated_actual_cost_usd=engineering_generation.actual_cost_usd,
            )
            run.audit_events.append(
                AuditEvent(
                    agent="engineering",
                    action="record_model_usage",
                    status="success",
                )
            )

        architecture_llm = getattr(self.architecture_provider, "llm", None)
        architecture_generation = getattr(architecture_llm, "last_generation", None)
        if architecture_generation is not None:
            run.architecture_usage = ModelUsageArtifact(
                provider=architecture_generation.provider,
                model=architecture_generation.model,
                response_id=architecture_generation.response_id,
                input_tokens=architecture_generation.usage.input_tokens,
                output_tokens=architecture_generation.usage.output_tokens,
                total_tokens=architecture_generation.usage.total_tokens,
                reserved_cost_usd=architecture_generation.reserved_cost_usd,
                estimated_actual_cost_usd=architecture_generation.actual_cost_usd,
            )
            run.audit_events.append(
                AuditEvent(
                    agent="architecture",
                    action="record_model_usage",
                    status="success",
                )
            )
        return self.repository.save(run)


    def execute_verified_mutation(
        self,
        run_id: UUID,
        executor: RepositoryExecutor,
    ) -> WorkflowRun | None:
        run = self.repository.get(run_id)
        if run is None:
            return None
        if run.engineering is None:
            raise ValueError("Engineering artifact is required before repository mutation")
        try:
            preflight = validate_source_preflight(run.engineering)
            result: RepositoryExecutionResult = executor.apply(run.engineering, preflight=preflight)
        except RepositoryPolicyError as exc:
            message = str(exc)
            if message.startswith("CRITICAL: rollback verification failed"):
                branch_name = getattr(executor, "authorized_branch", run.engineering.branch_name)
                client = getattr(executor, "client", None)
                observed_sha = client.get_branch_commit_sha(branch_name) if client is not None else "0" * 40
                starting_sha = getattr(client, "starting_sha", None) or "0" * 40
                run.repository_incident = RepositoryIncident(
                    severity="critical",
                    category="rollback_verification_failed",
                    message=message,
                    branch_name=branch_name,
                    starting_commit_sha=starting_sha,
                    observed_commit_sha=observed_sha,
                    mutation_actor=ActorIdentity(identity_id="repository-executor", actor_type="service", authentication_source="internal-capability", role="repository-mutation"),
                )
                run.audit_events.append(AuditEvent(agent="repository", action="rollback_verification", status="critical", commit_sha=observed_sha))
                run.status = RunStatus.FAILED
                self.repository.save(run)
            raise
        if result.commit_sha is None:
            raise ValueError("Verified mutation must return immutable commit SHA evidence")
        run.verified_mutation_commit_sha = result.commit_sha
        run.audit_events.append(AuditEvent(agent="repository", action="verified_mutation", status="success", commit_sha=result.commit_sha, evidence_refs=result.verified_paths))
        return self.repository.save(run)


    def resolve_repository_incident(
        self,
        run_id: UUID,
        resolution: IncidentResolution,
        assertion: IdentityAssertion,
        observed_current_sha: str,
    ) -> WorkflowRun | None:
        run = self.repository.get(run_id)
        if run is None:
            return None
        incident = run.repository_incident
        if incident is None or incident.resolved:
            raise ValueError("No unresolved repository incident exists")
        resolver = authorize_sensitive_action(
            assertion,
            SqlAssertionReplayGuard(),
            capability="resolve-repository-incident",
            workflow_id=str(run.id),
            commit_sha=observed_current_sha,
        )
        if incident.mutation_actor is not None and resolver.identity_id == incident.mutation_actor.identity_id:
            raise ValueError("Critical repository incident requires an independent resolver")
        if not resolution.repository_state_verified:
            raise ValueError("Incident resolution requires verified repository state")
        if resolution.restored_commit_sha != observed_current_sha:
            raise ValueError("Resolution SHA does not match currently observed repository SHA")
        incident.resolved = True
        incident.resolution = resolution
        run.verified_mutation_commit_sha = None
        run.ci_validation = None
        run.review = None
        run.approval = None
        run.status = RunStatus.REMEDIATION_REQUIRED
        run.audit_events.append(
            AuditEvent(
                agent="human",
                action="repository_incident_resolved",
                status="resolved",
                commit_sha=resolution.restored_commit_sha,
                evidence_refs=[resolver.identity_id, resolution.rationale],
            )
        )
        return self.repository.save(run)

    def record_ci_validation(
        self,
        run_id: UUID,
        validation: CIValidationArtifact,
        expected_commit_sha: str,
    ) -> WorkflowRun | None:
        run = self.repository.get(run_id)
        if run is None:
            return None
        if validation.commit_sha != expected_commit_sha:
            raise ValueError("CI evidence commit SHA does not match the executed change set")
        if run.verified_mutation_commit_sha is not None and validation.commit_sha != run.verified_mutation_commit_sha:
            raise ValueError("CI evidence commit SHA does not match verified repository mutation")
        run.ci_validation = validation
        run.audit_events.append(
            AuditEvent(
                agent="ci",
                action="record_executable_validation",
                status="success" if validation.passed else "failed",
            )
        )
        return self.repository.save(run)

    def record_human_approval(
        self, run_id: UUID, decision: ApprovalDecision, assertion: IdentityAssertion, expected_commit_sha: str
    ) -> WorkflowRun | None:
        run = self.repository.get(run_id)
        if run is None:
            return None
        if run.status != RunStatus.AWAITING_APPROVAL or run.review is None or not run.review.passed:
            raise ValueError("Workflow is not eligible for human approval")
        if run.ci_validation is None or not run.ci_validation.passed:
            raise ValueError("Successful executable CI evidence is required before human approval")
        if run.ci_validation.commit_sha != expected_commit_sha:
            raise ValueError("Human approval must target the current validated commit SHA")
        approver = authorize_sensitive_action(
            assertion,
            SqlAssertionReplayGuard(),
            capability="approve-workflow",
            workflow_id=str(run.id),
            commit_sha=expected_commit_sha,
        )
        run.approval = ApprovalArtifact(
            approved=decision.approved,
            approver=approver,
            rationale=decision.rationale,
            commit_sha=run.ci_validation.commit_sha,
        )
        run.status = RunStatus.APPROVED if decision.approved else RunStatus.REJECTED
        run.audit_events.append(
            AuditEvent(
                agent="human",
                action="approval_decision",
                status="approved" if decision.approved else "rejected",
            )
        )
        return self.repository.save(run)
