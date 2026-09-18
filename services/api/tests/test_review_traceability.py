from app.contracts import (
    AcceptanceCriterion,
    ArchitectureArtifact,
    ArchitectureDecision,
    EngineeringArtifact,
    PlanningArtifact,
    ProposedFileChange,
    QAArtifact,
    SecurityArtifact,
)
from app.review import DeterministicReviewer


def plan() -> PlanningArtifact:
    return PlanningArtifact(
        business_objective="prove governed traceability",
        scope=["bounded change"],
        assumptions=[],
        functional_requirements=["deterministic marker"],
        non_functional_requirements=[],
        acceptance_criteria=[AcceptanceCriterion(id="AC-001", statement="marker is implemented and verified")],
        dependencies=[],
        risks=[],
        implementation_tasks=["implement marker"],
    )


def architecture() -> ArchitectureArtifact:
    return ArchitectureArtifact(
        summary="bounded architecture",
        affected_components=["src"],
        data_flow=[],
        api_changes=[],
        data_changes=[],
        security_controls=["branch isolation"],
        observability_requirements=[],
        decisions=[ArchitectureDecision(id="ADR-001", title="isolated branch", decision="use agent branch", rationale="least privilege", consequences=[])],
        implementation_sequence=["implement marker"],
    )


def engineering(addressed: bool = True) -> EngineeringArtifact:
    return EngineeringArtifact(
        branch_name="agent/governed-mutation-proof",
        commit_message="feat: bounded mutation",
        summary="proposal",
        files=[ProposedFileChange(path="src/proof.py", operation="create", purpose="proof", content="PROOF = True\n")],
        acceptance_criteria_addressed=["AC-001"] if addressed else [],
        tests_required=["unit"],
        security_notes=["no secrets"],
    )


def qa(verified: bool = True) -> QAArtifact:
    return QAArtifact(
        passed=True,
        tests_planned=["pytest"],
        findings=[],
        acceptance_criteria_verified=["AC-001"] if verified else [],
    )


def security() -> SecurityArtifact:
    return SecurityArtifact(passed=True, scans_planned=["gitleaks", "semgrep"], findings=[], controls_verified=["branch isolation"])


def test_reviewer_builds_complete_traceability_chain() -> None:
    result = DeterministicReviewer().review(plan(), architecture(), engineering(), qa(), security())
    item = result.traceability[0]
    assert result.passed is True
    assert item.architecture_evidence == ["ADR-001"]
    assert item.implementation_evidence == ["src/proof.py"]
    assert item.verification_evidence == ["pytest"]
    assert item.reviewer_verification == ["independent-traceability-review"]
    assert item.covered is True


def test_reviewer_fails_closed_without_implementation_evidence() -> None:
    result = DeterministicReviewer().review(plan(), architecture(), engineering(addressed=False), qa(), security())
    assert result.passed is False
    assert result.recommendation == "return_to_engineering"
    assert result.traceability[0].covered is False
    assert any(finding.blocking for finding in result.findings)


def test_reviewer_fails_closed_without_verification_evidence() -> None:
    result = DeterministicReviewer().review(plan(), architecture(), engineering(), qa(verified=False), security())
    assert result.passed is False
    assert result.recommendation == "return_to_engineering"
    assert result.traceability[0].covered is False
    assert any(finding.blocking for finding in result.findings)
