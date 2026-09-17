from app.contracts import AuditEvent, RunStatus
from app.graph import build_engineering_graph
from app.providers import MockArchitectureProvider, MockPlanningProvider


def test_langgraph_hands_validated_plan_to_architecture_agent() -> None:
    graph = build_engineering_graph(MockPlanningProvider(), MockArchitectureProvider())
    result = graph.invoke(
        {
            "original_request": "Add churn forecasting to the SaaS product and expose it in mobile.",
            "status": RunStatus.PLANNING,
            "planning": None,
            "architecture": None,
            "audit_events": [
                AuditEvent(agent="system", action="workflow_created", status="success")
            ],
        }
    )

    assert result["status"] == RunStatus.ARCHITECTED
    assert result["planning"] is not None
    assert result["planning"].acceptance_criteria[0].id == "AC-001"
    assert result["architecture"] is not None
    assert result["architecture"].decisions[0].id == "ADR-AGENT-001"
    assert [event.agent for event in result["audit_events"]] == [
        "system",
        "planning",
        "architecture",
    ]
