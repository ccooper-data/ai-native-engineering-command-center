from unittest.mock import Mock

from pydantic import BaseModel

from app.config import Settings
from app.llm import OpenAIStructuredLLM


class Output(BaseModel):
    value: str


def test_openai_budget_gate_blocks_before_client_call() -> None:
    settings = Settings(
        llm_provider="openai",
        openai_api_key="test-only",
        openai_model="gpt-5.6-terra",
        llm_max_output_tokens=4096,
        llm_max_tokens_per_call=20000,
        llm_max_cost_per_call_usd=0.05,
        llm_max_cost_per_run_usd=0.25,
    )
    llm = OpenAIStructuredLLM("test-only", settings.openai_model, settings)
    llm.client = Mock()

    try:
        llm.generate(system="system", prompt="prompt", schema=Output)
        raise AssertionError("Expected cost policy to block the call")
    except RuntimeError as exc:
        assert "policy ceiling" in str(exc)

    llm.client.responses.parse.assert_not_called()
