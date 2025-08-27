"""
Middleware for request/response logging and monitoring.
"""
import logging
import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all incoming requests and outgoing responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Log incoming request
        start_time = time.time()
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)

            # Log outgoing response
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"Status: {response.status_code} - Time: {process_time:.3f}s"
            )

            return response
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"[{request_id}] {request.method} {request.url.path} - "
                f"Error: {str(e)} - Time: {process_time:.3f}s",
                exc_info=True,
            )
            raise
