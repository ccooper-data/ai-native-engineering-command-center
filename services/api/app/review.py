from .contracts import (
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
        engineering: EngineeringArtifact,
        qa: QAArtifact,
        security: SecurityArtifact,
    ) -> ReviewArtifact:
        addressed = set(engineering.acceptance_criteria_addressed)
        verified = set(qa.acceptance_criteria_verified)
        traceability: list[TraceabilityItem] = []
        findings: list[QualityFinding] = []

        for criterion in plan.acceptance_criteria:
            implementation = [change.path for change in engineering.files] if criterion.id in addressed else []
            verification = qa.tests_planned if criterion.id in verified else []
            covered = bool(implementation and verification)
            traceability.append(
                TraceabilityItem(
                    acceptance_criterion_id=criterion.id,
                    implementation_evidence=implementation,
                    verification_evidence=verification,
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
