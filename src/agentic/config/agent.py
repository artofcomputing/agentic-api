from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="AGENT_", extra="ignore"
    )

    api_key: SecretStr = Field(description="The API key required for LLM model")
    model: str = Field(description="The model to be used")
    token_limit: int = Field(
        gt=0,
        le=2_000_000,
        description="The maximum amount of tokens to use for a session",
    )

    instruction_limit: int = Field(
        gt=0,
        le=200_000,
        description="The maximum amount of tokens that the user can provide per instruction.",
    )
