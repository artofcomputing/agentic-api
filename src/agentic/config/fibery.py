from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class FiberySettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="FIBERY_", extra="ignore"
    )

    api_key: SecretStr = Field(
        description="The API Key required to authenticate with Fibery"
    )

    url: str = Field(description="Fibery GraphQL endpoint")
