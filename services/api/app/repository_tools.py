from abc import ABC, abstractmethod
from pathlib import PurePosixPath

from pydantic import BaseModel

from .contracts import EngineeringArtifact, ProposedFileChange


class RepositoryPolicyError(ValueError):
    pass


class RepositoryExecutionResult(BaseModel):
    branch_name: str
    applied_paths: list[str]
    commit_message: str
    dry_run: bool


class RepositoryExecutor(ABC):
    @abstractmethod
    def apply(self, artifact: EngineeringArtifact) -> RepositoryExecutionResult:
        raise NotImplementedError


def validate_change_set(artifact: EngineeringArtifact) -> None:
    if not artifact.branch_name.startswith("agent/"):
        raise RepositoryPolicyError("Agent branches must use the agent/ namespace")
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


def apply_single_change(change: ProposedFileChange) -> str:
    """Return the normalized path after policy validation in future concrete executors."""
    path = PurePosixPath(change.path)
    return str(path)
