from .contracts import (
    ArchitectureArtifact,
    EngineeringArtifact,
    PlanningArtifact,
    QAArtifact,
    QualityFinding,
    ReviewArtifact,
    SecurityArtifact,
    TraceabilityItem,
)


class DeterministicReviewer:
    """Independent second-pass reviewer; does not modify code or approve deployment."""

    def review(
        self,
        plan: PlanningArtifact,
        architecture: ArchitectureArtifact,
        engineering: EngineeringArtifact,
        qa: QAArtifact,
        security: SecurityArtifact,
    ) -> ReviewArtifact:
        addressed = set(engineering.acceptance_criteria_addressed)
        verified = set(qa.acceptance_criteria_verified)
        traceability: list[TraceabilityItem] = []
        architecture_ids = {decision.id for decision in architecture.decisions}
        findings: list[QualityFinding] = []

        for criterion in plan.acceptance_criteria:
            implementation = [change.path for change in engineering.files] if criterion.id in addressed else []
            verification = qa.tests_planned if criterion.id in verified else []
            architecture_evidence = sorted(architecture_ids) if implementation else []
            reviewer_verification = ["independent-traceability-review"] if implementation and verification else []
            covered = bool(architecture_evidence and implementation and verification and reviewer_verification)
            traceability.append(
                TraceabilityItem(
                    acceptance_criterion_id=criterion.id,
                    architecture_evidence=architecture_evidence,
                    implementation_evidence=implementation,
                    verification_evidence=verification,
                    reviewer_verification=reviewer_verification,
                    covered=covered,
                )
            )
            if not covered:
                findings.append(
                    QualityFinding(
                        id=f"REV-TRACE-{criterion.id}",
                        severity="high",
                        category="traceability",
                        message=f"Acceptance criterion {criterion.id} lacks complete implementation/test evidence",
                        blocking=True,
                    )
                )

        findings.extend(finding for finding in security.findings if finding.blocking)
        passed = not any(finding.blocking for finding in findings) and qa.passed and security.passed
        return ReviewArtifact(
            passed=passed,
            summary="Independent review of acceptance-criteria traceability and quality evidence.",
            traceability=traceability,
            findings=findings,
            recommendation="request_human_approval" if passed else "return_to_engineering",
        )
