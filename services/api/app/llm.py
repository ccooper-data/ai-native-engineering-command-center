import json
from abc import ABC, abstractmethod
from typing import TypeVar

import anthropic
import openai
from pydantic import BaseModel

from app.config import Settings
from app.preflight import RunCostBudget, reserve_standard_text_cost

T = TypeVar("T", bound=BaseModel)


class ModelUsage(BaseModel):
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class GenerationMetadata(BaseModel):
    provider: str
    model: str
    response_id: str | None = None
    usage: ModelUsage = ModelUsage()
    reserved_cost_usd: float = 0.0


class StructuredLLM(ABC):
    name: str
    model: str
    last_generation: GenerationMetadata | None = None

    @abstractmethod
    def generate(self, *, system: str, prompt: str, schema: type[T]) -> T:
        raise NotImplementedError


class OpenAIStructuredLLM(StructuredLLM):
    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str,
        settings: Settings,
        run_budget: RunCostBudget | None = None,
    ) -> None:
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.settings = settings
        self.run_budget = run_budget or RunCostBudget(
            max_run_cost_usd=settings.llm_max_cost_per_run_usd
        )
        self.last_generation = None

    def generate(self, *, system: str, prompt: str, schema: type[T]) -> T:
        reservation = reserve_standard_text_cost(
            provider=self.name,
            model=self.model,
            max_input_tokens=self.settings.llm_max_tokens_per_call - self.settings.llm_max_output_tokens,
            max_output_tokens=self.settings.llm_max_output_tokens,
            max_call_cost_usd=self.settings.llm_max_cost_per_call_usd,
        )
        self.run_budget.reserve(reservation)
        response = self.client.responses.parse(
            model=self.model,
            instructions=system,
            input=prompt,
            text_format=schema,
            max_output_tokens=self.settings.llm_max_output_tokens,
        )
        if response.output_parsed is None:
            raise RuntimeError("OpenAI returned no structured output")
        usage = response.usage
        self.last_generation = GenerationMetadata(
            provider=self.name,
            model=self.model,
            response_id=response.id,
            usage=ModelUsage(
                input_tokens=getattr(usage, "input_tokens", 0) or 0,
                output_tokens=getattr(usage, "output_tokens", 0) or 0,
                total_tokens=getattr(usage, "total_tokens", 0) or 0,
            ),
            reserved_cost_usd=reservation.reserved_usd,
        )
        return response.output_parsed


class AnthropicStructuredLLM(StructuredLLM):
    name = "anthropic"

    def __init__(self, api_key: str, model: str, settings: Settings) -> None:
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.settings = settings
        self.last_generation = None

    def generate(self, *, system: str, prompt: str, schema: type[T]) -> T:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=self.settings.llm_max_output_tokens,
            system=system,
            messages=[{"role": "user", "content": prompt}],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": schema.model_json_schema(),
                }
            },
        )
        text = "".join(block.text for block in message.content if block.type == "text")
        self.last_generation = GenerationMetadata(
            provider=self.name,
            model=self.model,
            response_id=message.id,
            usage=ModelUsage(
                input_tokens=message.usage.input_tokens,
                output_tokens=message.usage.output_tokens,
                total_tokens=message.usage.input_tokens + message.usage.output_tokens,
            ),
        )
        return schema.model_validate(json.loads(text))


def build_structured_llm(
    settings: Settings,
    run_budget: RunCostBudget | None = None,
) -> StructuredLLM | None:
    provider = settings.llm_provider.lower()
    if provider == "mock":
        return None
    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("COMMAND_CENTER_OPENAI_API_KEY is required for the OpenAI provider")
        return OpenAIStructuredLLM(
            settings.openai_api_key, settings.openai_model, settings, run_budget
        )
    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("COMMAND_CENTER_ANTHROPIC_API_KEY is required for the Anthropic provider")
        return AnthropicStructuredLLM(settings.anthropic_api_key, settings.anthropic_model, settings)
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
