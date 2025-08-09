"""Caching layer for performance optimization."""
import asyncio
import logging
import time
from typing import Any, Callable, Optional
from collections import OrderedDict
from functools import wraps

logger = logging.getLogger(__name__)


class CacheEntry:
    """Single cache entry with TTL."""

    def __init__(self, value: Any, ttl: Optional[int] = None):
        """Initialize cache entry.

        Args:
            value: Cached value
            ttl: Time to live in seconds (None for no expiration)
        """
        self.value = value
        self.created_at = time.time()
        self.ttl = ttl

    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def get_value(self) -> Optional[Any]:
        """Get value if not expired."""
        if self.is_expired():
            return None
        return self.value


class LRUCache:
    """Least Recently Used cache with TTL support."""

    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = 3600):
        """Initialize LRU cache.

        Args:
            max_size: Maximum number of entries
            default_ttl: Default time to live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self.cache:
            self.misses += 1
            return None

        entry = self.cache[key]
        value = entry.get_value()

        if value is None:
            del self.cache[key]
            self.misses += 1
            return None

        # Move to end (mark as recently used)
        self.cache.move_to_end(key)
        self.hits += 1
        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache."""
        if ttl is None:
            ttl = self.default_ttl

        entry = CacheEntry(value, ttl)
        self.cache[key] = entry

        # Remove least recently used if over capacity
        if len(self.cache) > self.max_size:
            removed_key, _ = self.cache.popitem(last=False)
            logger.debug(f"Evicted cache entry: {removed_key}")

    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        logger.info("Cache cleared")

    def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": round(hit_rate, 2),
        }


# Global cache instance
_cache = LRUCache()


def get_cache() -> LRUCache:
    """Get global cache instance."""
    return _cache


def cache_key(*args, **kwargs) -> str:
    """Generate cache key from function arguments."""
    key_parts = [str(arg) for arg in args]
    key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
    return ":".join(key_parts)


def cached(ttl: Optional[int] = 3600):
    """Decorator to cache function results.

    Args:
        ttl: Time to live in seconds
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            key = f"{func.__name__}:{cache_key(*args, **kwargs)}"
            cache = get_cache()

            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result

            # Call function and cache result
            result = await func(*args, **kwargs)
            cache.set(key, result, ttl)
            logger.debug(f"Cached result for {func.__name__}")
            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            key = f"{func.__name__}:{cache_key(*args, **kwargs)}"
            cache = get_cache()

            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result

            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            logger.debug(f"Cached result for {func.__name__}")
            return result

        # Return async or sync wrapper based on function
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
