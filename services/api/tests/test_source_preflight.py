from app.contracts import EngineeringArtifact, ProposedFileChange
from app.source_preflight import validate_source_preflight


def artifact(path: str, content: str) -> EngineeringArtifact:
    return EngineeringArtifact(
        branch_name="agent/preflight",
        commit_message="test: source preflight",
        summary="preflight",
        files=[ProposedFileChange(path=path, operation="create", purpose="test", content=content)],
        acceptance_criteria_addressed=["AC-001"],
        tests_required=["preflight"],
        security_notes=[],
    )


def test_python_syntax_error_is_blocked_before_mutation() -> None:
    result = validate_source_preflight(artifact("src/bad.py", "def broken(:\n    pass\n"))
    assert result.passed is False
    assert result.findings[0].check == "python-syntax"


def test_valid_python_source_passes_preflight() -> None:
    assert validate_source_preflight(artifact("src/good.py", "VALUE = 1\n")).passed is True


def test_literal_escaped_newline_in_typescript_is_blocked() -> None:
    result = validate_source_preflight(artifact("app/page.tsx", r"type A = {};\ntype B = {};"))
    assert result.passed is False
    assert result.findings[0].check == "typescript-representation"
