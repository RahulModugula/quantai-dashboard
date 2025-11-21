"""Tests for retry mechanism with exponential backoff."""
import pytest

from src.resilience.retry import RetryPolicy, Retry, RetryException, retry


class TestRetryPolicy:
    def test_initial_delay(self):
        policy = RetryPolicy(initial_delay=2.0, jitter=False)
        assert policy.get_delay(0) == 2.0

    def test_exponential_increase(self):
        policy = RetryPolicy(initial_delay=1.0, exponential_base=2.0, jitter=False)
        assert policy.get_delay(0) == 1.0
        assert policy.get_delay(1) == 2.0
        assert policy.get_delay(2) == 4.0

    def test_max_delay_cap(self):
        policy = RetryPolicy(initial_delay=1.0, max_delay=5.0, jitter=False)
        assert policy.get_delay(10) == 5.0


class TestRetryExecutor:
    def test_succeeds_first_try(self):
        executor = Retry(RetryPolicy(max_attempts=3))
        result = executor.execute(lambda: 42)
        assert result == 42

    def test_retries_on_failure(self):
        call_count = 0

        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("not yet")
            return "ok"

        executor = Retry(
            RetryPolicy(max_attempts=3, initial_delay=0.01),
            retryable_exceptions=(ValueError,),
        )
        result = executor.execute(flaky)
        assert result == "ok"
        assert call_count == 3

    def test_raises_after_max_attempts(self):
        executor = Retry(
            RetryPolicy(max_attempts=2, initial_delay=0.01),
            retryable_exceptions=(ValueError,),
        )
        with pytest.raises(RetryException):
            executor.execute(lambda: (_ for _ in ()).throw(ValueError("fail")))

    def test_non_retryable_exception_propagates(self):
        executor = Retry(
            RetryPolicy(max_attempts=3),
            retryable_exceptions=(ValueError,),
        )
        with pytest.raises(TypeError):
            executor.execute(lambda: (_ for _ in ()).throw(TypeError("wrong type")))


class TestRetryDecorator:
    def test_decorator_succeeds(self):
        @retry(max_attempts=3, initial_delay=0.01)
        def works():
            return 42

        assert works() == 42

    def test_decorator_retries(self):
        call_count = 0

        @retry(max_attempts=3, initial_delay=0.01, retryable_exceptions=(ValueError,))
        def flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("retry me")
            return "done"

        assert flaky() == "done"
        assert call_count == 2
