import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic_ai import UsageLimitExceeded, UsageLimits
from pydantic_ai.models import Model

from agentic.ai.agents.conversational.agent import (
    agent as conversational_agent,
)
from agentic.ai.tools import time_toolset
from agentic.api.deps import (
    get_agent_settings,
    get_conversational_agent_model,
)
from agentic.api.schema import AgentRunRequest, AgentRunResponse
from agentic.config.agent import AgentSettings

logger = logging.getLogger(__name__)

router = APIRouter()


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
    # Enforce the configurable instruction length limit. The hard ceiling
    # (MAX_INSTRUCTION_CHARS) is already enforced during schema validation.
    if len(payload.user_instruction) > agent_settings.instruction_limit:
        logger.warning("User instruction exceeds the configured instruction limit")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Instruction exceeds maximum length of "
                f"{agent_settings.instruction_limit} characters."
            ),
        )

    # Run Agent under a hard end-to-end deadline.
    try:
        logger.info("Executing conversational agent instruction")
        async with asyncio.timeout(agent_settings.request_timeout):
            result = await conversational_agent.run(
                payload.user_instruction,
                model=model,
                usage_limits=UsageLimits(total_tokens_limit=agent_settings.token_limit),
                toolsets=[time_toolset],
                retries=agent_settings.retries,
            )
        logger.info("Conversational agent instruction completed successfully")

        return AgentRunResponse(output=result.output, usage=result.usage)

    except TimeoutError:
        logger.warning(
            "Agent execution timed out after %s seconds",
            agent_settings.request_timeout,
        )
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Agent execution timed out",
        )

    except UsageLimitExceeded:
        logger.warning("Agent usage limit exceeded")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Usage limit exceeded",
        )

    except Exception:
        logger.exception("An error occurred during the conversational agent execution")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent execution failed",
        )
