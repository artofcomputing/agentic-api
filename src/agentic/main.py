import logging

import uvicorn

from agentic.api.app import create_app
from agentic.config.agent import AgentSettings
from agentic.config.fastapi import FastAPISettings
from agentic.config.fibery import FiberySettings
from agentic.config.logger import LoggerSettings
from agentic.logger import setup_logging

log_settings = LoggerSettings()

# Configure initial logging using our custom structured JSON formatter
setup_logging(log_level=log_settings.level, json_format=log_settings.json_format)
logger = logging.getLogger("main")


def start_web_server():

    # FastAPI Settings Initialization
    fastapi_settings: FastAPISettings = FastAPISettings()  # type: ignore[call-arg]

    # Agent Settings Initialization
    agent_settings: AgentSettings = AgentSettings()  # type: ignore[call-arg]

    # Fibery Settings Initialization
    fibery_settings: FiberySettings = FiberySettings()  # type: ignore[call-arg]

    """Starts the FastAPI Web Server using uvicorn."""
    logger.info(
        "Starting FastAPI Web Server on %s:%s...",
        fastapi_settings.host,
        fastapi_settings.port,
    )
    app = create_app(
        fastapi_settings=fastapi_settings,
        agent_settings=agent_settings,
        fibery_settings=fibery_settings,
    )
    uvicorn.run(
        app,
        host=fastapi_settings.host,
        port=fastapi_settings.port,
        log_config=None,
    )


if __name__ == "__main__":
    start_web_server()
