import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic_ai import UsageLimitExceeded, UsageLimits
from pydantic_ai.models import Model

from agentic.ai.agents.conversational.agent import (
    agent as conversational_agent,
)
from agentic.ai.agents.email.agent import agent as email_agent
from agentic.ai.tools.fibery import FiberyDeps
from agentic.api.deps import (
    get_agent_deps,
    get_agent_settings,
    get_conversational_agent_model,
    get_email_agent_model,
)
from agentic.api.schema import AgentRunRequest, AgentRunResponse
from agentic.config.agent import AgentSettings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/email",
    response_model=AgentRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Email Agent",
)
async def run_email_agent(
    payload: AgentRunRequest,
    deps: FiberyDeps = Depends(get_agent_deps),
    agent_settings: AgentSettings = Depends(get_agent_settings),
    model: Model = Depends(get_email_agent_model),
) -> AgentRunResponse:
    """Email Agent"""
    # Enforce the application-level instruction length limit
    if len(payload.user_instruction) > agent_settings.instruction_limit:
        logger.warning("User instruction exceeds the configured instruction limit")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Instruction exceeds maximum length of "
                f"{agent_settings.instruction_limit} characters."
            ),
        )

    # Run Agent
    try:
        logger.info("Executing email agent instruction")
        result = await email_agent.run(
            payload.user_instruction,
            model=model,
            deps=deps,
            usage_limits=UsageLimits(total_tokens_limit=agent_settings.token_limit),
        )
        logger.info("Email agent instruction completed successfully")

        return AgentRunResponse(output=result.output, usage=result.usage)

    except UsageLimitExceeded:
        logger.exception("Usage limit exceeded")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Usage limit exceeded",
        )

    except Exception:
        logger.exception("An error occurred during the conversational agent execution")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent execution failed",
        )


@router.post(
    "/chat",
    response_model=AgentRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Conversational Agent",
)
async def run_conversational_agent(
    payload: AgentRunRequest,
    agent_settings: AgentSettings = Depends(get_agent_settings),
    model: Model = Depends(get_conversational_agent_model),
) -> AgentRunResponse:
    """Conversational Agent"""
    # Enforce the application-level instruction length limit
    if len(payload.user_instruction) > agent_settings.instruction_limit:
        logger.warning("User instruction exceeds the configured instruction limit")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Instruction exceeds maximum length of "
                f"{agent_settings.instruction_limit} characters."
            ),
        )

    # Run Agent
    try:
        logger.info("Executing conversational agent instruction")
        result = await conversational_agent.run(
            payload.user_instruction,
            model=model,
            usage_limits=UsageLimits(total_tokens_limit=agent_settings.token_limit),
        )
        logger.info("Conversational agent instruction completed successfully")

        return AgentRunResponse(output=result.output, usage=result.usage)

    except UsageLimitExceeded:
        logger.exception("Usage limit exceeded")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Usage limit exceeded",
        )

    except Exception:
        logger.exception("An error occurred during the conversational agent execution")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent execution failed",
        )
