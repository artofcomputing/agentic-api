import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_ai.models import Model

from agentic.ai.prompts.loader import get_prompt
from agentic.api.deps import build_conversational_model
from agentic.api.health.probes import router as probes_router
from agentic.api.v1.router import api_router
from agentic.config.agent import AgentSettings
from agentic.config.fastapi import FastAPISettings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler for FastAPI application to run fail-fast checks."""
    # Readiness starts false; /readyz flips green only after the checks pass.
    app.state.ready = False
    logger.info("Performing fail-fast startup configuration checks...")
    try:
        # The prompt file must be readable before serving traffic
        # (also warms the lru_cache used on the request path).
        get_prompt("conversational", "SYSTEM_PROMPT")
        # The LLM model must be constructible from configuration
        # Built once here; requests reuse the shared instance
        # via app.state (no per-request provider/client construction).
        model, http_client = await build_conversational_model(app.state.agent_settings)
    except Exception as e:
        logger.critical("Fail-Fast Startup Error: %s", e)
        raise RuntimeError("Startup configuration checks failed") from e

    # Injects the model in the server state and mark the app ready
    # so the Kubernetes readiness probe (/readyz) starts succeeding.
    app.state.agent_model = model
    app.state.ready = True
    logger.info("Fail-fast configuration checks passed successfully.")
    try:
        yield
    # Teardown
    finally:
        app.state.ready = False
        await http_client.aclose()


def create_app(
    fastapi_settings: FastAPISettings,
    agent_settings: AgentSettings,
    agent_model: Model | None = None,  # test seam
) -> FastAPI:
    """Application factory for the FastAPI AI Agent server."""

    # Docs Feature Flag
    docs_url = f"/{fastapi_settings.docs_url}" if fastapi_settings.docs else None

    # Redoc Feature Flag
    redoc_url = f"/{fastapi_settings.redoc_url}" if fastapi_settings.redoc else None

    app = FastAPI(
        title="Agentic API",
        description="A modular, cloud-native API for AI Agents",
        version="0.1.0",
        docs_url=docs_url,
        redoc_url=redoc_url,
        lifespan=lifespan,
    )

    # Store FastAPI config state
    app.state.fastapi_settings = fastapi_settings
    # Store Agent config state
    app.state.agent_settings = agent_settings
    # Bounded concurrency gate for agents
    app.state.agent_concurrency = asyncio.Semaphore(agent_settings.max_concurrent_runs)

    # Test Seam for DeterministicModel and others, lifespan will override on startup
    app.state.agent_model = agent_model

    # Configure CORS: If '*' is present in allowed origins then
    # allow_credentials must be False to satisfy standard browser security
    allow_credentials = "*" not in fastapi_settings.cors_origins
    if not allow_credentials:
        logger.warning(
            "CORS wildcard origin enabled. "
            "Set FASTAPI_CORS_ORIGINS to explicit origins in production."
        )

    # noinspection bad-argument-type
    app.add_middleware(
        CORSMiddleware,
        allow_origins=fastapi_settings.cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=fastapi_settings.cors_methods,
        allow_headers=fastapi_settings.cors_headers,
    )

    # Register unauthenticated probe routes (/livez, /readyz) OUTSIDE the
    # protected API boundary so Kubernetes probes never need credentials.
    app.include_router(probes_router)

    # Register API v1 Routers
    app.include_router(api_router, prefix="/api/v1")

    return app
