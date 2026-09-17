import pytest

from app.config import Settings
from app.providers import LLMPlanningProvider, MockPlanningProvider
from app.service import build_planning_provider


def test_mock_runtime_selects_deterministic_planner() -> None:
    provider = build_planning_provider(Settings(llm_provider="mock"))
    assert isinstance(provider, MockPlanningProvider)


def test_openai_runtime_selects_llm_planner_without_calling_api() -> None:
    provider = build_planning_provider(
        Settings(
            llm_provider="openai",
            openai_api_key="test-only-not-a-real-key",
            openai_model="test-openai-model",
        )
    )
    assert isinstance(provider, LLMPlanningProvider)
    assert provider.name == "openai"
    assert provider.model == "test-openai-model"


def test_anthropic_runtime_selects_llm_planner_without_calling_api() -> None:
    provider = build_planning_provider(
        Settings(
            llm_provider="anthropic",
            anthropic_api_key="test-only-not-a-real-key",
            anthropic_model="test-anthropic-model",
        )
    )
    assert isinstance(provider, LLMPlanningProvider)
    assert provider.name == "anthropic"
    assert provider.model == "test-anthropic-model"


def test_real_runtime_without_credential_fails_closed() -> None:
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        build_planning_provider(Settings(llm_provider="openai", openai_api_key=None))
