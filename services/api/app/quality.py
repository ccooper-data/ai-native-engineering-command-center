from abc import ABC, abstractmethod

from .contracts import (
    ArchitectureArtifact,
    EngineeringArtifact,
    PlanningArtifact,
    QAArtifact,
    QualityFinding,
    SecurityArtifact,
)


class QAProvider(ABC):
    @abstractmethod
    def validate(self, plan: PlanningArtifact, engineering: EngineeringArtifact) -> QAArtifact:
        raise NotImplementedError


class SecurityProvider(ABC):
    @abstractmethod
    def scan(
        self, architecture: ArchitectureArtifact, engineering: EngineeringArtifact
    ) -> SecurityArtifact:
        raise NotImplementedError


class MockQAProvider(QAProvider):
    def validate(self, plan: PlanningArtifact, engineering: EngineeringArtifact) -> QAArtifact:
        required_ids = {criterion.id for criterion in plan.acceptance_criteria}
        addressed = set(engineering.acceptance_criteria_addressed)
        missing = sorted(required_ids - addressed)
        findings = [
            QualityFinding(
                id=f"QA-MISSING-{criterion_id}",
                severity="high",
                category="acceptance-criteria",
                message=f"Engineering change set does not address {criterion_id}",
                blocking=True,
            )
            for criterion_id in missing
        ]
        return QAArtifact(
            passed=not findings,
            tests_planned=engineering.tests_required,
            findings=findings,
            acceptance_criteria_verified=sorted(required_ids & addressed),
        )


class MockSecurityProvider(SecurityProvider):
    def scan(
        self, architecture: ArchitectureArtifact, engineering: EngineeringArtifact
    ) -> SecurityArtifact:
        findings: list[QualityFinding] = []
        for change in engineering.files:
            content = (change.content or "").lower()
            if "api_key=" in content or "password=" in content or "secret=" in content:
                findings.append(
                    QualityFinding(
                        id="SEC-SECRET-001",
                        severity="critical",
                        category="secret-detection",
                        message=f"Potential hard-coded secret in {change.path}",
                        blocking=True,
                    )
                )
        return SecurityArtifact(
            passed=not findings,
            scans_planned=["Gitleaks secret scan", "Semgrep SAST", "Dependency scan", "Container scan"],
            findings=findings,
            controls_verified=architecture.security_controls,
        )
