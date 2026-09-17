from app.execution_evidence import CommandResult, evaluate_qa_commands, evaluate_security_commands


def result(command: str, exit_code: int) -> CommandResult:
    return CommandResult(command=command, exit_code=exit_code, duration_ms=10)


def test_qa_requires_real_successful_command_evidence() -> None:
    evidence = evaluate_qa_commands([result("pytest -q", 0), result("ruff check .", 0)])
    assert evidence.passed is True


def test_qa_blocks_when_any_command_fails() -> None:
    evidence = evaluate_qa_commands([result("pytest -q", 1), result("ruff check .", 0)])
    assert evidence.passed is False


def test_security_records_blocking_tool_failures() -> None:
    evidence = evaluate_security_commands(
        [result("gitleaks detect", 0), result("semgrep scan --config auto", 1)]
    )
    assert evidence.passed is False
    assert evidence.blocking_tools == ["semgrep scan --config auto"]


def test_empty_evidence_cannot_pass() -> None:
    assert evaluate_qa_commands([]).passed is False
    assert evaluate_security_commands([]).passed is False
