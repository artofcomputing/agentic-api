import json
from typing import Annotated, Any

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class FastAPISettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="FASTAPI_", extra="ignore"
    )

    api_key: SecretStr = Field(
        description="The FastAPI key required to secure the HTTP endpoints.",
    )

    docs: bool = Field(
        default=True,
        description="Whether or not the FastAPI docs should be shown.",
    )

    docs_url: str = Field(
        description="The base URL for the FastAPI docs endpoint.",
    )

    redoc: bool = Field(
        default=True,
        description="Whether or not the FastAPI redoc should be shown.",
    )

    redoc_url: str = Field(
        default="redoc",
        description="The base URL for the FastAPI redoc endpoint.",
    )

    host: str = Field(
        default="localhost",
        description="The FastAPI host where the FastAPI server will bind.",
    )

    port: int = Field(
        default=8000,
        description="The FastAPI port where the FastAPI server will bind.",
    )

    cors_origins: Annotated[list[str], NoDecode] = Field(
        description="List of origins allowed to make CORS requests."
    )

    cors_methods: Annotated[list[str], NoDecode] = Field(
        description="List of methods allowed to make CORS requests."
    )

    cors_headers: Annotated[list[str], NoDecode] = Field(
        description="List of headers allowed to make CORS requests."
    )

    max_body_bytes: int = Field(
        default=2_097_152,  # 2 MiB; covers MAX_INSTRUCTION_CHARS + JSON overhead + room for API growth
        gt=0,
        description="Maximum accepted request body size in bytes.",
    )

    @field_validator("cors_origins", "cors_methods", "cors_headers", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> Any:
        """Parses the CORS origins JSON array from string-based sources.

        Docker's --env-file (unlike python-dotenv) preserves surrounding quotes,
        so values like '["*"]' arrive still wrapped in single quotes. Strips any
        wrapping quotes before decoding to guarantee identical behavior across
        dotenv files, --env-file, and plain environment variables.
        """
        if isinstance(value, str):
            candidate = value.strip()
            if (
                len(candidate) >= 2
                and candidate[0] == candidate[-1]
                and candidate[0] in {"'", '"'}
            ):
                candidate = candidate[1:-1]
            return json.loads(candidate)
        return value

    @field_validator("cors_origins", mode="after")
    @classmethod
    def validate_cors_origins(cls, value: list[str]) -> list[str]:
        """Require explicit scheme so default configs can never silently no-match."""
        for origin in value:
            if origin != "*" and not origin.startswith(("http://", "https://")):
                raise ValueError(
                    "CORS origin must include scheme and port, e.g. "
                    f"'http://127.0.0.1:3000'; got {origin!r}"
                )
        return value
