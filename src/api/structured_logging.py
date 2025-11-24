"""Structured logging with structlog for production."""

import time

import structlog

logger = structlog.get_logger(__name__)


def configure_logging(json_output: bool = True):
    """Configure structlog for the application.

    Args:
        json_output: If True, output JSON logs (production). If False, use
                     colored console output (development).
    """
    processors = [
        structlog.contextvars.merge_contextvars,
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
        wrapper_class=structlog.make_filtering_bound_logger(0),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


class RequestLoggingMiddleware:
    """Log all HTTP requests with structlog."""

    def __init__(self, app):
        self.app = app
        self.logger = structlog.get_logger("http")

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start = time.time()
        status_code = 500

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration = time.time() - start
            path = scope.get("path", "unknown")
            method = scope.get("method", "unknown")

            self.logger.info(
                "request",
                method=method,
                path=path,
                status_code=status_code,
                duration_ms=round(duration * 1000, 1),
            )
