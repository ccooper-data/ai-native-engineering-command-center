from app.contracts import AcceptanceCriterion, PlanningArtifact
from app.providers import LLMPlanningProvider


class RecordingStructuredLLM:
    name = "test-provider"
    model = "test-model"

    def __init__(self) -> None:
        self.system = ""
        self.prompt = ""
        self.schema = None

    def generate(self, *, system: str, prompt: str, schema: type[PlanningArtifact]) -> PlanningArtifact:
        self.system = system
        self.prompt = prompt
        self.schema = schema
        return PlanningArtifact(
            business_objective="Reduce preventable churn with actionable forecasts.",
            scope=["Forecast churn", "Expose results to authorized mobile users"],
            assumptions=["Historical labeled customer data is available"],
            functional_requirements=["Produce churn risk forecasts"],
            non_functional_requirements=["Forecast access is auditable"],
            acceptance_criteria=[
                AcceptanceCriterion(id="AC-001", statement="Authorized users can retrieve a churn forecast")
            ],
            dependencies=["Historical customer data"],
            risks=["Concept drift"],
            implementation_tasks=["Validate data", "Design", "Implement", "Test"],
        )


def test_llm_planning_provider_requests_schema_validated_plan() -> None:
    llm = RecordingStructuredLLM()
    provider = LLMPlanningProvider(llm)

    artifact = provider.plan(
        "Add customer churn forecasting to our SaaS product and expose the results through the mobile app."
    )

    assert provider.name == "test-provider"
    assert provider.model == "test-model"
    assert llm.schema is PlanningArtifact
    assert "Do not write code" in llm.system
    assert "AC-001" in llm.prompt
    assert artifact.acceptance_criteria[0].id == "AC-001"
