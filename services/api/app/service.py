from typing import Protocol
from uuid import UUID

from .contracts import AuditEvent, ProductRequest, RunStatus, WorkflowRun
from .graph import build_engineering_graph
from .providers import (
    ArchitectureProvider,
    MockArchitectureProvider,
    MockPlanningProvider,
    PlanningProvider,
)


class RunRepository(Protocol):
    def save(self, run: WorkflowRun) -> WorkflowRun: ...

    def get(self, run_id: UUID) -> WorkflowRun | None: ...


class EngineeringWorkflowService:
    def __init__(
        self,
        repository: RunRepository,
        planning_provider: PlanningProvider | None = None,
        architecture_provider: ArchitectureProvider | None = None,
    ) -> None:
        self.repository = repository
        self.planning_provider = planning_provider or MockPlanningProvider()
        self.architecture_provider = architecture_provider or MockArchitectureProvider()
        self.graph = build_engineering_graph(
            self.planning_provider,
            self.architecture_provider,
        )

    def create_and_run(self, product_request: ProductRequest) -> WorkflowRun:
        run = WorkflowRun(
            original_request=product_request.request,
            provider=self.planning_provider.name,
            model=self.planning_provider.model,
            status=RunStatus.PLANNING,
            audit_events=[
                AuditEvent(agent="system", action="workflow_created", status="success")
            ],
        )
        self.repository.save(run)

        result = self.graph.invoke(
            {
                "original_request": run.original_request,
                "status": run.status,
                "planning": None,
                "architecture": None,
                "audit_events": run.audit_events,
            }
        )
        run.status = result["status"]
        run.planning = result["planning"]
        run.architecture = result["architecture"]
        run.audit_events = result["audit_events"]
        return self.repository.save(run)
