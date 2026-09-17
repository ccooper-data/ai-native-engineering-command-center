from abc import ABC, abstractmethod

from .contracts import AcceptanceCriterion, PlanningArtifact


class PlanningProvider(ABC):
    name: str
    model: str

    @abstractmethod
    def plan(self, product_request: str) -> PlanningArtifact:
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
