import pytest

from app.config import Settings
from app.llm import build_structured_llm


def test_mock_provider_requires_no_api_key() -> None:
    settings = Settings(llm_provider="mock")
    assert build_structured_llm(settings) is None


def test_openai_provider_fails_closed_without_key() -> None:
    settings = Settings(llm_provider="openai", openai_api_key=None)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        build_structured_llm(settings)


def test_anthropic_provider_fails_closed_without_key() -> None:
    settings = Settings(llm_provider="anthropic", anthropic_api_key=None)
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        build_structured_llm(settings)


def test_unknown_provider_is_rejected() -> None:
    settings = Settings(llm_provider="untrusted-provider")
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        build_structured_llm(settings)
