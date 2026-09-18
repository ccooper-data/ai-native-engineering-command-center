import ast
from pathlib import PurePosixPath

from pydantic import BaseModel

from .contracts import EngineeringArtifact


class SourcePreflightFinding(BaseModel):
    path: str
    check: str
    passed: bool
    message: str


class SourcePreflightResult(BaseModel):
    passed: bool
    findings: list[SourcePreflightFinding]


def validate_source_preflight(artifact: EngineeringArtifact) -> SourcePreflightResult:
    """Deterministic source checks before mutation; CI remains authoritative."""
    findings: list[SourcePreflightFinding] = []
    for change in artifact.files:
        if change.operation == "delete" or change.content is None:
            continue
        suffix = PurePosixPath(change.path).suffix.lower()
        if suffix == ".py":
            try:
                ast.parse(change.content)
                findings.append(SourcePreflightFinding(path=change.path, check="python-syntax", passed=True, message="Python AST parsed successfully."))
            except SyntaxError as exc:
                findings.append(SourcePreflightFinding(path=change.path, check="python-syntax", passed=False, message=f"Python syntax error at line {exc.lineno}: {exc.msg}"))
        if suffix in {".ts", ".tsx"}:
            suspicious = "\\n" in change.content
            findings.append(SourcePreflightFinding(path=change.path, check="typescript-representation", passed=not suspicious, message="Literal escaped newline sequence detected." if suspicious else "Source representation check passed."))
    return SourcePreflightResult(passed=all(item.passed for item in findings), findings=findings)
