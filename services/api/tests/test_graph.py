from app.contracts import AuditEvent, RunStatus
from app.graph import build_engineering_graph
from app.providers import MockArchitectureProvider, MockEngineeringProvider, MockPlanningProvider
from app.quality import MockQAProvider, MockSecurityProvider


def test_parallel_quality_checks_join_at_gate() -> None:
    graph = build_engineering_graph(
        MockPlanningProvider(), MockArchitectureProvider(), MockEngineeringProvider(),
        MockQAProvider(), MockSecurityProvider(),
    )
    result = graph.invoke({
        "original_request": "Add churn forecasting to the SaaS product and expose it in mobile.",
        "status": RunStatus.PLANNING,
        "planning": None, "architecture": None, "engineering": None,
        "qa": None, "security": None, "quality_gate": None,
        "audit_events": [AuditEvent(agent="system", action="workflow_created", status="success")],
    })
    assert result["status"] == RunStatus.QUALITY_PASSED
    assert result["qa"].passed is True
    assert result["security"].passed is True
    assert result["quality_gate"].decision == "continue_to_review"
    agents = [event.agent for event in result["audit_events"]]
    assert agents[:4] == ["system", "planning", "architecture", "engineering"]
    assert set(agents[4:6]) == {"qa", "security"}
    assert agents[-1] == "quality_gate"
