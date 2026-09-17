from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./command_center.db"
    llm_provider: str = "mock"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="COMMAND_CENTER_")


settings = Settings()
