from typing import Any

from pydantic import BaseModel, Field


class AgentRunRequest(BaseModel):
    """Schema for requesting an agent execution with a user instruction."""

    user_instruction: str = Field(
        ...,
        min_length=1,
        description="Markdown text or instruction query",
    )


class AgentRunResponse(BaseModel):
    """Schema representing the successful execution result of the Agent."""

    output: Any = Field(
        ..., description="The direct output/result of the agent execution"
    )
    # The usage field is extremely dynamic due to different provider's definitions of usage, therefore it's best
    # to keep it simple.
    usage: Any = Field(..., description="The agent API usage results")
