from dataclasses import dataclass

from .llm import ModelUsage


@dataclass(frozen=True)
class ModelPrice:
    input_per_million_usd: float
    output_per_million_usd: float


PRICE_TABLE_VERSION = "2026-09-17"
MODEL_PRICES: dict[tuple[str, str], ModelPrice] = {
    ("openai", "gpt-5.6-terra"): ModelPrice(2.00, 12.00),
    ("openai", "gpt-5.6-luna"): ModelPrice(0.20, 1.20),
    ("openai", "gpt-5.6-sol"): ModelPrice(4.00, 20.00),
}


class UnknownModelPriceError(ValueError):
    pass


def estimate_standard_text_cost_usd(provider: str, model: str, usage: ModelUsage) -> float:
    price = MODEL_PRICES.get((provider, model))
    if price is None:
        raise UnknownModelPriceError(f"No approved price snapshot for provider={provider!r}, model={model!r}")
    input_cost = usage.input_tokens / 1_000_000 * price.input_per_million_usd
    output_cost = usage.output_tokens / 1_000_000 * price.output_per_million_usd
    return input_cost + output_cost
