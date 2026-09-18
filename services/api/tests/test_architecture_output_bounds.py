from app.contracts import (
    AcceptanceCriterion,
    ArchitectureArtifact,
    ArchitectureDecision,
    PlanningArtifact,
)
from app.providers import LLMArchitectureProvider


class PromptRecordingLLM:
    name = "test"
    model = "test"

    def __init__(self) -> None:
        self.prompt = ""

    def generate(self, *, system, prompt, schema):
        self.prompt = prompt
        return ArchitectureArtifact(
            summary="Bounded architecture",
            affected_components=["API"],
            data_flow=["request", "response"],
            api_changes=["Version endpoint"],
            data_changes=["Persist metadata"],
            security_controls=["Authorize tenant"],
            observability_requirements=["Trace requests"],
            decisions=[
                ArchitectureDecision(
                    id="ADR-001",
                    title="API boundary",
                    decision="Use versioned API",
                    rationale="Decouple clients",
                    consequences=["Maintain contract"],
                )
            ],
            implementation_sequence=["Contract", "Build", "Test"],
        )


def test_architecture_prompt_explicitly_bounds_artifact_size() -> None:
    plan = PlanningArtifact(
        business_objective="Reduce churn",
        scope=["Forecast churn"],
        assumptions=["Historical data exists"],
        functional_requirements=["Produce forecast"],
        non_functional_requirements=["Audit access"],
        acceptance_criteria=[
            AcceptanceCriterion(id="AC-001", statement="Forecast is retrievable")
        ],
        dependencies=["Customer data"],
        risks=["Drift"],
        implementation_tasks=["Build", "Test"],
    )
    llm = PromptRecordingLLM()
    LLMArchitectureProvider(llm).design("Add churn forecasting.", plan)

    assert "at most 8 affected components" in llm.prompt
    assert "6 architecture decisions" in llm.prompt
    assert "12 implementation-sequence steps" in llm.prompt
