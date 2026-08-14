import asyncio
import logging
from collections.abc import AsyncIterator

import httpx
from fastapi import HTTPException, Request, status
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers import Provider
from pydantic_ai.providers.alibaba import AlibabaProvider
from pydantic_ai.providers.openai import OpenAIProvider

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


def _build_provider(
    agent_config: AgentSettings, http_client: httpx.AsyncClient
) -> Provider:
    """Decouples provider construction from configuration."""
    api_key = agent_config.api_key.get_secret_value()
    if agent_config.provider == "openai_compatible":
        if not agent_config.provider_base_url:
            raise ValueError(
                "AGENT_BASE_URL is required when AGENT_PROVIDER=openai_compatible"
            )
        return OpenAIProvider(
            api_key=api_key,
            base_url=agent_config.provider_base_url,
            http_client=http_client,
        )
    return AlibabaProvider(api_key=api_key, http_client=http_client)


async def build_conversational_model(
    agent_config: AgentSettings,
) -> tuple[OpenAIChatModel, httpx.AsyncClient]:
    """Builds the shared LLM model plus the HTTP client it owns"""
    http_timeout = max(
        float(agent_config.request_timeout) - _HTTP_TIMEOUT_MARGIN_SECONDS,
        1.0,
    )
    http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(
            timeout=http_timeout, connect=_HTTP_CONNECT_TIMEOUT_SECONDS
        ),
    )

    try:
        model = OpenAIChatModel(
            model_name=agent_config.model,
            provider=_build_provider(agent_config, http_client),
        )
    except Exception:
        await http_client.aclose()
        raise
    return model, http_client


def get_conversational_agent_model(request: Request) -> Model:
    """Dependency returning the shared, lifespan-managed LLM model"""
    return request.app.state.agent_model


async def agent_capacity(request: Request) -> AsyncIterator[None]:
    """Bounded concurrency gate: rejects with 429 when all agent slots are busy.

    Async-generator dependency: the semaphore is held for the whole request and
    released even if the handler raises or the client disconnects (cancellation).
    """
    semaphore: asyncio.Semaphore = request.app.state.agent_concurrency
    if semaphore.locked():  # all slots busy -> shed load instead of queueing
        logger.warning("Agent concurrency limit reached; shedding request")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Server is at capacity; retry later",
            headers={"Retry-After": "5"},
        )
    async with semaphore:
        yield
