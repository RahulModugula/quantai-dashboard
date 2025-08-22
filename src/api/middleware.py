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


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to responses."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with security headers."""
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self' 'unsafe-inline'"
        )

        return response


class CacheMiddleware(BaseHTTPMiddleware):
    """Cache GET responses."""

    def __init__(self, app, ttl: int = 3600):
        """Initialize cache middleware."""
        super().__init__(app)
        self.ttl = ttl
        self.cache = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with caching."""
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)

        cache_key = f"{request.method}:{request.url.path}"

        if cache_key in self.cache:
            cached_response = self.cache[cache_key]

            # Check if still valid
            if time.time() - cached_response["time"] < self.ttl:
                logger.debug(f"Cache hit: {cache_key}")
                return Response(
                    content=cached_response["body"],
                    status_code=cached_response["status"],
                    headers=dict(cached_response["headers"]),
                    media_type="application/json",
                )

        response = await call_next(request)

        # Cache successful responses
        if response.status_code == 200:
            try:
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk

                self.cache[cache_key] = {
                    "body": body,
                    "status": response.status_code,
                    "headers": dict(response.headers),
                    "time": time.time(),
                }

                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                )
            except Exception as e:
                logger.error(f"Cache error: {e}")
                return response

        return response
