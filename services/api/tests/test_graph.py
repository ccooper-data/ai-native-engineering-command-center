from app.contracts import AuditEvent, RunStatus
from app.graph import build_planning_graph
from app.providers import MockPlanningProvider


def test_langgraph_planning_node_produces_auditable_plan() -> None:
    graph = build_planning_graph(MockPlanningProvider())
    result = graph.invoke(
        {
            "original_request": "Add churn forecasting to the SaaS product and expose it in mobile.",
            "status": RunStatus.PLANNING,
            "planning": None,
            "audit_events": [
                AuditEvent(agent="system", action="workflow_created", status="success")
            ],
        }
    )

    assert result["status"] == RunStatus.PLANNED
    assert result["planning"] is not None
    assert result["planning"].acceptance_criteria[0].id == "AC-001"
    assert result["audit_events"][-1].agent == "planning"
    assert result["audit_events"][-1].status == "success"
