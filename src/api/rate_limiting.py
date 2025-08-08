"""Rate limiting for API endpoints."""
import logging
import time
from collections import defaultdict
from typing import Optional
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, requests_per_minute: int = 60):
        """Initialize rate limiter.

        Args:
            requests_per_minute: Maximum requests per minute
        """
        self.requests_per_minute = requests_per_minute
        self.buckets = defaultdict(lambda: {"tokens": requests_per_minute, "last_update": time.time()})

    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for identifier."""
        bucket = self.buckets[identifier]
        now = time.time()
        elapsed = now - bucket["last_update"]

        # Add tokens based on elapsed time
        tokens_to_add = (elapsed * self.requests_per_minute) / 60
        bucket["tokens"] = min(self.requests_per_minute, bucket["tokens"] + tokens_to_add)
        bucket["last_update"] = now

        if bucket["tokens"] >= 1:
            bucket["tokens"] -= 1
            return True

        return False

    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests for identifier."""
        bucket = self.buckets[identifier]
        return int(bucket["tokens"])


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting."""

    def __init__(self, app, requests_per_minute: int = 60):
        """Initialize middleware."""
        super().__init__(app)
        self.rate_limiter = RateLimiter(requests_per_minute)
        self.excluded_paths = {"/api/health", "/api/version"}

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        if request.url.path in self.excluded_paths:
            return await call_next(request)

        # Use client IP as identifier
        client_ip = request.client.host if request.client else "unknown"
        identifier = f"{client_ip}:{request.url.path}"

        if not self.rate_limiter.is_allowed(identifier):
            logger.warning(f"Rate limit exceeded for {identifier}")
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
            )

        response = await call_next(request)
        remaining = self.rate_limiter.get_remaining(identifier)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response


class EndpointRateLimiter:
    """Per-endpoint rate limiting configuration."""

    def __init__(self):
        self.limits = {}

    def set_limit(self, endpoint: str, requests_per_minute: int):
        """Set rate limit for endpoint."""
        self.limits[endpoint] = requests_per_minute
        logger.info(f"Rate limit set for {endpoint}: {requests_per_minute} req/min")

    def get_limit(self, endpoint: str) -> int:
        """Get rate limit for endpoint."""
        return self.limits.get(endpoint, 60)

    def create_limiter(self, endpoint: str) -> RateLimiter:
        """Create rate limiter for endpoint."""
        limit = self.get_limit(endpoint)
        return RateLimiter(limit)


# Global endpoint rate limiter
_endpoint_limiter = EndpointRateLimiter()


def get_endpoint_limiter() -> EndpointRateLimiter:
    """Get global endpoint rate limiter."""
    return _endpoint_limiter
