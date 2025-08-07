"""Request context management and correlation IDs."""
import contextvars
import uuid
import logging
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Context variables for request tracking
request_id_context: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)
user_context: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "user", default=None
)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware for managing request context and correlation IDs."""

    async def dispatch(self, request: Request, call_next):
        """Process request with context management."""
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request_id_context.set(request_id)

        # Extract user info if available
        user = request.headers.get("X-User-ID")
        if user:
            user_context.set(user)

        # Add request ID to response
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


def get_request_id() -> str:
    """Get current request ID from context."""
    return request_id_context.get()


def get_user() -> Optional[str]:
    """Get current user from context."""
    return user_context.get()


class ContextualLogger(logging.LoggerAdapter):
    """Logger adapter that includes request context in log records."""

    def process(self, msg, kwargs):
        """Add context to log message."""
        request_id = get_request_id()
        user = get_user()

        context_info = []
        if request_id:
            context_info.append(f"[{request_id}]")
        if user:
            context_info.append(f"[user:{user}]")

        if context_info:
            msg = " ".join(context_info) + " " + msg

        return msg, kwargs


def get_contextual_logger(name: str) -> ContextualLogger:
    """Get a contextual logger for a module."""
    logger = logging.getLogger(name)
    return ContextualLogger(logger, {})
