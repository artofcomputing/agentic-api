import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agentic.api.probes import router as probes_router
from agentic.api.v1.router import api_router
from agentic.config.agent import AgentSettings
from agentic.config.fastapi import FastAPISettings
from agentic.config.fibery import FiberySettings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan handler for FastAPI application to run fail-fast checks."""
    # Readiness starts false; /readyz flips green only after the checks pass.
    app.state.ready = False
    logger.info("Performing fail-fast startup configuration checks...")
    try:
        # Verify every settings object was attached to app.state by
        # create_app(); a missing attribute raises immediately (fail fast).
        _ = (
            app.state.fastapi_settings,
            app.state.agent_settings,
            app.state.fibery_settings,
        )
        logger.info("Fail-fast configuration checks passed successfully.")
    except Exception as e:
        logger.critical(
            "Fail-Fast Startup Error: Configuration validation failed: %s",
            e,
        )
        raise SystemExit(1) from e
    # Startup checks passed: mark the app ready so the Kubernetes readiness
    # probe (/readyz) starts succeeding.
    app.state.ready = True
    yield


def create_app(
    fastapi_settings: FastAPISettings,
    agent_settings: AgentSettings,
    fibery_settings: FiberySettings,
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
    # Store Fibery config state
    app.state.fibery_settings = fibery_settings

    # Configure CORS: If '*' is present in allowed origins then
    # allow_credentials must be False to satisfy standard browser security
    allow_credentials = "*" not in fastapi_settings.cors_origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=fastapi_settings.cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register unauthenticated probe routes (/livez, /readyz) OUTSIDE the
    # protected API boundary so Kubernetes probes never need credentials.
    app.include_router(probes_router)

    # Register API v1 Routers
    app.include_router(api_router, prefix="/api/v1")

    return app
