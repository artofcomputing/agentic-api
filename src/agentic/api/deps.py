import logging

from fastapi import Depends as FastAPIDep
from fastapi import Request
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.alibaba import AlibabaProvider

from agentic.config.agent import AgentSettings
from agentic.config.fastapi import FastAPISettings

logger = logging.getLogger(__name__)


def get_fastapi_settings(request: Request) -> FastAPISettings:
    """Dependency to retrieve the FastAPI state settings."""
    return request.app.state.fastapi_settings


def get_agent_settings(request: Request) -> AgentSettings:
    """Dependency to retrieve the Agent state settings."""
    return request.app.state.agent_settings


def get_conversational_agent_model(
    agent_config: AgentSettings = FastAPIDep(get_agent_settings),
) -> Model:
    """Dependency to retrieve an initialized LLM Model object for the conversational agent."""
    provider = AlibabaProvider(api_key=agent_config.api_key.get_secret_value())
    return OpenAIChatModel(model_name=agent_config.model, provider=provider)
