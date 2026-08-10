from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Hard ceiling on user instruction length, in *characters*. Doubles as the
# `le` cap for the configurable `instruction_limit` below and as the static
# `max_length` bound on the request schema, so oversized payloads are rejected
# during Pydantic validation.
MAX_INSTRUCTION_CHARS = 200_000


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
        le=MAX_INSTRUCTION_CHARS,
        description="Maximum characters the user may provide per instruction.",
    )

    request_timeout: int = Field(
        default=60,
        gt=0,
        le=600,
        description="End-to-end deadline (seconds) for a single agent request.",
    )

    retries: int = Field(
        default=1,
        ge=0,
        le=5,
        description=(
            "Tool/output retries per agent run (each retry is a full LLM round-trip)."
        ),
    )
