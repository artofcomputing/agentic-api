import logging

from pydantic_ai import Agent

from agentic.ai.prompts.loader import get_prompt

logger = logging.getLogger(__name__)

# Initialize the Pydantic AI Agent declaratively with tools and dependency type.
# Kept stateless: the model and the retry budget are supplied per-run from
# configuration (agent.run) to support runtime configuration.
agent = Agent()


@agent.system_prompt
def load_conversational_instructions() -> str:
    """Dynamically loads and injects instructions from SYSTEM_PROMPT.md"""
    try:
        content = get_prompt("conversational", "SYSTEM_PROMPT")
        logger.info("Successfully loaded SYSTEM_PROMPT")
        return content
    except Exception as e:
        logger.critical("Failed to read system prompt instructions. Error: %s", e)
        raise RuntimeError(
            "Missing or unreadable system prompt instruction file"
        ) from e
