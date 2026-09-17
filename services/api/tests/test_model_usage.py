from app.config import Settings
from app.contracts import AcceptanceCriterion, PlanningArtifact
from app.llm import GenerationMetadata, ModelUsage
from app.providers import LLMPlanningProvider


class RecordingStructuredLLM:
    name = "test-provider"
    model = "test-model"

    def __init__(self) -> None:
        self.last_generation = None

    def generate(self, *, system: str, prompt: str, schema: type[PlanningArtifact]) -> PlanningArtifact:
        self.last_generation = GenerationMetadata(
            provider=self.name,
            model=self.model,
            response_id="response-test-1",
            usage=ModelUsage(input_tokens=100, output_tokens=50, total_tokens=150),
        )
        return PlanningArtifact(
            business_objective="Reduce preventable churn.",
            scope=["Forecast churn"],
            assumptions=["Historical data exists"],
            functional_requirements=["Produce forecasts"],
            non_functional_requirements=["Auditable access"],
            acceptance_criteria=[
                AcceptanceCriterion(id="AC-001", statement="Authorized users can retrieve a forecast")
            ],
            dependencies=["Historical data"],
            risks=["Concept drift"],
            implementation_tasks=["Validate", "Build", "Test"],
        )


def test_planning_provider_retains_generation_usage_metadata() -> None:
    llm = RecordingStructuredLLM()
    provider = LLMPlanningProvider(llm)

    provider.plan("Add customer churn forecasting and expose it through the mobile application.")

    assert llm.last_generation is not None
    assert llm.last_generation.provider == "test-provider"
    assert llm.last_generation.response_id == "response-test-1"
    assert llm.last_generation.usage.total_tokens == 150


def test_mock_mode_still_requires_no_paid_provider() -> None:
    from app.llm import build_structured_llm

    assert build_structured_llm(Settings(llm_provider="mock")) is None
