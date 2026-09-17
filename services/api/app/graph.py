from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .contracts import ArchitectureArtifact, AuditEvent, PlanningArtifact, RunStatus
from .providers import ArchitectureProvider, PlanningProvider


class EngineeringGraphState(TypedDict):
    original_request: str
    status: RunStatus
    planning: PlanningArtifact | None
    architecture: ArchitectureArtifact | None
    audit_events: list[AuditEvent]


def build_engineering_graph(
    planning_provider: PlanningProvider,
    architecture_provider: ArchitectureProvider,
):
    def planning_node(state: EngineeringGraphState) -> EngineeringGraphState:
        events = list(state["audit_events"])
        plan = planning_provider.plan(state["original_request"])
        events.append(AuditEvent(agent="planning", action="create_plan", status="success"))
        return {
            **state,
            "status": RunStatus.PLANNED,
            "planning": plan,
            "audit_events": events,
        }

    def architecture_node(state: EngineeringGraphState) -> EngineeringGraphState:
        plan = state["planning"]
        if plan is None:
            raise ValueError("Architecture Agent requires a validated planning artifact")
        events = list(state["audit_events"])
        architecture = architecture_provider.design(state["original_request"], plan)
        events.append(
            AuditEvent(agent="architecture", action="create_architecture", status="success")
        )
        return {
            **state,
            "status": RunStatus.ARCHITECTED,
            "architecture": architecture,
            "audit_events": events,
        }

    graph = StateGraph(EngineeringGraphState)
    graph.add_node("planning", planning_node)
    graph.add_node("architecture", architecture_node)
    graph.add_edge(START, "planning")
    graph.add_edge("planning", "architecture")
    graph.add_edge("architecture", END)
    return graph.compile()
