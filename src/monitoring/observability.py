"""Observability and metrics collection."""
import time
from functools import wraps


class MetricsCollector:
    """Collect application metrics."""

    def __init__(self):
        self.metrics = {}

    def increment_counter(self, name: str, value: float = 1.0):
        """Increment a counter metric."""
        if name not in self.metrics:
            self.metrics[name] = {"type": "counter", "value": 0}
        self.metrics[name]["value"] += value

    def set_gauge(self, name: str, value: float):
        """Set a gauge metric."""
        self.metrics[name] = {"type": "gauge", "value": value}

    def get_metrics(self) -> dict:
        """Get all metrics."""
        return self.metrics


# Global metrics collector
_metrics = MetricsCollector()


def track_execution_time(func):
    """Decorator to track function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start
            _metrics.set_gauge(f"{func.__name__}_duration_ms", duration * 1000)
            _metrics.increment_counter(f"{func.__name__}_calls")
            return result
        except Exception:
            _metrics.increment_counter(f"{func.__name__}_errors")
            raise
    return wrapper


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector."""
    return _metrics
