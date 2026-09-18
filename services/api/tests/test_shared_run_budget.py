from app.config import Settings
from app.llm import build_structured_llm
from app.preflight import RunCostBudget


def test_multiple_openai_agents_share_same_run_budget_ledger() -> None:
    settings = Settings(
        llm_provider="openai",
        openai_api_key="test-only",
        openai_model="gpt-5.6-terra",
        llm_max_cost_per_run_usd=0.25,
    )
    ledger = RunCostBudget(max_run_cost_usd=settings.llm_max_cost_per_run_usd)

    planning_llm = build_structured_llm(settings, ledger)
    architecture_llm = build_structured_llm(settings, ledger)

    assert planning_llm is not None
    assert architecture_llm is not None
    assert planning_llm.run_budget is ledger
    assert architecture_llm.run_budget is ledger
