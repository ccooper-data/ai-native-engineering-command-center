from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./command_center.db"
    llm_provider: str = "mock"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5.6-terra"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-5"
    llm_max_output_tokens: int = Field(default=4096, ge=256, le=32768)
    llm_max_tokens_per_call: int = Field(default=20000, ge=1000)
    llm_max_tokens_per_run: int = Field(default=50000, ge=1000)
    llm_max_cost_per_call_usd: float = Field(default=0.10, gt=0)
    llm_max_cost_per_run_usd: float = Field(default=0.25, gt=0)

    model_config = SettingsConfigDict(env_file=".env", env_prefix="COMMAND_CENTER_")


settings = Settings()
