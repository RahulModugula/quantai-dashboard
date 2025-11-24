"""Useful decorators for trading application."""

import functools
import logging
import time

logger = logging.getLogger(__name__)


def timer(func):
    """Decorator to measure function execution time."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.debug(f"{func.__name__} took {elapsed:.3f}s")
        return result

    return wrapper


def retry(max_attempts: int = 3, delay: float = 1.0):
    """Decorator to retry function on failure.

    Args:
        max_attempts: Maximum number of attempts
        delay: Delay between attempts in seconds
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(delay)

        return wrapper

    return decorator


def log_calls(func):
    """Decorator to log function calls and returns."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        logger.info(f"{func.__name__} returned {result}")
        return result

    return wrapper


def validate_input(**validators):
    """Decorator to validate function inputs.

    Example:
        @validate_input(ticker=lambda x: len(x) <= 5)
        def predict(ticker):
            pass
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for key, validator in validators.items():
                if key in kwargs and not validator(kwargs[key]):
                    raise ValueError(f"Invalid {key}: {kwargs[key]}")
            return func(*args, **kwargs)

        return wrapper

    return decorator
