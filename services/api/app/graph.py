from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .contracts import (
    ArchitectureArtifact,
    AuditEvent,
    EngineeringArtifact,
    PlanningArtifact,
    RunStatus,
)
from .providers import ArchitectureProvider, EngineeringProvider, PlanningProvider


class EngineeringGraphState(TypedDict):
    original_request: str
    status: RunStatus
    planning: PlanningArtifact | None
    architecture: ArchitectureArtifact | None
    engineering: EngineeringArtifact | None
    audit_events: list[AuditEvent]


def build_engineering_graph(
    planning_provider: PlanningProvider,
    architecture_provider: ArchitectureProvider,
    engineering_provider: EngineeringProvider,
):
    def planning_node(state: EngineeringGraphState) -> EngineeringGraphState:
        events = list(state["audit_events"])
        plan = planning_provider.plan(state["original_request"])
        events.append(AuditEvent(agent="planning", action="create_plan", status="success"))
        return {**state, "status": RunStatus.PLANNED, "planning": plan, "audit_events": events}

    def architecture_node(state: EngineeringGraphState) -> EngineeringGraphState:
        plan = state["planning"]
        if plan is None:
            raise ValueError("Architecture Agent requires a validated planning artifact")
        events = list(state["audit_events"])
        architecture = architecture_provider.design(state["original_request"], plan)
        events.append(AuditEvent(agent="architecture", action="create_architecture", status="success"))
        return {**state, "status": RunStatus.ARCHITECTED, "architecture": architecture, "audit_events": events}

    def engineering_node(state: EngineeringGraphState) -> EngineeringGraphState:
        plan = state["planning"]
        architecture = state["architecture"]
        if plan is None or architecture is None:
            raise ValueError("Engineering Agent requires validated planning and architecture artifacts")
        events = list(state["audit_events"])
        engineering = engineering_provider.implement(state["original_request"], plan, architecture)
        events.append(AuditEvent(agent="engineering", action="propose_change_set", status="success"))
        return {**state, "status": RunStatus.IMPLEMENTED, "engineering": engineering, "audit_events": events}

    graph = StateGraph(EngineeringGraphState)
    graph.add_node("planning", planning_node)
    graph.add_node("architecture", architecture_node)
    graph.add_node("engineering", engineering_node)
    graph.add_edge(START, "planning")
    graph.add_edge("planning", "architecture")
    graph.add_edge("architecture", "engineering")
    graph.add_edge("engineering", END)
    return graph.compile()
