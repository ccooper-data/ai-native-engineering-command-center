from app.config import Settings
from app.providers import (
    LLMArchitectureProvider,
    LLMEngineeringProvider,
    LLMPlanningProvider,
    MockEngineeringProvider,
)
from app.service import EngineeringWorkflowService


class MemoryRepository:
    def __init__(self) -> None:
        self.run = None

    def save(self, run):
        self.run = run
        return run

    def get(self, run_id):
        return self.run if self.run and self.run.id == run_id else None


def settings(engineering_enabled: bool) -> Settings:
    return Settings(
        llm_provider="openai",
        openai_api_key="test-only",
        openai_model="gpt-5.6-terra",
        architecture_llm_enabled=True,
        engineering_llm_enabled=engineering_enabled,
    )


def test_engineering_remains_mock_unless_explicitly_enabled() -> None:
    service = EngineeringWorkflowService(MemoryRepository(), settings(False))
    assert isinstance(service.planning_provider, LLMPlanningProvider)
    assert isinstance(service.architecture_provider, LLMArchitectureProvider)
    assert isinstance(service.engineering_provider, MockEngineeringProvider)


def test_three_real_agents_share_exactly_one_run_budget() -> None:
    service = EngineeringWorkflowService(MemoryRepository(), settings(True))
    assert isinstance(service.engineering_provider, LLMEngineeringProvider)
    assert service.planning_provider.llm.run_budget is service.run_cost_budget
    assert service.architecture_provider.llm.run_budget is service.run_cost_budget
    assert service.engineering_provider.llm.run_budget is service.run_cost_budget
