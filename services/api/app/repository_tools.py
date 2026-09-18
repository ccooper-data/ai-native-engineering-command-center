from abc import ABC, abstractmethod
from pathlib import PurePosixPath
from typing import Protocol

from pydantic import BaseModel

from .contracts import EngineeringArtifact, ProposedFileChange
from .source_preflight import validate_source_preflight


class RepositoryPolicyError(ValueError):
    pass


class RepositoryExecutionResult(BaseModel):
    branch_name: str
    applied_paths: list[str]
    commit_message: str
    dry_run: bool
    verification_performed: bool = False
    verified_paths: list[str] = []
    commit_sha: str | None = None


class RepositoryExecutor(ABC):
    @abstractmethod
    def apply(self, artifact: EngineeringArtifact) -> RepositoryExecutionResult:
        raise NotImplementedError


class RepositoryMutationClient(Protocol):
    """Narrow capability interface implemented by the GitHub adapter at runtime."""

    def create_branch(self, branch_name: str) -> None: ...

    def create_file(self, branch_name: str, change: ProposedFileChange, message: str) -> None: ...

    def update_file(self, branch_name: str, change: ProposedFileChange, message: str) -> None: ...

    def delete_file(self, branch_name: str, change: ProposedFileChange, message: str) -> None: ...

    def read_file(self, branch_name: str, path: str) -> str | None: ...

    def get_branch_commit_sha(self, branch_name: str) -> str: ...


def validate_change_set(artifact: EngineeringArtifact) -> None:
    if len(artifact.files) > 6:
        raise RepositoryPolicyError("Engineering change set exceeds six-file limit")
    if not artifact.branch_name.startswith("agent/"):
        raise RepositoryPolicyError("Agent branches must use the agent/ namespace")
    if artifact.branch_name in {"agent/main", "agent/master"}:
        raise RepositoryPolicyError("Protected branch alias")
    if not artifact.files:
        raise RepositoryPolicyError("Engineering change set must contain at least one file")

    protected = {".github/workflows/ci.yml", ".gitignore"}
    seen: set[str] = set()
    for change in artifact.files:
        path = PurePosixPath(change.path)
        normalized = str(path)
        if path.is_absolute() or ".." in path.parts:
            raise RepositoryPolicyError(f"Unsafe repository path: {change.path}")
        if normalized in protected or normalized.startswith(".github/"):
            raise RepositoryPolicyError(f"Protected repository path: {change.path}")
        if normalized in seen:
            raise RepositoryPolicyError(f"Duplicate repository path: {change.path}")
        if change.operation in {"create", "update"} and change.content is None:
            raise RepositoryPolicyError(f"Content required for {change.operation}: {change.path}")
        if change.content is not None and len(change.content.encode("utf-8")) > 100_000:
            raise RepositoryPolicyError(f"Generated file exceeds 100 KB limit: {change.path}")
        seen.add(normalized)


class DryRunRepositoryExecutor(RepositoryExecutor):
    """Policy-enforcing executor with zero repository mutation authority."""

    def apply(self, artifact: EngineeringArtifact) -> RepositoryExecutionResult:
        validate_change_set(artifact)
        return RepositoryExecutionResult(
            branch_name=artifact.branch_name,
            applied_paths=[change.path for change in artifact.files],
            commit_message=artifact.commit_message,
            dry_run=True,
        )


class BranchOnlyRepositoryExecutor(RepositoryExecutor):
    """Creates only an isolated agent branch; never writes files or opens/merges PRs."""

    def __init__(self, client: RepositoryMutationClient) -> None:
        self.client = client

    def apply(self, artifact: EngineeringArtifact) -> RepositoryExecutionResult:
        validate_change_set(artifact)
        self.client.create_branch(artifact.branch_name)
        return RepositoryExecutionResult(
            branch_name=artifact.branch_name,
            applied_paths=[],
            commit_message=artifact.commit_message,
            dry_run=False,
        )


class IsolatedBranchRepositoryExecutor(RepositoryExecutor):
    """Applies validated changes only to a pre-authorized isolated agent branch."""

    def __init__(self, client: RepositoryMutationClient, authorized_branch: str) -> None:
        if not authorized_branch.startswith("agent/"):
            raise RepositoryPolicyError("Authorized mutation branch must use agent/ namespace")
        self.client = client
        self.authorized_branch = authorized_branch

    def apply(self, artifact: EngineeringArtifact) -> RepositoryExecutionResult:
        validate_change_set(artifact)
        preflight = validate_source_preflight(artifact)
        if not preflight.passed:
            failed = [finding for finding in preflight.findings if not finding.passed]
            detail = "; ".join(f"{item.path}: {item.message}" for item in failed)
            raise RepositoryPolicyError(f"Source preflight failed: {detail}")
        if artifact.branch_name != self.authorized_branch:
            raise RepositoryPolicyError("Artifact branch does not match authorized branch")
        applied: list[str] = []
        for change in artifact.files:
            operation = {
                "create": self.client.create_file,
                "update": self.client.update_file,
                "delete": self.client.delete_file,
            }[change.operation]
            operation(self.authorized_branch, change, artifact.commit_message)
            normalized = str(PurePosixPath(change.path))
            stored = self.client.read_file(self.authorized_branch, normalized)
            if change.operation == "delete":
                if stored is not None:
                    raise RepositoryPolicyError(f"Post-mutation verification failed for deleted path: {normalized}")
            elif stored != change.content:
                raise RepositoryPolicyError(f"Post-mutation content verification failed: {normalized}")
            applied.append(normalized)
        commit_sha = self.client.get_branch_commit_sha(self.authorized_branch)
        if len(commit_sha) != 40:
            raise RepositoryPolicyError("Post-mutation commit SHA verification failed")
        return RepositoryExecutionResult(
            branch_name=self.authorized_branch,
            applied_paths=applied,
            commit_message=artifact.commit_message,
            dry_run=False,
            verification_performed=True,
            verified_paths=applied,
            commit_sha=commit_sha,
        )


class GovernedRepositoryExecutor(RepositoryExecutor):
    """Concrete executor whose only authority comes from a narrow mutation client."""

    def __init__(self, client: RepositoryMutationClient) -> None:
        self.client = client

    def apply(self, artifact: EngineeringArtifact) -> RepositoryExecutionResult:
        validate_change_set(artifact)
        self.client.create_branch(artifact.branch_name)
        applied: list[str] = []
        for change in artifact.files:
            operation = {
                "create": self.client.create_file,
                "update": self.client.update_file,
                "delete": self.client.delete_file,
            }[change.operation]
            operation(artifact.branch_name, change, artifact.commit_message)
            applied.append(str(PurePosixPath(change.path)))
        return RepositoryExecutionResult(
            branch_name=artifact.branch_name,
            applied_paths=applied,
            commit_message=artifact.commit_message,
            dry_run=False,
        )


def apply_single_change(change: ProposedFileChange) -> str:
    return str(PurePosixPath(change.path))
