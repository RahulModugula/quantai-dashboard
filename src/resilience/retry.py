"""Retry mechanism with exponential backoff."""
import logging
import time
import asyncio
from typing import Callable, Any, Type, Tuple
from functools import wraps

logger = logging.getLogger(__name__)


class RetryException(Exception):
    """Exception raised when all retry attempts fail."""

    def __init__(self, message: str, last_exception: Exception = None):
        """Initialize retry exception."""
        self.message = message
        self.last_exception = last_exception
        super().__init__(message)


class RetryPolicy:
    """Retry policy with exponential backoff."""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        """Initialize retry policy.

        Args:
            max_attempts: Maximum number of attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Whether to add random jitter
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for attempt."""
        delay = self.initial_delay * (self.exponential_base ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            import random
            delay *= random.uniform(0.5, 1.5)

        return delay

    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """Check if should retry."""
        return attempt < self.max_attempts


class Retry:
    """Retry executor with exponential backoff."""

    def __init__(
        self,
        policy: RetryPolicy = None,
        retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
    ):
        """Initialize retry executor.

        Args:
            policy: Retry policy
            retryable_exceptions: Exceptions that trigger retry
        """
        self.policy = policy or RetryPolicy()
        self.retryable_exceptions = retryable_exceptions

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retries."""
        last_exception = None

        for attempt in range(self.policy.max_attempts):
            try:
                return func(*args, **kwargs)
            except self.retryable_exceptions as e:
                last_exception = e

                if not self.policy.should_retry(attempt, e):
                    logger.error(
                        f"Max retries exceeded for {func.__name__}: {str(e)}"
                    )
                    raise RetryException(
                        f"Failed after {self.policy.max_attempts} attempts",
                        last_exception,
                    )

                delay = self.policy.get_delay(attempt)
                logger.warning(
                    f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                    f"Retrying in {delay:.2f}s"
                )
                time.sleep(delay)

        raise RetryException(
            f"Failed after {self.policy.max_attempts} attempts",
            last_exception,
        )

    async def execute_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function with retries."""
        last_exception = None

        for attempt in range(self.policy.max_attempts):
            try:
                return await func(*args, **kwargs)
            except self.retryable_exceptions as e:
                last_exception = e

                if not self.policy.should_retry(attempt, e):
                    logger.error(
                        f"Max retries exceeded for {func.__name__}: {str(e)}"
                    )
                    raise RetryException(
                        f"Failed after {self.policy.max_attempts} attempts",
                        last_exception,
                    )

                delay = self.policy.get_delay(attempt)
                logger.warning(
                    f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. "
                    f"Retrying in {delay:.2f}s"
                )
                await asyncio.sleep(delay)

        raise RetryException(
            f"Failed after {self.policy.max_attempts} attempts",
            last_exception,
        )


def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
):
    """Decorator to add retry logic to function."""

    def decorator(func: Callable) -> Callable:
        policy = RetryPolicy(max_attempts=max_attempts, initial_delay=initial_delay)
        executor = Retry(policy, retryable_exceptions)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return executor.execute(func, *args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await executor.execute_async(func, *args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# Default retry policy
DEFAULT_POLICY = RetryPolicy(max_attempts=3, initial_delay=1.0, max_delay=30.0)


def create_retry_executor(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    retryable_exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Retry:
    """Create a retry executor with custom parameters."""
    policy = RetryPolicy(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
    )
    return Retry(policy, retryable_exceptions)
