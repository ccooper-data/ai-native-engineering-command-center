from pydantic import BaseModel

from .capabilities import evaluate_post_approval_capability
from .contracts import WorkflowRun


class FaultInjectionResult(BaseModel):
    scenario: str
    detected: bool
    blocked: bool
    evidence: list[str]


def evaluate_fault_scenario(run: WorkflowRun, scenario: str) -> FaultInjectionResult:
    """Deterministic governance fault injection; never mutates external state."""
    if scenario == "stale_approval_sha":
        decision = evaluate_post_approval_capability(run, "f" * 40, "draft_pr")
        return FaultInjectionResult(
            scenario=scenario,
            detected=not decision.allowed,
            blocked=not decision.allowed,
            evidence=[decision.reason],
        )
    if scenario == "failed_ci":
        detected = run.ci_validation is not None and not run.ci_validation.passed
        return FaultInjectionResult(scenario=scenario, detected=detected, blocked=detected, evidence=["CI passed=false"] if detected else [])
    if scenario == "missing_ac_evidence":
        gaps = [item.acceptance_criterion_id for item in run.review.traceability if not item.covered] if run.review is not None else []
        return FaultInjectionResult(scenario=scenario, detected=bool(gaps), blocked=bool(gaps), evidence=gaps)
    if scenario == "excessive_cost":
        usages = [item for item in (run.planning_usage, run.architecture_usage, run.engineering_usage) if item is not None]
        cost = sum(item.estimated_actual_cost_usd or 0.0 for item in usages)
        detected = cost > 0.25
        return FaultInjectionResult(scenario=scenario, detected=detected, blocked=detected, evidence=[f"cost={cost:.4f}"])
    raise ValueError(f"Unknown fault-injection scenario: {scenario}")
