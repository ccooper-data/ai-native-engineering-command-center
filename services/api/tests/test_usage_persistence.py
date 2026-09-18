from app.config import Settings
from app.contracts import AcceptanceCriterion, PlanningArtifact, ProductRequest
from app.llm import GenerationMetadata, ModelUsage
from app.providers import LLMPlanningProvider
from app.service import EngineeringWorkflowService


class MemoryRepository:
    def __init__(self) -> None:
        self.run = None

    def save(self, run):
        self.run = run
        return run

    def get(self, run_id):
        return self.run if self.run and self.run.id == run_id else None


class RecordingLLM:
    name = "openai"
    model = "test-model"

    def __init__(self) -> None:
        self.last_generation = None

    def generate(self, *, system, prompt, schema):
        self.last_generation = GenerationMetadata(
            provider="openai",
            model="test-model",
            response_id="resp-123",
            usage=ModelUsage(input_tokens=120, output_tokens=80, total_tokens=200),
        )
        return PlanningArtifact(
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


def test_service_persists_planning_usage_metadata() -> None:
    repository = MemoryRepository()
    service = EngineeringWorkflowService(repository, Settings(llm_provider="mock"))
    service.planning_provider = LLMPlanningProvider(RecordingLLM())
    service.graph = __import__("app.graph", fromlist=["build_engineering_graph"]).build_engineering_graph(
        service.planning_provider,
        service.architecture_provider,
        service.engineering_provider,
        service.qa_provider,
        service.security_provider,
    )

    run = service.create_and_run(
        ProductRequest(request="Add churn forecasting to the SaaS mobile experience.")
    )

    assert run.planning_usage is not None
    assert run.planning_usage.response_id == "resp-123"
    assert run.planning_usage.total_tokens == 200
    assert any(
        event.agent == "planning" and event.action == "record_model_usage"
        for event in run.audit_events
    )
