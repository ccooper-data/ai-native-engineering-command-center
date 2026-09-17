import json
from abc import ABC, abstractmethod
from typing import TypeVar

import anthropic
import openai
from pydantic import BaseModel

from app.config import Settings

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


class StructuredLLM(ABC):
    name: str
    model: str
    last_generation: GenerationMetadata | None = None

    @abstractmethod
    def generate(self, *, system: str, prompt: str, schema: type[T]) -> T:
        raise NotImplementedError


class OpenAIStructuredLLM(StructuredLLM):
    name = "openai"

    def __init__(self, api_key: str, model: str) -> None:
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.last_generation = None

    def generate(self, *, system: str, prompt: str, schema: type[T]) -> T:
        response = self.client.responses.parse(
            model=self.model,
            instructions=system,
            input=prompt,
            text_format=schema,
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
        )
        return response.output_parsed


class AnthropicStructuredLLM(StructuredLLM):
    name = "anthropic"

    def __init__(self, api_key: str, model: str) -> None:
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.last_generation = None

    def generate(self, *, system: str, prompt: str, schema: type[T]) -> T:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=8192,
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


def build_structured_llm(settings: Settings) -> StructuredLLM | None:
    provider = settings.llm_provider.lower()
    if provider == "mock":
        return None
    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("COMMAND_CENTER_OPENAI_API_KEY is required for the OpenAI provider")
        return OpenAIStructuredLLM(settings.openai_api_key, settings.openai_model)
    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("COMMAND_CENTER_ANTHROPIC_API_KEY is required for the Anthropic provider")
        return AnthropicStructuredLLM(settings.anthropic_api_key, settings.anthropic_model)
    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")
