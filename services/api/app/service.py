from uuid import UUID

from .contracts import AuditEvent, ProductRequest, RunStatus, WorkflowRun
from .providers import MockPlanningProvider, PlanningProvider


class InMemoryRunRepository:
    """Milestone-1 development repository. PostgreSQL replaces this before milestone completion."""

    def __init__(self) -> None:
        self._runs: dict[UUID, WorkflowRun] = {}

    def save(self, run: WorkflowRun) -> WorkflowRun:
        self._runs[run.id] = run
        return run

    def get(self, run_id: UUID) -> WorkflowRun | None:
        return self._runs.get(run_id)


class PlanningService:
    def __init__(
        self,
        repository: InMemoryRunRepository,
        provider: PlanningProvider | None = None,
    ) -> None:
        self.repository = repository
        self.provider = provider or MockPlanningProvider()

    def create_and_plan(self, product_request: ProductRequest) -> WorkflowRun:
        run = WorkflowRun(
            original_request=product_request.request,
            provider=self.provider.name,
            model=self.provider.model,
        )
        run.audit_events.append(
            AuditEvent(agent="system", action="workflow_created", status="success")
        )
        run.status = RunStatus.PLANNING
        self.repository.save(run)

        try:
            run.planning = self.provider.plan(product_request.request)
            run.status = RunStatus.PLANNED
            run.audit_events.append(
                AuditEvent(agent="planning", action="create_plan", status="success")
            )
        except Exception:
            run.status = RunStatus.FAILED
            run.audit_events.append(
                AuditEvent(agent="planning", action="create_plan", status="failed")
            )
            self.repository.save(run)
            raise

        return self.repository.save(run)
