import pytest

from app.budget import BudgetExceededError, TokenBudget
from app.llm import GenerationMetadata, ModelUsage


def generation(total: int) -> GenerationMetadata:
    return GenerationMetadata(
        provider="test",
        model="test",
        usage=ModelUsage(total_tokens=total),
    )


def test_budget_records_usage_below_both_limits() -> None:
    budget = TokenBudget(max_tokens_per_call=1000, max_tokens_per_run=1500)
    budget.record(generation(600))
    budget.record(generation(700))
    assert budget.consumed_tokens == 1300


def test_budget_blocks_oversized_single_call() -> None:
    budget = TokenBudget(max_tokens_per_call=1000, max_tokens_per_run=5000)
    with pytest.raises(BudgetExceededError, match="per-call ceiling"):
        budget.record(generation(1001))


def test_budget_blocks_cumulative_run_overage() -> None:
    budget = TokenBudget(max_tokens_per_call=1000, max_tokens_per_run=1500)
    budget.record(generation(900))
    with pytest.raises(BudgetExceededError, match="run ceiling"):
        budget.record(generation(700))
    assert budget.consumed_tokens == 900
