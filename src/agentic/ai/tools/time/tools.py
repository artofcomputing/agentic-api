import logging
from datetime import UTC, datetime
from typing import Any

from pydantic_ai import FunctionToolset

logger = logging.getLogger(__name__)

# Initializes Time Toolset collection
time_toolset = FunctionToolset()


@time_toolset.tool_plain
def get_current_time() -> dict[str, Any]:
    """Fetches the current time from the system.

    Returns:
        A dictionary containing the current UTC time as an ISO 8601 string,
        the local time with UTC offset, and the UNIX epoch timestamp.
    """
    now_utc = datetime.now(UTC)
    result = {
        "utc_now": now_utc.isoformat(),
        "local_now": now_utc.astimezone().isoformat(),
        "timestamp": now_utc.timestamp(),
    }
    logger.info("Fetched current time: %s", result["utc_now"])
    return result
