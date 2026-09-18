from .contracts import GovernanceEvidence, WorkflowRun


def build_governance_evidence(run: WorkflowRun) -> GovernanceEvidence:
    usages = [
        item
        for item in (run.planning_usage, run.architecture_usage, run.engineering_usage)
        if item is not None
    ]
    commit_sha = run.ci_validation.commit_sha if run.ci_validation is not None else None
    ci_runs = [run.ci_validation.run_id] if run.ci_validation is not None else []
    remediation_cycles = sum(
        1
        for event in run.audit_events
        if event.status in {"failed", "blocked"} or event.action.startswith("remediation")
    )
    return GovernanceEvidence(
        current_commit_sha=commit_sha,
        repository_branch=run.engineering.branch_name if run.engineering is not None else None,
        ci_run_ids=ci_runs,
        remediation_cycles=remediation_cycles,
        total_tokens=sum(item.total_tokens for item in usages),
        estimated_actual_cost_usd=sum(
            item.estimated_actual_cost_usd or 0.0 for item in usages
        ),
    )


def refresh_governance_evidence(run: WorkflowRun) -> WorkflowRun:
    run.governance_evidence = build_governance_evidence(run)
    return run
