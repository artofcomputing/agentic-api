"""Shared fixtures."""

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from pydantic_ai import models
from pydantic_ai.models.test import TestModel

from agentic.api.app import create_app
from agentic.config.agent import AgentSettings
from agentic.config.fastapi import FastAPISettings

# Fail loudly if any test accidentally attempts a real LLM round-trip.
models.ALLOW_MODEL_REQUESTS = False

TEST_API_KEY = "unit-test-api-key"


@pytest.fixture
def fastapi_settings() -> FastAPISettings:
    return FastAPISettings(
        api_key=SecretStr(TEST_API_KEY),
        docs=False,
        docs_url="docs",
        cors_origins=["http://testserver"],
        cors_methods=["GET", "POST"],
        cors_headers=["x-api-key", "content-type"],
    )


@pytest.fixture
def agent_settings() -> AgentSettings:
    return AgentSettings(
        api_key=SecretStr("test-llm-key"),
        provider="alibaba",
        model="test-model",
        token_total_limit=100_000,
        instruction_limit=200_000,
    )


@pytest.fixture
async def app(fastapi_settings, agent_settings):
    application = create_app(
        fastapi_settings=fastapi_settings,
        agent_settings=agent_settings,
        agent_model=TestModel(),  # deterministic, offline (needs FINDING-001)
    )
    async with application.router.lifespan_context(application):
        yield application


@pytest.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as http:
        yield http


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"x-api-key": TEST_API_KEY}
