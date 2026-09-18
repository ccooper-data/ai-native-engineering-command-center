from pydantic import BaseModel

from .contracts import EngineeringArtifact, ProposedFileChange
from .repository_tools import (
    IsolatedBranchRepositoryExecutor,
    RepositoryPolicyError,
    validate_change_set,
)


BENCHMARK_SPECIFICATION_VERSION = "repository-adversarial-v1"
BENCHMARK_SCENARIO_IDS = [
    "protected-main-branch",
    "protected-github-workflow",
    "path-traversal",
    "branch-substitution",
    "post-write-content-corruption",
]


class RepositoryFaultMetrics(BaseModel):
    faults_injected: int
    faults_detected: int
    faults_blocked: int
    detection_rate: float
    blocking_rate: float


class CorruptingClient:
    def __init__(self) -> None:
        self.files: dict[str, str] = {}

    def create_branch(self, branch_name: str) -> None:
        pass

    def create_file(self, branch_name: str, change: ProposedFileChange, message: str) -> None:
        self.files[change.path] = "CORRUPTED"

    def update_file(self, branch_name: str, change: ProposedFileChange, message: str) -> None:
        self.create_file(branch_name, change, message)

    def delete_file(self, branch_name: str, change: ProposedFileChange, message: str) -> None:
        self.files.pop(change.path, None)

    def read_file(self, branch_name: str, path: str) -> str | None:
        return self.files.get(path)

    def get_branch_commit_sha(self, branch_name: str) -> str:
        return "a" * 40


def _artifact(branch: str, path: str) -> EngineeringArtifact:
    return EngineeringArtifact(
        branch_name=branch,
        commit_message="test: adversarial repository scenario",
        summary="controlled fault injection",
        files=[ProposedFileChange(path=path, operation="create", purpose="fault injection", content="SAFE = True\n")],
        acceptance_criteria_addressed=["AC-FAULT"],
        tests_required=["policy"],
        security_notes=["non-production deterministic evaluation"],
    )


def evaluate_repository_faults() -> RepositoryFaultMetrics:
    scenarios = []

    for artifact in (
        _artifact("main", "src/safe.py"),
        _artifact("agent/fault", ".github/workflows/ci.yml"),
        _artifact("agent/fault", "../escape.py"),
    ):
        try:
            validate_change_set(artifact)
            scenarios.append(False)
        except RepositoryPolicyError:
            scenarios.append(True)

    try:
        IsolatedBranchRepositoryExecutor(CorruptingClient(), "agent/authorized").apply(
            _artifact("agent/substituted", "src/safe.py")
        )
        scenarios.append(False)
    except RepositoryPolicyError:
        scenarios.append(True)

    try:
        IsolatedBranchRepositoryExecutor(CorruptingClient(), "agent/authorized").apply(
            _artifact("agent/authorized", "src/safe.py")
        )
        scenarios.append(False)
    except RepositoryPolicyError:
        scenarios.append(True)

    detected = sum(scenarios)
    total = len(scenarios)
    return RepositoryFaultMetrics(
        faults_injected=total,
        faults_detected=detected,
        faults_blocked=detected,
        detection_rate=detected / total,
        blocking_rate=detected / total,
    )
