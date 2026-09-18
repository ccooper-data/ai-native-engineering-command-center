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
    VALIDATING = "validating"
    QUALITY_PASSED = "quality_passed"
    REMEDIATION_REQUIRED = "remediation_required"
    REVIEWED = "reviewed"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
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


class ModelUsageArtifact(BaseModel):
    provider: str
    model: str
    response_id: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    reserved_cost_usd: float = 0.0
    estimated_actual_cost_usd: float | None = None


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


class QualityFinding(BaseModel):
    id: str
    severity: str = Field(pattern="^(info|low|medium|high|critical)$")
    category: str
    message: str
    blocking: bool = False


class QAArtifact(BaseModel):
    passed: bool
    tests_planned: list[str]
    findings: list[QualityFinding]
    acceptance_criteria_verified: list[str]


class SecurityArtifact(BaseModel):
    passed: bool
    scans_planned: list[str]
    findings: list[QualityFinding]
    controls_verified: list[str]


class QualityGateArtifact(BaseModel):
    passed: bool
    blocking_findings: list[str]
    decision: str


class RepositoryDryRunArtifact(BaseModel):
    passed: bool
    branch_name: str
    proposed_paths: list[str]
    commit_message: str
    mutation_performed: bool = False


class CIJobEvidence(BaseModel):
    name: str
    conclusion: str
    passed: bool
    checks: list[str] = Field(default_factory=list)


class CIValidationArtifact(BaseModel):
    run_id: int
    commit_sha: str
    passed: bool
    jobs: list[CIJobEvidence]
    source: str = "github-actions"


class TraceabilityItem(BaseModel):
    acceptance_criterion_id: str
    architecture_evidence: list[str] = Field(default_factory=list)
    implementation_evidence: list[str]
    verification_evidence: list[str]
    reviewer_verification: list[str] = Field(default_factory=list)
    covered: bool


class ReviewArtifact(BaseModel):
    passed: bool
    summary: str
    traceability: list[TraceabilityItem]
    findings: list[QualityFinding]
    recommendation: str


class ApprovalDecision(BaseModel):
    approved: bool
    approver: str = Field(min_length=2, max_length=200)
    rationale: str = Field(min_length=3, max_length=2000)


class ApprovalArtifact(BaseModel):
    approved: bool
    approver: str
    rationale: str
    commit_sha: str = Field(min_length=40, max_length=40)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AuditEvent(BaseModel):
    agent: str
    action: str
    status: str
    commit_sha: str | None = Field(default=None, min_length=40, max_length=40)
    evidence_refs: list[str] = Field(default_factory=list)
    duration_ms: int | None = Field(default=None, ge=0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class GovernanceEvidence(BaseModel):
    current_commit_sha: str | None = Field(default=None, min_length=40, max_length=40)
    repository_branch: str | None = None
    ci_run_ids: list[int] = Field(default_factory=list)
    remediation_cycles: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    estimated_actual_cost_usd: float = Field(default=0.0, ge=0.0)


class GovernanceException(BaseModel):
    code: str
    severity: str = Field(pattern="^(info|warning|high|critical)$")
    message: str
    workflow_id: UUID
    evidence: list[str] = Field(default_factory=list)


class ManagementSummary(BaseModel):
    total_workflows: int = Field(ge=0)
    active_workflows: int = Field(ge=0)
    blocked_workflows: int = Field(ge=0)
    pending_approvals: int = Field(ge=0)
    ci_failures: int = Field(ge=0)
    review_failures: int = Field(ge=0)
    total_tokens: int = Field(ge=0)
    estimated_actual_cost_usd: float = Field(ge=0.0)
    exceptions: list[GovernanceException] = Field(default_factory=list)


class ManagementRunView(BaseModel):
    id: UUID
    status: RunStatus
    original_request: str
    provider: str
    model: str
    governance_evidence: GovernanceEvidence
    ci_passed: bool | None = None
    review_passed: bool | None = None
    approval_state: str
    audit_events: list[AuditEvent] = Field(default_factory=list)
    traceability: list[TraceabilityItem] = Field(default_factory=list)
    created_at: datetime


class WorkflowRun(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    original_request: str
    status: RunStatus = RunStatus.CREATED
    planning: PlanningArtifact | None = None
    planning_usage: ModelUsageArtifact | None = None
    architecture: ArchitectureArtifact | None = None
    architecture_usage: ModelUsageArtifact | None = None
    engineering: EngineeringArtifact | None = None
    engineering_usage: ModelUsageArtifact | None = None
    repository_dry_run: RepositoryDryRunArtifact | None = None
    verified_mutation_commit_sha: str | None = Field(default=None, min_length=40, max_length=40)
    qa: QAArtifact | None = None
    security: SecurityArtifact | None = None
    quality_gate: QualityGateArtifact | None = None
    ci_validation: CIValidationArtifact | None = None
    review: ReviewArtifact | None = None
    approval: ApprovalArtifact | None = None
    audit_events: list[AuditEvent] = Field(default_factory=list)
    governance_evidence: GovernanceEvidence = Field(default_factory=GovernanceEvidence)
    provider: str = "mock"
    model: str = "deterministic-v1"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
