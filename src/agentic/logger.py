import json
import logging
from datetime import UTC, datetime
from typing import Any

_VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def _get_reserved_attrs() -> set[str]:
    dummy_record = logging.LogRecord("", 0, "", 0, "", None, None)
    reserved = {a for a in dir(dummy_record) if "__" not in a}
    return reserved


RESERVED_ATTRS: set[str] = _get_reserved_attrs()

# Custom ignored logs attributes
IGNORED_ATTRS: set[str] = {"color_message"}


class JsonFormatter(logging.Formatter):
    """Custom logging formatter that outputs log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include traceback details if an exception is logged
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        # Include stack details if an exception is logged
        if record.stack_info:
            payload["stack_info"] = self.formatStack(record.stack_info)

        # Merge any custom fields passed via extra={...}
        for key, value in record.__dict__.items():
            if (
                key not in RESERVED_ATTRS
                and key not in IGNORED_ATTRS  # <-- Ignore extra fields here
                and key not in payload
            ):
                payload[key] = value

        return json.dumps(payload, default=str)


def setup_logging(log_level: str = "INFO", json_format: bool = True) -> None:
    """Configures global logging stream handler using either JSON or standard formatting."""
    name = log_level.strip().upper()
    if name not in _VALID_LEVELS:
        raise ValueError(
            f"Invalid LOG_LEVEL {log_level!r}; expected one of {sorted(_VALID_LEVELS)}"
        )

    root_logger = logging.getLogger()

    # Clear existing handlers to prevent duplicate logging
    root_logger.handlers.clear()

    # Stream to standard output / error
    handler = logging.StreamHandler()

    if json_format:
        handler.setFormatter(JsonFormatter())
    else:
        # Standard human-readable console logging
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )

    root_logger.addHandler(handler)
    root_logger.setLevel(logging.getLevelNamesMapping()[name])
