from pydantic import BaseModel, Field


class CommandResult(BaseModel):
    command: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    duration_ms: int = Field(ge=0)

    @property
    def passed(self) -> bool:
        return self.exit_code == 0


class ExecutableQAResult(BaseModel):
    passed: bool
    commands: list[CommandResult]


class ExecutableSecurityResult(BaseModel):
    passed: bool
    commands: list[CommandResult]
    blocking_tools: list[str]


def evaluate_qa_commands(commands: list[CommandResult]) -> ExecutableQAResult:
    return ExecutableQAResult(passed=bool(commands) and all(item.passed for item in commands), commands=commands)


def evaluate_security_commands(commands: list[CommandResult]) -> ExecutableSecurityResult:
    blocking = [item.command for item in commands if not item.passed]
    return ExecutableSecurityResult(
        passed=bool(commands) and not blocking,
        commands=commands,
        blocking_tools=blocking,
    )
