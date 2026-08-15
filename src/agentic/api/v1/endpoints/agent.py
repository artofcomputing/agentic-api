import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic_ai import UsageLimitExceeded, UsageLimits
from pydantic_ai.exceptions import (
    AgentRunError,
    ModelAPIError,
    ModelHTTPError,
    UnexpectedModelBehavior,
)
from pydantic_ai.models import Model

from agentic.ai.agents.conversational.agent import (
    agent as conversational_agent,
)
from agentic.ai.tools import time_toolset
from agentic.api.deps import (
    agent_capacity,
    get_agent_settings,
    get_conversational_agent_model,
)
from agentic.ai.agents.conversational.schema import AgentRunRequest, AgentRunResponse
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
    _capacity: None = Depends(agent_capacity),
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
            # NOTE: Count Tokens before request is not implemented for OpenAI compatible
            # endpoints, therefore it cannot be enabled to save costs with Pydantic AI.
            result = await conversational_agent.run(
                payload.user_instruction,
                model=model,
                usage_limits=UsageLimits(
                    total_tokens_limit=agent_settings.token_total_limit,
                    tool_calls_limit=agent_settings.tool_calls_limit,
                    output_tokens_limit=agent_settings.output_tokens_limit,
                ),
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

    except ModelHTTPError as exc:
        # Upstream provider returned an HTTP error (auth, throttling, outage).

        retry_after = getattr(exc, "retry_after", None)

        headers = {"Retry-After": str(retry_after)} if retry_after else None

        if exc.status_code in (401, 403):
            logger.error(
                "LLM provider rejected credentials (upstream %s)", exc.status_code
            )

            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="LLM provider authentication failure",
            )

        if exc.status_code == 429:
            logger.warning("LLM provider rate-limited the request")

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LLM provider busy",
                headers=headers,
            )

        logger.warning("LLM provider error (upstream %s)", exc.status_code)

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM provider request failed",
        )

    except ModelAPIError, UnexpectedModelBehavior, AgentRunError:
        logger.exception("LLM communication/protocol failure")

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LLM provider communication failure",
        )

    except Exception:
        logger.exception("An error occurred during the conversational agent execution")

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Agent execution failed",
        )
