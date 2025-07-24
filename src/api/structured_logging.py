"""Structured logging for production."""
import json
import logging
import time
from fastapi import Request


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for production."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class RequestLoggingMiddleware:
    """Log all HTTP requests with structured format."""

    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger(__name__)

    async def __call__(self, request: Request, call_next):
        """Log request and response."""
        start = time.time()
        response = await call_next(request)
        duration = time.time() - start

        self.logger.info(
            f"HTTP Request: {request.method} {request.url.path}",
            extra={
                "status_code": response.status_code,
                "duration_ms": int(duration * 1000),
                "client_ip": request.client.host if request.client else "unknown",
            },
        )

        return response
