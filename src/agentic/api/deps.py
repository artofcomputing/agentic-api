import logging

import httpx
from fastapi import Request
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.alibaba import AlibabaProvider

from agentic.config.agent import AgentSettings
from agentic.config.fastapi import FastAPISettings

logger = logging.getLogger(__name__)

# Per-HTTP-call budget is kept slightly below the request-level asyncio
# deadline (AGENT_REQUEST_TIMEOUT) so upstream stalls surface as transport
# errors before the outer deadline cancels the whole run.
_HTTP_TIMEOUT_MARGIN_SECONDS = 5.0
_HTTP_CONNECT_TIMEOUT_SECONDS = 5.0


def get_fastapi_settings(request: Request) -> FastAPISettings:
    """Dependency to retrieve the FastAPI state settings."""
    return request.app.state.fastapi_settings


def get_agent_settings(request: Request) -> AgentSettings:
    """Dependency to retrieve the Agent state settings."""
    return request.app.state.agent_settings


def build_conversational_model(
    agent_config: AgentSettings,
) -> tuple[OpenAIChatModel, httpx.AsyncClient]:
    """Builds the shared LLM model plus the HTTP client it owns (closed at shutdown).

    The caller owns the returned ``httpx.AsyncClient`` and must close it
    deterministically (application lifespan shutdown): the provider does not
    own it and will therefore never close it itself.
    """
    http_timeout = max(
        float(agent_config.request_timeout) - _HTTP_TIMEOUT_MARGIN_SECONDS,
        1.0,
    )
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(
            timeout=http_timeout, connect=_HTTP_CONNECT_TIMEOUT_SECONDS
        ),
    )
    provider = AlibabaProvider(
        api_key=agent_config.api_key.get_secret_value(),
        http_client=http_client,
    )
    model = OpenAIChatModel(model_name=agent_config.model, provider=provider)
    return model, http_client


def get_conversational_agent_model(request: Request) -> Model:
    """Dependency returning the shared, lifespan-managed LLM model."""
    return request.app.state.agent_model
