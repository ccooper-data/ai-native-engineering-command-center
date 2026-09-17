from typing import Protocol
from uuid import UUID

from .contracts import AuditEvent, ProductRequest, RunStatus, WorkflowRun
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
        result = self.graph.invoke({
            "original_request": run.original_request,
            "status": run.status,
            "planning": None,
            "architecture": None,
            "engineering": None,
            "qa": None,
            "security": None,
            "quality_gate": None,
            "audit_events": run.audit_events,
        })
        for field in ("status", "planning", "architecture", "engineering", "qa", "security", "quality_gate", "audit_events"):
            setattr(run, field, result[field])
        return self.repository.save(run)
