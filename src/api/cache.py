"""
Caching utilities for API responses.
"""
import logging
from functools import wraps
from typing import Any, Callable, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheEntry:
    """Simple cache entry with TTL."""

    def __init__(self, value: Any, ttl_seconds: int = 300):
        self.value = value
        self.created_at = datetime.now()
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed > self.ttl_seconds


class SimpleCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self):
        self._cache: dict[str, CacheEntry] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if entry.is_expired():
            del self._cache[key]
            logger.debug(f"Cache hit for {key} (expired, removed)")
            return None

        logger.debug(f"Cache hit for {key}")
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Set value in cache with TTL."""
        self._cache[key] = CacheEntry(value, ttl_seconds)
        logger.debug(f"Cache set for {key} with TTL {ttl_seconds}s")

    def invalidate(self, key: str) -> None:
        """Remove entry from cache."""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache invalidated for {key}")

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        logger.debug("Cache cleared")

    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)


# Global cache instance
_api_cache = SimpleCache()


def cache_response(ttl_seconds: int = 300) -> Callable:
    """Decorator to cache function responses."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached = _api_cache.get(cache_key)
            if cached is not None:
                return cached

            # Call function and cache result
            result = func(*args, **kwargs)
            _api_cache.set(cache_key, result, ttl_seconds)
            return result

        return wrapper

    return decorator


def get_cache() -> SimpleCache:
    """Get the global cache instance."""
    return _api_cache
