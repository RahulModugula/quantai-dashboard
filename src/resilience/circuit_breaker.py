"""Circuit breaker pattern for fault tolerance."""
import asyncio
import logging
import time
from typing import Callable, Any
from enum import Enum
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    """Circuit breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker for preventing cascading failures."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        """Initialize circuit breaker.

        Args:
            name: Circuit breaker name
            failure_threshold: Number of failures before opening
            recovery_timeout: Seconds before attempting recovery
            expected_exception: Exception type to catch
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info(f"Circuit {self.name} entering half-open state")
            else:
                raise RuntimeError(f"Circuit {self.name} is open")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 2:
                self._close()

    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self._open()

    def _open(self):
        """Open the circuit."""
        if self.state != CircuitState.OPEN:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit {self.name} opened after {self.failure_count} failures")

    def _close(self):
        """Close the circuit."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        logger.info(f"Circuit {self.name} closed")

    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset."""
        if not self.last_failure_time:
            return True

        elapsed = datetime.now() - self.last_failure_time
        return elapsed.total_seconds() >= self.recovery_timeout

    def get_state(self) -> str:
        """Get current circuit state."""
        return self.state.value

    def get_metrics(self) -> dict:
        """Get circuit metrics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failures": self.failure_count,
            "threshold": self.failure_threshold,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None,
        }


class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""

    def __init__(self):
        """Initialize registry."""
        self.breakers = {}

    def register(self, breaker: CircuitBreaker):
        """Register a circuit breaker."""
        self.breakers[breaker.name] = breaker
        logger.info(f"Circuit breaker registered: {breaker.name}")

    def get(self, name: str) -> CircuitBreaker:
        """Get circuit breaker by name."""
        if name not in self.breakers:
            raise ValueError(f"Unknown circuit breaker: {name}")
        return self.breakers[name]

    def get_all_states(self) -> dict:
        """Get all circuit breaker states."""
        return {name: breaker.get_metrics() for name, breaker in self.breakers.items()}


# Global circuit breaker registry
_registry = CircuitBreakerRegistry()

# Register default circuit breakers
_registry.register(CircuitBreaker("database", failure_threshold=3, recovery_timeout=30))
_registry.register(CircuitBreaker("external_api", failure_threshold=5, recovery_timeout=60))
_registry.register(CircuitBreaker("cache", failure_threshold=10, recovery_timeout=20))


def get_registry() -> CircuitBreakerRegistry:
    """Get global circuit breaker registry."""
    return _registry


def circuit_breaker(name: str = None):
    """Decorator to apply circuit breaker to function."""

    def decorator(func: Callable) -> Callable:
        breaker_name = name or func.__name__
        try:
            breaker = get_registry().get(breaker_name)
        except ValueError:
            breaker = CircuitBreaker(breaker_name)
            get_registry().register(breaker)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper

    return decorator
