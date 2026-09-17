import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from .contracts import (
    ArchitectureArtifact,
    AuditEvent,
    EngineeringArtifact,
    PlanningArtifact,
    QAArtifact,
    QualityGateArtifact,
    RunStatus,
    SecurityArtifact,
)
from .providers import ArchitectureProvider, EngineeringProvider, PlanningProvider
from .quality import QAProvider, SecurityProvider


class EngineeringGraphState(TypedDict):
    original_request: str
    status: RunStatus
    planning: PlanningArtifact | None
    architecture: ArchitectureArtifact | None
    engineering: EngineeringArtifact | None
    qa: QAArtifact | None
    security: SecurityArtifact | None
    quality_gate: QualityGateArtifact | None
    audit_events: Annotated[list[AuditEvent], operator.add]


def build_engineering_graph(
    planning_provider: PlanningProvider,
    architecture_provider: ArchitectureProvider,
    engineering_provider: EngineeringProvider,
    qa_provider: QAProvider,
    security_provider: SecurityProvider,
):
    def planning_node(state: EngineeringGraphState) -> dict:
        plan = planning_provider.plan(state["original_request"])
        return {"status": RunStatus.PLANNED, "planning": plan, "audit_events": [AuditEvent(agent="planning", action="create_plan", status="success")]}

    def architecture_node(state: EngineeringGraphState) -> dict:
        plan = state["planning"]
        if plan is None:
            raise ValueError("Architecture Agent requires a validated planning artifact")
        architecture = architecture_provider.design(state["original_request"], plan)
        return {"status": RunStatus.ARCHITECTED, "architecture": architecture, "audit_events": [AuditEvent(agent="architecture", action="create_architecture", status="success")]}

    def engineering_node(state: EngineeringGraphState) -> dict:
        plan, architecture = state["planning"], state["architecture"]
        if plan is None or architecture is None:
            raise ValueError("Engineering Agent requires planning and architecture artifacts")
        engineering = engineering_provider.implement(state["original_request"], plan, architecture)
        return {"status": RunStatus.IMPLEMENTED, "engineering": engineering, "audit_events": [AuditEvent(agent="engineering", action="propose_change_set", status="success")]}

    def qa_node(state: EngineeringGraphState) -> dict:
        plan, engineering = state["planning"], state["engineering"]
        if plan is None or engineering is None:
            raise ValueError("QA Agent requires planning and engineering artifacts")
        qa = qa_provider.validate(plan, engineering)
        return {"qa": qa, "audit_events": [AuditEvent(agent="qa", action="validate_change_set", status="success" if qa.passed else "failed")]}

    def security_node(state: EngineeringGraphState) -> dict:
        architecture, engineering = state["architecture"], state["engineering"]
        if architecture is None or engineering is None:
            raise ValueError("Security Agent requires architecture and engineering artifacts")
        security = security_provider.scan(architecture, engineering)
        return {"security": security, "audit_events": [AuditEvent(agent="security", action="scan_change_set", status="success" if security.passed else "failed")]}

    def quality_gate_node(state: EngineeringGraphState) -> dict:
        qa, security = state["qa"], state["security"]
        if qa is None or security is None:
            raise ValueError("Quality Gate requires both QA and Security results")
        blocking = [finding.id for finding in [*qa.findings, *security.findings] if finding.blocking]
        passed = qa.passed and security.passed and not blocking
        gate = QualityGateArtifact(passed=passed, blocking_findings=blocking, decision="continue_to_review" if passed else "return_to_engineering")
        return {"status": RunStatus.QUALITY_PASSED if passed else RunStatus.REMEDIATION_REQUIRED, "quality_gate": gate, "audit_events": [AuditEvent(agent="quality_gate", action="evaluate_independent_checks", status="success" if passed else "blocked")]}

    graph = StateGraph(EngineeringGraphState)
    graph.add_node("planning", planning_node)
    graph.add_node("architecture", architecture_node)
    graph.add_node("engineering", engineering_node)
    graph.add_node("qa", qa_node)
    graph.add_node("security", security_node)
    graph.add_node("quality_gate", quality_gate_node)
    graph.add_edge(START, "planning")
    graph.add_edge("planning", "architecture")
    graph.add_edge("architecture", "engineering")
    graph.add_edge("engineering", "qa")
    graph.add_edge("engineering", "security")
    graph.add_edge("qa", "quality_gate")
    graph.add_edge("security", "quality_gate")
    graph.add_edge("quality_gate", END)
    return graph.compile()
