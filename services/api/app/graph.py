from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .contracts import AuditEvent, PlanningArtifact, RunStatus
from .providers import PlanningProvider


class PlanningGraphState(TypedDict):
    original_request: str
    status: RunStatus
    planning: PlanningArtifact | None
    audit_events: list[AuditEvent]


def build_planning_graph(provider: PlanningProvider):
    def planning_node(state: PlanningGraphState) -> PlanningGraphState:
        events = list(state["audit_events"])
        try:
            plan = provider.plan(state["original_request"])
            events.append(AuditEvent(agent="planning", action="create_plan", status="success"))
            return {
                **state,
                "status": RunStatus.PLANNED,
                "planning": plan,
                "audit_events": events,
            }
        except Exception:
            events.append(AuditEvent(agent="planning", action="create_plan", status="failed"))
            return {
                **state,
                "status": RunStatus.FAILED,
                "planning": None,
                "audit_events": events,
            }

    graph = StateGraph(PlanningGraphState)
    graph.add_node("planning", planning_node)
    graph.add_edge(START, "planning")
    graph.add_edge("planning", END)
    return graph.compile()
