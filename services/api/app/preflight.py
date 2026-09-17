from dataclasses import dataclass

from .pricing import MODEL_PRICES, UnknownModelPriceError


class CostPolicyError(RuntimeError):
    pass


@dataclass(frozen=True)
class CostReservation:
    provider: str
    model: str
    max_input_tokens: int
    max_output_tokens: int
    reserved_usd: float


def reserve_standard_text_cost(*, provider: str, model: str, max_input_tokens: int, max_output_tokens: int, max_call_cost_usd: float) -> CostReservation:
    price = MODEL_PRICES.get((provider, model))
    if price is None:
        raise UnknownModelPriceError(f"No approved price snapshot for provider={provider!r}, model={model!r}")
    reserved = (max_input_tokens / 1_000_000 * price.input_per_million_usd + max_output_tokens / 1_000_000 * price.output_per_million_usd)
    if reserved > max_call_cost_usd:
        raise CostPolicyError(f"Worst-case call cost ${reserved:.4f} exceeds policy ceiling ${max_call_cost_usd:.4f}")
    return CostReservation(provider=provider, model=model, max_input_tokens=max_input_tokens, max_output_tokens=max_output_tokens, reserved_usd=reserved)
