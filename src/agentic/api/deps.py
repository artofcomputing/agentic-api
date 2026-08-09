import logging

from fastapi import Depends as FastAPIDep
from fastapi import Request
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.alibaba import AlibabaProvider

from agentic.ai.tools.fibery import FiberyDeps
from agentic.config.agent import AgentSettings
from agentic.config.fastapi import FastAPISettings
from agentic.config.fibery import FiberySettings

logger = logging.getLogger(__name__)


def get_fastapi_settings(request: Request) -> FastAPISettings:
    """Dependency to retrieve the FastAPI state settings."""
    return request.app.state.fastapi_settings


def get_agent_settings(request: Request) -> AgentSettings:
    """Dependency to retrieve the Agent state settings."""
    return request.app.state.agent_settings


def get_fibery_settings(request: Request) -> FiberySettings:
    """Dependency to retrieve the Fibery state settings."""
    return request.app.state.fibery_settings


def get_agent_deps(
    fibery_config: FiberySettings = FastAPIDep(get_fibery_settings),
) -> FiberyDeps:
    """Dependency to retrieve an initialized Deps object for the Pydantic AI agent."""

    return FiberyDeps(
        url=fibery_config.url,
        api_key=fibery_config.api_key,
    )


def get_email_agent_model(
    agent_config: AgentSettings = FastAPIDep(get_agent_settings),
) -> Model:
    """Dependency to retrieve an initialized LLM Model object for the Email agent."""
    provider = AlibabaProvider(api_key=agent_config.api_key.get_secret_value())
    return OpenAIChatModel(model_name=agent_config.model, provider=provider)


def get_conversational_agent_model(
    agent_config: AgentSettings = FastAPIDep(get_agent_settings),
) -> Model:
    """Dependency to retrieve an initialized LLM Model object for the conversational agent."""
    provider = AlibabaProvider(api_key=agent_config.api_key.get_secret_value())
    return OpenAIChatModel(model_name=agent_config.model, provider=provider)
