from uuid import UUID

from fastapi import FastAPI, HTTPException, status

from .contracts import ProductRequest, WorkflowRun
from .service import InMemoryRunRepository, PlanningService

app = FastAPI(
    title="AI-Native Engineering Command Center API",
    version="0.1.0",
    description="Auditable orchestration API for bounded autonomous software engineering.",
)

repository = InMemoryRunRepository()
planning_service = PlanningService(repository=repository)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/runs", response_model=WorkflowRun, status_code=status.HTTP_201_CREATED)
def create_run(product_request: ProductRequest) -> WorkflowRun:
    return planning_service.create_and_plan(product_request)


@app.get("/api/v1/runs/{run_id}", response_model=WorkflowRun)
def get_run(run_id: UUID) -> WorkflowRun:
    run = repository.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Workflow run not found")
    return run
