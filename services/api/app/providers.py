from abc import ABC, abstractmethod

from .contracts import (
    AcceptanceCriterion,
    ArchitectureArtifact,
    ArchitectureDecision,
    PlanningArtifact,
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


class MockPlanningProvider(PlanningProvider):
    """Deterministic provider used to develop orchestration without API spend."""

    name = "mock"
    model = "deterministic-v1"

    def plan(self, product_request: str) -> PlanningArtifact:
        return PlanningArtifact(
            business_objective=(
                "Convert the product request into a measurable, secure capability that can be "
                "implemented incrementally and verified against explicit acceptance criteria."
            ),
            scope=[
                "Clarify the requested customer-facing capability",
                "Define backend/API changes required to support the capability",
                "Define client experience and operational expectations",
            ],
            assumptions=[
                f"The originating request is: {product_request}",
                "Existing authentication and authorization mechanisms will be reused where possible",
                "Production deployment requires human approval",
            ],
            functional_requirements=[
                "The system must expose the requested capability through a documented API contract",
                "The client application must present the resulting information to authorized users",
                "The system must preserve traceability from requirement to implementation and test evidence",
            ],
            non_functional_requirements=[
                "Changes must be observable and auditable",
                "Sensitive information must not be written to application logs",
                "API changes must preserve backward compatibility unless explicitly approved",
            ],
            acceptance_criteria=[
                AcceptanceCriterion(
                    id="AC-001",
                    statement="An authorized user can access the implemented capability end to end",
                ),
                AcceptanceCriterion(
                    id="AC-002",
                    statement="Automated tests verify the primary success and failure paths",
                ),
                AcceptanceCriterion(
                    id="AC-003",
                    statement="Security and audit controls produce no unresolved blocking findings",
                ),
            ],
            dependencies=[
                "Existing application repository and test environment",
                "Authentication/authorization service",
                "Approved deployment pipeline",
            ],
            risks=[
                "Ambiguous product language may hide unstated business rules",
                "Client and API changes can drift without contract tests",
                "Model-generated implementation can introduce security or regression defects",
            ],
            implementation_tasks=[
                "Validate requirements with product owner",
                "Produce architecture decision and interface changes",
                "Implement changes on an isolated Git branch",
                "Execute automated QA and security checks",
                "Review acceptance-criteria coverage before human approval",
            ],
        )


class MockArchitectureProvider(ArchitectureProvider):
    """Deterministic architecture provider for the first multi-agent handoff."""

    name = "mock"
    model = "deterministic-v1"

    def design(self, product_request: str, plan: PlanningArtifact) -> ArchitectureArtifact:
        return ArchitectureArtifact(
            summary=(
                "Implement the requested capability as an authenticated API-backed feature with "
                "durable data, explicit contracts, client integration, and observable execution."
            ),
            affected_components=[
                "Next.js client experience",
                "FastAPI application API",
                "PostgreSQL persistence layer",
                "Background/agent workflow",
                "CI/CD quality gates",
            ],
            data_flow=[
                "Authorized client requests capability",
                "API validates identity, authorization, and request contract",
                "Service reads or computes the required result",
                "Durable result/metadata is persisted where required",
                "API returns versioned response to client",
                "Telemetry records execution without sensitive payload leakage",
            ],
            api_changes=[
                "Define versioned REST contract for the new capability",
                "Document success, validation, authorization, and unavailable-result responses",
                "Add contract tests to prevent client/API drift",
            ],
            data_changes=[
                "Persist capability metadata and version identifiers when required",
                "Use migration-controlled schema changes",
                "Retain only data required by the approved product requirement",
            ],
            security_controls=[
                "Reuse centralized authentication and enforce resource-level authorization",
                "Prevent secrets and sensitive customer data from entering logs or model prompts",
                "Run dependency, secret, and static-analysis checks before review",
                "Require explicit human approval before production deployment",
            ],
            observability_requirements=[
                "Trace request and workflow identifiers across services",
                "Record latency, failure rate, and dependency errors",
                "Emit auditable agent/tool events without storing sensitive content",
            ],
            decisions=[
                ArchitectureDecision(
                    id="ADR-AGENT-001",
                    title="Contract-first service boundary",
                    decision="Expose the capability through a versioned REST API before client coupling.",
                    rationale=(
                        "The plan requires client access while preserving independent backend and "
                        "frontend evolution and executable acceptance tests."
                    ),
                    consequences=[
                        "Requires OpenAPI and contract-test maintenance",
                        "Allows web/mobile clients to evolve independently",
                    ],
                ),
                ArchitectureDecision(
                    id="ADR-AGENT-002",
                    title="Human-controlled production transition",
                    decision="Keep merge/deployment authorization outside LLM authority.",
                    rationale="Production state transitions are consequential and require accountable approval.",
                    consequences=[
                        "Autonomous work pauses at the approval gate",
                        "Approval identity and timestamp become auditable workflow evidence",
                    ],
                ),
            ],
            implementation_sequence=[
                "Finalize API and data contracts",
                "Implement persistence/service changes",
                "Implement client integration",
                "Add functional, contract, and security tests",
                "Run independent QA/security review",
                "Require human approval before merge/deployment",
            ],
        )
