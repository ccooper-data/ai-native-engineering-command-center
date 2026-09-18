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


@dataclass
class RunCostBudget:
    max_run_cost_usd: float
    reserved_usd: float = 0.0

    @property
    def remaining_usd(self) -> float:
        return max(0.0, self.max_run_cost_usd - self.reserved_usd)

    def can_reserve(self, reservation: CostReservation) -> bool:
        return self.reserved_usd + reservation.reserved_usd <= self.max_run_cost_usd

    def reserve(self, reservation: CostReservation) -> None:
        projected = self.reserved_usd + reservation.reserved_usd
        if projected > self.max_run_cost_usd:
            raise CostPolicyError(f"Run reservation would reach ${projected:.4f}; run ceiling is ${self.max_run_cost_usd:.4f}")
        self.reserved_usd = projected


def reserve_standard_text_cost(*, provider: str, model: str, max_input_tokens: int, max_output_tokens: int, max_call_cost_usd: float) -> CostReservation:
    price = MODEL_PRICES.get((provider, model))
    if price is None:
        raise UnknownModelPriceError(f"No approved price snapshot for provider={provider!r}, model={model!r}")
    reserved = (max_input_tokens / 1_000_000 * price.input_per_million_usd + max_output_tokens / 1_000_000 * price.output_per_million_usd)
    if reserved > max_call_cost_usd:
        raise CostPolicyError(f"Worst-case call cost ${reserved:.4f} exceeds policy ceiling ${max_call_cost_usd:.4f}")
    return CostReservation(provider=provider, model=model, max_input_tokens=max_input_tokens, max_output_tokens=max_output_tokens, reserved_usd=reserved)
