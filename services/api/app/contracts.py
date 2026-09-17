from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    CREATED = "created"
    PLANNING = "planning"
    PLANNED = "planned"
    ARCHITECTING = "architecting"
    ARCHITECTED = "architected"
    ENGINEERING = "engineering"
    IMPLEMENTED = "implemented"
    FAILED = "failed"


class ProductRequest(BaseModel):
    request: str = Field(min_length=10, max_length=10_000)


class AcceptanceCriterion(BaseModel):
    id: str
    statement: str


class PlanningArtifact(BaseModel):
    business_objective: str
    scope: list[str]
    assumptions: list[str]
    functional_requirements: list[str]
    non_functional_requirements: list[str]
    acceptance_criteria: list[AcceptanceCriterion]
    dependencies: list[str]
    risks: list[str]
    implementation_tasks: list[str]


class ArchitectureDecision(BaseModel):
    id: str
    title: str
    decision: str
    rationale: str
    consequences: list[str]


class ArchitectureArtifact(BaseModel):
    summary: str
    affected_components: list[str]
    data_flow: list[str]
    api_changes: list[str]
    data_changes: list[str]
    security_controls: list[str]
    observability_requirements: list[str]
    decisions: list[ArchitectureDecision]
    implementation_sequence: list[str]


class ProposedFileChange(BaseModel):
    path: str
    operation: str = Field(pattern="^(create|update|delete)$")
    purpose: str
    content: str | None = None


class EngineeringArtifact(BaseModel):
    branch_name: str
    commit_message: str
    summary: str
    files: list[ProposedFileChange]
    acceptance_criteria_addressed: list[str]
    tests_required: list[str]
    security_notes: list[str]


class AuditEvent(BaseModel):
    agent: str
    action: str
    status: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class WorkflowRun(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    original_request: str
    status: RunStatus = RunStatus.CREATED
    planning: PlanningArtifact | None = None
    architecture: ArchitectureArtifact | None = None
    engineering: EngineeringArtifact | None = None
    audit_events: list[AuditEvent] = Field(default_factory=list)
    provider: str = "mock"
    model: str = "deterministic-v1"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
