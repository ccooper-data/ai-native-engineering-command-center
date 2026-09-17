import pytest

from app.preflight import CostPolicyError, RunCostBudget, reserve_standard_text_cost


def reservation(cost_limit: float = 0.10):
    return reserve_standard_text_cost(provider="openai", model="gpt-5.6-terra", max_input_tokens=4000, max_output_tokens=4096, max_call_cost_usd=cost_limit)


def test_run_budget_reserves_multiple_agent_calls() -> None:
    budget = RunCostBudget(max_run_cost_usd=0.15)
    budget.reserve(reservation())
    budget.reserve(reservation())
    assert budget.reserved_usd == pytest.approx(0.114304)
    assert budget.remaining_usd == pytest.approx(0.035696)


def test_run_budget_blocks_downstream_agent_before_api_call() -> None:
    budget = RunCostBudget(max_run_cost_usd=0.10)
    budget.reserve(reservation())
    with pytest.raises(CostPolicyError, match="run ceiling"):
        budget.reserve(reservation())
    assert budget.reserved_usd == pytest.approx(0.057152)
