from abc import ABC, abstractmethod

from .contracts import (
    AcceptanceCriterion,
    ArchitectureArtifact,
    ArchitectureDecision,
    EngineeringArtifact,
    PlanningArtifact,
    ProposedFileChange,
)


class PlanningProvider(ABC):
    name: str
    model: str

    @abstractmethod
    def plan(self, product_request: str) -> PlanningArtifact:
        raise NotImplementedError


class ArchitectureProvider(ABC):
    name: str
    model: str

    @abstractmethod
    def design(self, product_request: str, plan: PlanningArtifact) -> ArchitectureArtifact:
        raise NotImplementedError


class EngineeringProvider(ABC):
    name: str
    model: str

    @abstractmethod
    def implement(
        self,
        product_request: str,
        plan: PlanningArtifact,
        architecture: ArchitectureArtifact,
    ) -> EngineeringArtifact:
        raise NotImplementedError


class MockPlanningProvider(PlanningProvider):
    name = "mock"
    model = "deterministic-v1"

    def plan(self, product_request: str) -> PlanningArtifact:
        return PlanningArtifact(
            business_objective="Convert the request into a measurable, secure, testable capability.",
            scope=["Define API/backend changes", "Define client experience", "Preserve traceability"],
            assumptions=[
                f"Originating request: {product_request}",
                "Existing authentication will be reused where possible",
                "Production deployment requires human approval",
            ],
            functional_requirements=[
                "Expose the capability through a documented API contract",
                "Present results to authorized client users",
                "Trace requirements to implementation and test evidence",
            ],
            non_functional_requirements=[
                "Changes must be observable and auditable",
                "Sensitive information must not enter application logs",
                "API compatibility changes require explicit approval",
            ],
            acceptance_criteria=[
                AcceptanceCriterion(id="AC-001", statement="Authorized users can use the capability end to end"),
                AcceptanceCriterion(id="AC-002", statement="Automated tests cover success and failure paths"),
                AcceptanceCriterion(id="AC-003", statement="No unresolved blocking security findings remain"),
            ],
            dependencies=["Application repository", "Authentication service", "Deployment pipeline"],
            risks=["Unstated business rules", "Client/API drift", "Generated-code regressions"],
            implementation_tasks=["Design", "Implement", "Test", "Security review", "Human approval"],
        )


class MockArchitectureProvider(ArchitectureProvider):
    name = "mock"
    model = "deterministic-v1"

    def design(self, product_request: str, plan: PlanningArtifact) -> ArchitectureArtifact:
        return ArchitectureArtifact(
            summary="Implement an authenticated API-backed feature with durable state and explicit contracts.",
            affected_components=["Next.js client", "FastAPI API", "PostgreSQL", "Agent workflow", "CI/CD"],
            data_flow=["Client request", "API validation", "Service execution", "Persistence", "Response", "Telemetry"],
            api_changes=["Versioned REST contract", "Document failure responses", "Contract tests"],
            data_changes=["Migration-controlled schema changes", "Persist only approved data"],
            security_controls=["Resource authorization", "Secret-safe logging", "Static/security scans", "Human deploy approval"],
            observability_requirements=["Trace workflow IDs", "Measure latency/failures", "Audit tool actions"],
            decisions=[
                ArchitectureDecision(
                    id="ADR-AGENT-001",
                    title="Contract-first service boundary",
                    decision="Expose the capability through a versioned REST API before client coupling.",
                    rationale="Supports independent evolution and executable acceptance tests.",
                    consequences=["Maintain OpenAPI", "Maintain contract tests"],
                ),
                ArchitectureDecision(
                    id="ADR-AGENT-002",
                    title="Human-controlled production transition",
                    decision="Keep merge/deployment authorization outside LLM authority.",
                    rationale="Consequential production transitions require accountable approval.",
                    consequences=["Workflow pauses for approval", "Approval becomes audit evidence"],
                ),
            ],
            implementation_sequence=["Contracts", "Backend", "Client", "Tests", "Security review", "Human approval"],
        )


class MockEngineeringProvider(EngineeringProvider):
    """Produces a bounded proposed change set; it has no repository-write authority."""

    name = "mock"
    model = "deterministic-v1"

    def implement(
        self,
        product_request: str,
        plan: PlanningArtifact,
        architecture: ArchitectureArtifact,
    ) -> EngineeringArtifact:
        return EngineeringArtifact(
            branch_name="agent/churn-capability",
            commit_message="feat: implement planned product capability",
            summary=(
                "Propose a minimal contract-first implementation derived from the validated plan "
                "and architecture. Repository mutation is delegated to a separate bounded tool."
            ),
            files=[
                ProposedFileChange(
                    path="src/capability/service.py",
                    operation="create",
                    purpose="Implement the backend capability behind the approved service boundary.",
                    content=(
                        '"""Generated proposal: implementation placeholder for bounded tool execution."""\n\n'
                        "def capability_status() -> dict[str, str]:\n"
                        '    return {"status": "ready-for-integration"}\n'
                    ),
                ),
                ProposedFileChange(
                    path="tests/test_capability.py",
                    operation="create",
                    purpose="Provide executable evidence for the primary capability path.",
                    content=(
                        "from src.capability.service import capability_status\n\n\n"
                        "def test_capability_status() -> None:\n"
                        '    assert capability_status()["status"] == "ready-for-integration"\n'
                    ),
                ),
            ],
            acceptance_criteria_addressed=[criterion.id for criterion in plan.acceptance_criteria],
            tests_required=["Unit tests", "API contract tests", "Authorization tests", "Regression tests"],
            security_notes=architecture.security_controls,
        )
