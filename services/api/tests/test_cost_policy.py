import pytest

from app.llm import ModelUsage
from app.preflight import CostPolicyError, reserve_standard_text_cost
from app.pricing import UnknownModelPriceError, estimate_standard_text_cost_usd


def test_terra_cost_uses_versioned_standard_pricing() -> None:
    cost = estimate_standard_text_cost_usd("openai", "gpt-5.6-terra", ModelUsage(input_tokens=1000, output_tokens=2000, total_tokens=3000))
    assert cost == pytest.approx(0.026)


def test_preflight_reserves_worst_case_before_call() -> None:
    reservation = reserve_standard_text_cost(provider="openai", model="gpt-5.6-terra", max_input_tokens=4000, max_output_tokens=4096, max_call_cost_usd=0.10)
    assert reservation.reserved_usd == pytest.approx(0.057152)


def test_preflight_blocks_call_above_dollar_ceiling() -> None:
    with pytest.raises(CostPolicyError, match="exceeds policy ceiling"):
        reserve_standard_text_cost(provider="openai", model="gpt-5.6-terra", max_input_tokens=20000, max_output_tokens=4096, max_call_cost_usd=0.05)


def test_unknown_model_price_fails_closed() -> None:
    with pytest.raises(UnknownModelPriceError):
        reserve_standard_text_cost(provider="unknown", model="unknown", max_input_tokens=100, max_output_tokens=100, max_call_cost_usd=1.0)
