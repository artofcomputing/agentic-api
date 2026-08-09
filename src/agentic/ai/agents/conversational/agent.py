import logging

from pydantic_ai import Agent

from agentic.ai.prompts.loader import load_prompt

logger = logging.getLogger(__name__)

# Initialize the Pydantic AI Agent declaratively with tools and dependency type.
# The model is dynamically passed during execution (agent.run) to support runtime configuration.
agent = Agent(retries=3)


@agent.system_prompt
def load_conversational_instructions() -> str:
    """Dynamically loads and injects instructions from SYSTEM_PROMPT.md"""
    try:
        content = load_prompt("conversational", "SYSTEM_PROMPT")
        logger.info("Successfully loaded SYSTEM_PROMPT")
        return content
    except Exception as e:
        logger.critical("Failed to read system prompt instructions. Error: %s", e)
        raise RuntimeError(
            "Missing or unreadable system prompt instruction file"
        ) from e
