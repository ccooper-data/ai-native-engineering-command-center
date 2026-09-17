from app.contracts import (
    AcceptanceCriterion,
    ArchitectureArtifact,
    ArchitectureDecision,
    PlanningArtifact,
)
from app.providers import LLMArchitectureProvider


class RecordingLLM:
    name = "test-provider"
    model = "test-model"

    def __init__(self) -> None:
        self.schema = None
        self.prompt = ""

    def generate(self, *, system, prompt, schema):
        self.schema = schema
        self.prompt = prompt
        return ArchitectureArtifact(
            summary="Contract-first churn architecture",
            affected_components=["API", "mobile", "model service"],
            data_flow=["features", "forecast", "authorized mobile response"],
            api_changes=["Add versioned churn endpoint"],
            data_changes=["Persist forecast metadata"],
            security_controls=["Tenant authorization"],
            observability_requirements=["Trace forecast requests"],
            decisions=[
                ArchitectureDecision(
                    id="ADR-001",
                    title="Versioned forecast API",
                    decision="Expose forecasts through a versioned API",
                    rationale="Decouples mobile from model internals",
                    consequences=["Maintain contract tests"],
                )
            ],
            implementation_sequence=["API contract", "model service", "mobile", "tests"],
        )


def test_architecture_provider_consumes_approved_plan_as_structured_context() -> None:
    plan = PlanningArtifact(
        business_objective="Reduce churn",
        scope=["Forecast churn"],
        assumptions=["Historical data exists"],
        functional_requirements=["Produce forecast"],
        non_functional_requirements=["Audit access"],
        acceptance_criteria=[
            AcceptanceCriterion(id="AC-001", statement="Forecast is retrievable")
        ],
        dependencies=["Customer data"],
        risks=["Drift"],
        implementation_tasks=["Build", "Test"],
    )
    llm = RecordingLLM()
    provider = LLMArchitectureProvider(llm)

    artifact = provider.design("Add churn forecasting to the mobile app.", plan)

    assert llm.schema is ArchitectureArtifact
    assert "AC-001" in llm.prompt
    assert "APPROVED PLAN" in llm.prompt
    assert artifact.decisions[0].id == "ADR-001"
