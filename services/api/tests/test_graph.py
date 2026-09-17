from app.contracts import AuditEvent, RunStatus
from app.graph import build_engineering_graph
from app.providers import MockArchitectureProvider, MockEngineeringProvider, MockPlanningProvider


def test_langgraph_hands_artifacts_through_three_bounded_agents() -> None:
    graph = build_engineering_graph(
        MockPlanningProvider(), MockArchitectureProvider(), MockEngineeringProvider()
    )
    result = graph.invoke(
        {
            "original_request": "Add churn forecasting to the SaaS product and expose it in mobile.",
            "status": RunStatus.PLANNING,
            "planning": None,
            "architecture": None,
            "engineering": None,
            "audit_events": [AuditEvent(agent="system", action="workflow_created", status="success")],
        }
    )

    assert result["status"] == RunStatus.IMPLEMENTED
    assert result["planning"].acceptance_criteria[0].id == "AC-001"
    assert result["architecture"].decisions[0].id == "ADR-AGENT-001"
    assert result["engineering"].files[0].operation == "create"
    assert result["engineering"].acceptance_criteria_addressed == ["AC-001", "AC-002", "AC-003"]
    assert [event.agent for event in result["audit_events"]] == [
        "system",
        "planning",
        "architecture",
        "engineering",
    ]
