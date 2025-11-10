"""Centralized logging configuration using structlog."""
import logging
import os

import structlog


def configure_logging(log_level: str = "INFO", json_output: bool = None):
    """Configure application-wide structured logging.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).
        json_output: Force JSON output. Defaults to True in production
                     (QUANTAI_ENV=production), False otherwise.
    """
    if json_output is None:
        json_output = os.getenv("QUANTAI_ENV", "development") == "production"

    level = getattr(logging, log_level.upper(), logging.INFO)

    # Configure stdlib logging to route through structlog
    logging.basicConfig(format="%(message)s", level=level)

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
    ]

    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


# Configure at module import
configure_logging()
