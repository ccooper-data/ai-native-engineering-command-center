import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from .contracts import (
    ArchitectureArtifact, AuditEvent, EngineeringArtifact, PlanningArtifact, QAArtifact,
    QualityGateArtifact, ReviewArtifact, RunStatus, SecurityArtifact,
)
from .providers import ArchitectureProvider, EngineeringProvider, PlanningProvider
from .quality import QAProvider, SecurityProvider
from .review import DeterministicReviewer


class EngineeringGraphState(TypedDict):
    original_request: str
    status: RunStatus
    planning: PlanningArtifact | None
    architecture: ArchitectureArtifact | None
    engineering: EngineeringArtifact | None
    qa: QAArtifact | None
    security: SecurityArtifact | None
    quality_gate: QualityGateArtifact | None
    review: ReviewArtifact | None
    audit_events: Annotated[list[AuditEvent], operator.add]


def build_engineering_graph(planning_provider: PlanningProvider, architecture_provider: ArchitectureProvider, engineering_provider: EngineeringProvider, qa_provider: QAProvider, security_provider: SecurityProvider):
    reviewer = DeterministicReviewer()

    def planning_node(state: EngineeringGraphState) -> dict:
        plan = planning_provider.plan(state["original_request"])
        return {"status": RunStatus.PLANNED, "planning": plan, "audit_events": [AuditEvent(agent="planning", action="create_plan", status="success")]}

    def architecture_node(state: EngineeringGraphState) -> dict:
        plan = state["planning"]
        if plan is None: raise ValueError("Architecture requires planning")
        artifact = architecture_provider.design(state["original_request"], plan)
        return {"status": RunStatus.ARCHITECTED, "architecture": artifact, "audit_events": [AuditEvent(agent="architecture", action="create_architecture", status="success")]}

    def engineering_node(state: EngineeringGraphState) -> dict:
        plan, architecture = state["planning"], state["architecture"]
        if plan is None or architecture is None: raise ValueError("Engineering requires upstream artifacts")
        artifact = engineering_provider.implement(state["original_request"], plan, architecture)
        return {"status": RunStatus.IMPLEMENTED, "engineering": artifact, "audit_events": [AuditEvent(agent="engineering", action="propose_change_set", status="success")]}

    def qa_node(state: EngineeringGraphState) -> dict:
        if state["planning"] is None or state["engineering"] is None: raise ValueError("QA requires artifacts")
        qa = qa_provider.validate(state["planning"], state["engineering"])
        return {"qa": qa, "audit_events": [AuditEvent(agent="qa", action="validate_change_set", status="success" if qa.passed else "failed")]}

    def security_node(state: EngineeringGraphState) -> dict:
        if state["architecture"] is None or state["engineering"] is None: raise ValueError("Security requires artifacts")
        security = security_provider.scan(state["architecture"], state["engineering"])
        return {"security": security, "audit_events": [AuditEvent(agent="security", action="scan_change_set", status="success" if security.passed else "failed")]}

    def quality_gate_node(state: EngineeringGraphState) -> dict:
        qa, security = state["qa"], state["security"]
        if qa is None or security is None: raise ValueError("Quality Gate requires both checks")
        blocking = [x.id for x in [*qa.findings, *security.findings] if x.blocking]
        passed = qa.passed and security.passed and not blocking
        gate = QualityGateArtifact(passed=passed, blocking_findings=blocking, decision="continue_to_review" if passed else "return_to_engineering")
        return {"status": RunStatus.QUALITY_PASSED if passed else RunStatus.REMEDIATION_REQUIRED, "quality_gate": gate, "audit_events": [AuditEvent(agent="quality_gate", action="evaluate_independent_checks", status="success" if passed else "blocked")]}

    def route_quality(state: EngineeringGraphState) -> str:
        return "review" if state["quality_gate"] and state["quality_gate"].passed else "end"

    def review_node(state: EngineeringGraphState) -> dict:
        plan, engineering, qa, security = state["planning"], state["engineering"], state["qa"], state["security"]
        if plan is None or engineering is None or qa is None or security is None: raise ValueError("Reviewer requires complete evidence")
        review = reviewer.review(plan, engineering, qa, security)
        status = RunStatus.AWAITING_APPROVAL if review.passed else RunStatus.REMEDIATION_REQUIRED
        return {"status": status, "review": review, "audit_events": [AuditEvent(agent="reviewer", action="review_traceability", status="success" if review.passed else "blocked")]}

    graph = StateGraph(EngineeringGraphState)
    for name, node in [("planning", planning_node), ("architecture", architecture_node), ("engineering", engineering_node), ("qa", qa_node), ("security", security_node), ("quality_gate", quality_gate_node), ("review", review_node)]: graph.add_node(name, node)
    graph.add_edge(START, "planning"); graph.add_edge("planning", "architecture"); graph.add_edge("architecture", "engineering")
    graph.add_edge("engineering", "qa"); graph.add_edge("engineering", "security"); graph.add_edge("qa", "quality_gate"); graph.add_edge("security", "quality_gate")
    graph.add_conditional_edges("quality_gate", route_quality, {"review": "review", "end": END}); graph.add_edge("review", END)
    return graph.compile()
