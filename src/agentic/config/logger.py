from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggerSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="LOG_", extra="ignore"
    )

    level: str = Field(
        default="INFO",
        description="Global logging level",
    )

    json_format: bool = Field(
        description="Enable JSON logging",
        default=True,
    )
