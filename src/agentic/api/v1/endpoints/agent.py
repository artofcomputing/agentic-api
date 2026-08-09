import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic_ai import UsageLimitExceeded, UsageLimits
from pydantic_ai.models import Model

from agentic.ai.agents.conversational.agent import (
    agent as conversational_agent,
)
from agentic.ai.agents.email.agent import agent as email_agent
from agentic.ai.prompts.loader import load_prompt
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
    payload: AgentRunRequest | None = None,
    deps: FiberyDeps = Depends(get_agent_deps),
    agent_settings: AgentSettings = Depends(get_agent_settings),
    model: Model = Depends(get_email_agent_model),
) -> AgentRunResponse:
    """Email Agent"""
    # Resolve user instruction, if any
    if payload and payload.user_instruction:
        logger.info("User instruction received")
        instruction = payload.user_instruction
    else:
        try:
            instruction = load_prompt("email", "DEFAULT_INSTRUCTION")
            logger.info("Using email default instruction from DEFAULT_INSTRUCTION.md")
        except Exception as e:
            logger.critical("Failed to load email default instruction: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to load email default instruction prompt.",
            )

    # Run Agent
    try:
        logger.info("Executing email agent instruction")
        result = await email_agent.run(
            instruction,
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
    payload: AgentRunRequest | None = None,
    agent_settings: AgentSettings = Depends(get_agent_settings),
    model: Model = Depends(get_conversational_agent_model),
) -> AgentRunResponse:
    """Conversational Agent"""
    # Resolve user instruction, if any
    if payload and payload.user_instruction:
        logger.info("User instruction received")
        instruction = payload.user_instruction
    else:
        try:
            instruction = load_prompt("conversational", "DEFAULT_INSTRUCTION")
            logger.info(
                "Using conversational default instruction from DEFAULT_INSTRUCTION.md"
            )
        except Exception:
            logger.critical("Failed to load conversational default instruction")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to load conversational default instruction prompt.",
            )

    # Run Agent
    try:
        logger.info("Executing conversational agent instruction")
        result = await conversational_agent.run(
            instruction,
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
