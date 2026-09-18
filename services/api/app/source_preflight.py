import ast
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import PurePosixPath

from pydantic import BaseModel

from .contracts import EngineeringArtifact


class SourcePreflightFinding(BaseModel):
    path: str
    check: str
    passed: bool
    message: str


def _ruff_check(path: str, content: str) -> SourcePreflightFinding:
    executable = shutil.which("ruff")
    if executable is None:
        return SourcePreflightFinding(path=path, check="ruff", passed=True, message="Ruff unavailable; authoritative CI check remains required.")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", encoding="utf-8") as handle:
        handle.write(content)
        handle.flush()
        result = subprocess.run(
            [executable, "check", "--output-format", "concise", handle.name],
            capture_output=True,
            text=True,
            check=False,
        )
    message = (result.stdout or result.stderr).strip()
    return SourcePreflightFinding(
        path=path,
        check="ruff",
        passed=result.returncode == 0,
        message=message or "Ruff check passed.",
    )


class SourcePreflightResult(BaseModel):
    artifact_digest: str
    passed: bool
    findings: list[SourcePreflightFinding]


def engineering_artifact_digest(artifact: EngineeringArtifact) -> str:
    payload = json.dumps(artifact.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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
                findings.append(_ruff_check(change.path, change.content))
            except SyntaxError as exc:
                findings.append(SourcePreflightFinding(path=change.path, check="python-syntax", passed=False, message=f"Python syntax error at line {exc.lineno}: {exc.msg}"))
        if suffix in {".ts", ".tsx"}:
            suspicious = "\\n" in change.content
            findings.append(SourcePreflightFinding(path=change.path, check="typescript-representation", passed=not suspicious, message="Literal escaped newline sequence detected." if suspicious else "Source representation check passed."))
    return SourcePreflightResult(artifact_digest=engineering_artifact_digest(artifact), passed=all(item.passed for item in findings), findings=findings)
