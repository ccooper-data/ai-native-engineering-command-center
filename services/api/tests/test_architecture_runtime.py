from app.config import Settings
from app.providers import LLMArchitectureProvider, LLMPlanningProvider, MockArchitectureProvider
from app.service import EngineeringWorkflowService


class MemoryRepository:
    def __init__(self) -> None:
        self.run = None

    def save(self, run):
        self.run = run
        return run

    def get(self, run_id):
        return self.run if self.run and self.run.id == run_id else None


def settings(architecture_enabled: bool) -> Settings:
    return Settings(
        llm_provider="openai",
        openai_api_key="test-only",
        openai_model="gpt-5.6-terra",
        architecture_llm_enabled=architecture_enabled,
    )


def test_architecture_remains_mock_unless_explicitly_enabled() -> None:
    service = EngineeringWorkflowService(MemoryRepository(), settings(False))
    assert isinstance(service.planning_provider, LLMPlanningProvider)
    assert isinstance(service.architecture_provider, MockArchitectureProvider)


def test_real_planning_and_architecture_share_one_budget() -> None:
    service = EngineeringWorkflowService(MemoryRepository(), settings(True))
    assert isinstance(service.planning_provider, LLMPlanningProvider)
    assert isinstance(service.architecture_provider, LLMArchitectureProvider)
    assert service.planning_provider.llm.run_budget is service.run_cost_budget
    assert service.architecture_provider.llm.run_budget is service.run_cost_budget
