import json
from abc import ABC, abstractmethod
from typing import TypeVar

import anthropic
import openai
from pydantic import BaseModel
from app.config import Settings

T = TypeVar("T", bound=BaseModel)


class StructuredLLM(ABC):
    name: str
    model: str

    @abstractmethod
    def generate(self, *, system: str, prompt: str, schema: type[T]) -> T:
        raise NotImplementedError


class OpenAIStructuredLLM(StructuredLLM):
    name = "openai"

    def __init__(self, api_key: str, model: str) -> None:
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

    def generate(self, *, system: str, prompt: str, schema: type[T]) -> T:
        response = self.client.responses.parse(
            model=self.model,
            instructions=system,
            input=prompt,
            text_format=schema,
        )
        if response.output_parsed is None:
            raise RuntimeError("OpenAI returned no structured output")
        return response.output_parsed


class AnthropicStructuredLLM(StructuredLLM):
    name = "anthropic"

    def __init__(self, api_key: str, model: str) -> None:
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

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
