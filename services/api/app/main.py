from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .contracts import (
    ApprovalDecision,
    ManagementRunView,
    ManagementSummary,
    ProductRequest,
    WorkflowRun,
)
from .database import SqlRunRepository, create_schema
from .management import build_management_summary, build_management_view
from .service import EngineeringWorkflowService


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_schema(); yield


app = FastAPI(title="AI-Native Engineering Command Center API", version="0.3.0", description="Auditable orchestration API for bounded autonomous software engineering.", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
repository = SqlRunRepository(); workflow_service = EngineeringWorkflowService(repository=repository)


@app.get("/health")
def health() -> dict[str, str]: return {"status": "ok"}


@app.post("/api/v1/runs", response_model=WorkflowRun, status_code=status.HTTP_201_CREATED)
def create_run(product_request: ProductRequest) -> WorkflowRun: return workflow_service.create_and_run(product_request)


@app.get("/api/v1/runs/{run_id}", response_model=WorkflowRun)
def get_run(run_id: UUID) -> WorkflowRun:
    run = repository.get(run_id)
    if run is None: raise HTTPException(status_code=404, detail="Workflow run not found")
    return run


@app.get("/api/v1/management/summary", response_model=ManagementSummary)
def get_management_summary() -> ManagementSummary:
    return build_management_summary(repository.list())


@app.get("/api/v1/management/runs/{run_id}", response_model=ManagementRunView)
def get_management_run(run_id: UUID) -> ManagementRunView:
    run = repository.get(run_id)
    if run is None: raise HTTPException(status_code=404, detail="Workflow run not found")
    return build_management_view(run)


@app.post("/api/v1/runs/{run_id}/approval", response_model=WorkflowRun)
def approve_run(run_id: UUID, decision: ApprovalDecision, commit_sha: str) -> WorkflowRun:
    try: run = workflow_service.record_human_approval(run_id, decision, commit_sha)
    except ValueError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc
    if run is None: raise HTTPException(status_code=404, detail="Workflow run not found")
    return run
