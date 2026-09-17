from typing import Protocol
from uuid import UUID

from .contracts import (
    ApprovalArtifact,
    ApprovalDecision,
    AuditEvent,
    ProductRequest,
    RunStatus,
    WorkflowRun,
)
from .graph import build_engineering_graph
from .providers import MockArchitectureProvider, MockEngineeringProvider, MockPlanningProvider
from .quality import MockQAProvider, MockSecurityProvider


class RunRepository(Protocol):
    def save(self, run: WorkflowRun) -> WorkflowRun: ...

    def get(self, run_id: UUID) -> WorkflowRun | None: ...


class EngineeringWorkflowService:
    def __init__(self, repository: RunRepository) -> None:
        self.repository = repository
        self.planning_provider = MockPlanningProvider()
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
            "status", "planning", "architecture", "engineering", "qa", "security",
            "quality_gate", "review", "audit_events",
        )
        for field in fields:
            setattr(run, field, result[field])
        return self.repository.save(run)

    def record_human_approval(
        self, run_id: UUID, decision: ApprovalDecision
    ) -> WorkflowRun | None:
        run = self.repository.get(run_id)
        if run is None:
            return None
        if run.status != RunStatus.AWAITING_APPROVAL or run.review is None or not run.review.passed:
            raise ValueError("Workflow is not eligible for human approval")
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
