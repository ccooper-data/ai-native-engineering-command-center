from pydantic import BaseModel

from .llm import GenerationMetadata


class BudgetExceededError(RuntimeError):
    pass


class TokenBudget(BaseModel):
    max_tokens_per_call: int
    max_tokens_per_run: int
    consumed_tokens: int = 0

    def record(self, generation: GenerationMetadata) -> None:
        used = generation.usage.total_tokens
        if used > self.max_tokens_per_call:
            raise BudgetExceededError(
                f"Model call used {used} tokens; per-call ceiling is {self.max_tokens_per_call}"
            )
        projected = self.consumed_tokens + used
        if projected > self.max_tokens_per_run:
            raise BudgetExceededError(
                f"Run would use {projected} tokens; run ceiling is {self.max_tokens_per_run}"
            )
        self.consumed_tokens = projected
