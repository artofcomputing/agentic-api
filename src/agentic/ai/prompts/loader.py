from functools import lru_cache
from pathlib import Path

# Base directory relative to this file's position
PROMPTS_DIR = Path(__file__).parent.resolve()

@lru_cache(maxsize=32)
def get_prompt(agent: str, name: str) -> str:
    """Fetches prompt text for a given agent and prompt name.

    Args:
        agent: Subdirectory name under prompts (e.g., 'conversational').
        name: Name of the prompt file (e.g., 'SYSTEM_PROMPT').

    Returns:
        The stripped string content of the prompt file.
    """
    filename = name if name.endswith(".md") else f"{name}.md"
    file_path = PROMPTS_DIR / agent / filename

    try:
        return file_path.read_text(encoding="utf-8").strip()
    except Exception as e:
        raise RuntimeError(
            f"Missing or unreadable prompt file at {file_path}. Error: {e}"
        ) from e
