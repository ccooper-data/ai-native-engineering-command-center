import pytest

from app.preflight import RunCostBudget, reserve_standard_text_cost


def test_three_terra_reservations_fit_default_quarter_dollar_run_budget() -> None:
    reservation = reserve_standard_text_cost(
        provider="openai",
        model="gpt-5.6-terra",
        max_input_tokens=15904,
        max_output_tokens=4096,
        max_call_cost_usd=0.10,
    )
    budget = RunCostBudget(max_run_cost_usd=0.25)

    assert reservation.reserved_usd == pytest.approx(0.08096)

    for _ in range(3):
        assert budget.can_reserve(reservation)
        budget.reserve(reservation)

    assert budget.reserved_usd == pytest.approx(0.24288)
    assert budget.remaining_usd == pytest.approx(0.00712)


def test_fourth_default_terra_reservation_is_blocked_before_call() -> None:
    reservation = reserve_standard_text_cost(
        provider="openai",
        model="gpt-5.6-terra",
        max_input_tokens=15904,
        max_output_tokens=4096,
        max_call_cost_usd=0.10,
    )
    budget = RunCostBudget(max_run_cost_usd=0.25)

    for _ in range(3):
        budget.reserve(reservation)

    assert budget.can_reserve(reservation) is False
