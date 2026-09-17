from typing import Protocol
from uuid import UUID

from .contracts import AuditEvent, ProductRequest, RunStatus, WorkflowRun
from .graph import build_planning_graph
from .providers import MockPlanningProvider, PlanningProvider


class RunRepository(Protocol):
    def save(self, run: WorkflowRun) -> WorkflowRun: ...

    def get(self, run_id: UUID) -> WorkflowRun | None: ...


class PlanningService:
    def __init__(
        self,
        repository: RunRepository,
        provider: PlanningProvider | None = None,
    ) -> None:
        self.repository = repository
        self.provider = provider or MockPlanningProvider()
        self.graph = build_planning_graph(self.provider)

    def create_and_plan(self, product_request: ProductRequest) -> WorkflowRun:
        run = WorkflowRun(
            original_request=product_request.request,
            provider=self.provider.name,
            model=self.provider.model,
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
                "audit_events": run.audit_events,
            }
        )
        run.status = result["status"]
        run.planning = result["planning"]
        run.audit_events = result["audit_events"]
        return self.repository.save(run)
