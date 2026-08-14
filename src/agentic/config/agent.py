from typing import Literal

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
    provider: Literal["openai_compatible", "alibaba"] = Field(
        default="alibaba",
        description="LLM provider backend to be used by the conversational agent.",
    )
    provider_base_url: str | None = Field(
        default=None,
        description="Override endpoint required for OpenAI compatible providers.",
    )
    model: str = Field(description="The model to be used")
    token_total_limit: int = Field(
        gt=0,
        le=2_000_000,
        description=(
            "Maximum tokens for a single agent run (each request is a fresh, "
            "stateless run; cross-request budgets require an external limiter)"
        ),
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
        description="Tool/output retries per agent run (each retry is a full LLM round-trip).",
    )

    max_concurrent_runs: int = Field(
        default=3,
        gt=0,
        le=128,
        description="Maximum agent executions in flight per instance before load shedding.",
    )

    tool_calls_limit: int = Field(
        default=10,
        gt=0,
        le=50,
        description="Maximum tool invocations per agent run",
    )

    output_tokens_limit: int = Field(
        default=100_000,
        gt=0,
        le=2_000_000,
        description="Maximum generated tokens per agent run",
    )
