import logging

from pydantic_ai import Agent, RunContext

from agentic.ai.prompts.loader import load_prompt
from agentic.ai.tools import fibery_toolset
from agentic.ai.tools.fibery import FiberyDeps

logger = logging.getLogger(__name__)

# Initialize the Pydantic AI Agent declaratively with tools and dependency type.
# The model is dynamically passed during execution (agent.run) to support runtime configuration.
agent = Agent(deps_type=FiberyDeps, retries=3, toolsets=[fibery_toolset])


@agent.system_prompt
def load_instructions(ctx: RunContext[FiberyDeps]) -> str:
    """Dynamically loads and injects instructions from SYSTEM_PROMPT.md."""
    try:
        content = load_prompt("email", "SYSTEM_PROMPT")
        logger.info("Successfully loaded SYSTEM_PROMPT")
        return content
    except Exception as e:
        logger.critical("Failed to read system prompt instructions. Error: %s", e)
        raise RuntimeError(
            "Missing or unreadable system prompt instruction file"
        ) from e
