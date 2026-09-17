from typing import Protocol
from uuid import UUID

from .config import Settings, settings
from .contracts import (
    ApprovalArtifact,
    ApprovalDecision,
    AuditEvent,
    CIValidationArtifact,
    ModelUsageArtifact,
    ProductRequest,
    RunStatus,
    WorkflowRun,
)
from .graph import build_engineering_graph
from .llm import build_structured_llm
from .preflight import RunCostBudget
from .providers import (
    LLMArchitectureProvider,
    LLMPlanningProvider,
    MockArchitectureProvider,
    MockEngineeringProvider,
    MockPlanningProvider,
    PlanningProvider,
)
from .quality import MockQAProvider, MockSecurityProvider


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
            )
            run.audit_events.append(
                AuditEvent(agent="planning", action="record_model_usage", status="success")
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
        self, run_id: UUID, decision: ApprovalDecision
    ) -> WorkflowRun | None:
        run = self.repository.get(run_id)
        if run is None:
            return None
        if run.status != RunStatus.AWAITING_APPROVAL or run.review is None or not run.review.passed:
            raise ValueError("Workflow is not eligible for human approval")
        if run.ci_validation is None or not run.ci_validation.passed:
            raise ValueError("Successful executable CI evidence is required before human approval")
        run.approval = ApprovalArtifact(
            approved=decision.approved,
            approver=decision.approver,
            rationale=decision.rationale,
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
