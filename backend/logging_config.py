"""
Structured JSON logging configuration for TikTok Live Recorder API.
"""

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional

from pythonjsonlogger import jsonlogger


# Context variables for tracking request/task context
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)
task_id_ctx: ContextVar[Optional[str]] = ContextVar("task_id", default=None)
room_id_ctx: ContextVar[Optional[str]] = ContextVar("room_id", default=None)
url_ctx: ContextVar[Optional[str]] = ContextVar("url", default=None)


class CorrelationFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter that includes context variables."""

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ):
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)

        # Add timestamp
        log_record["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Add context variables
        log_record["correlation_id"] = correlation_id_ctx.get()
        log_record["task_id"] = task_id_ctx.get()
        log_record["room_id"] = room_id_ctx.get()
        log_record["url"] = url_ctx.get()

        # Add service info
        log_record["service"] = "tiktok-live-recorder-api"
        log_record["version"] = "1.0.0"

        # Clean up None values
        log_record = {k: v for k, v in log_record.items() if v is not None}


def setup_logging(level: str = "INFO") -> None:
    """Setup structured JSON logging."""

    # Create formatter
    formatter = CorrelationFormatter(fmt="%(timestamp)s %(level)s %(name)s %(message)s")

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Configure specific loggers
    loggers = [
        "uvicorn",
        "uvicorn.access",
        "celery",
        "celery.task",
        "service",
    ]

    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(getattr(logging, level.upper()))
        logger.propagate = True


def generate_correlation_id() -> str:
    """Generate a new correlation ID."""
    return str(uuid.uuid4())


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID in context."""
    correlation_id_ctx.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID from context."""
    return correlation_id_ctx.get()


def set_task_context(
    task_id: str, room_id: Optional[str] = None, url: Optional[str] = None
) -> None:
    """Set task context variables."""
    task_id_ctx.set(task_id)
    if room_id:
        room_id_ctx.set(room_id)
    if url:
        url_ctx.set(url)


def clear_context() -> None:
    """Clear all context variables."""
    correlation_id_ctx.set(None)
    task_id_ctx.set(None)
    room_id_ctx.set(None)
    url_ctx.set(None)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)
