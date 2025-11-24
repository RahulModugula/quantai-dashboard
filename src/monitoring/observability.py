"""Prometheus metrics for request tracking, model inference, and predictions."""

import time
from functools import wraps

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST


# Request metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

# Model metrics
MODEL_INFERENCE_LATENCY = Histogram(
    "model_inference_duration_seconds",
    "Model inference latency in seconds",
    ["model_name"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5],
)
MODEL_PREDICTIONS = Counter(
    "model_predictions_total",
    "Total model predictions",
    ["ticker", "direction"],
)
MODEL_CONFIDENCE = Histogram(
    "model_prediction_confidence",
    "Distribution of model prediction confidence scores",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

# Portfolio metrics
PORTFOLIO_VALUE = Gauge(
    "portfolio_total_value",
    "Current portfolio total value in USD",
)
PORTFOLIO_DRAWDOWN = Gauge(
    "portfolio_current_drawdown",
    "Current portfolio drawdown percentage",
)

# Data pipeline metrics
DATA_FETCH_LATENCY = Histogram(
    "data_fetch_duration_seconds",
    "Data fetching latency in seconds",
    ["source"],
)
DATA_FETCH_ERRORS = Counter(
    "data_fetch_errors_total",
    "Total data fetch errors",
    ["source", "error_type"],
)


def get_prometheus_metrics() -> bytes:
    """Generate Prometheus-compatible metrics output."""
    return generate_latest()


def get_prometheus_content_type() -> str:
    """Return the Prometheus content type header."""
    return CONTENT_TYPE_LATEST


def track_execution_time(func):
    """Decorator to track function execution time as a Prometheus histogram."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start
            MODEL_INFERENCE_LATENCY.labels(model_name=func.__name__).observe(duration)

    return wrapper


# Backward-compatible interface
class MetricsCollector:
    """Thin wrapper around Prometheus metrics for backward compatibility."""

    def increment_counter(self, name: str, value: float = 1.0):
        REQUEST_COUNT.labels(method="internal", endpoint=name, status_code="200").inc(value)

    def set_gauge(self, name: str, value: float):
        PORTFOLIO_VALUE.set(value)

    def get_metrics(self) -> dict:
        return {"note": "Use /api/metrics/prometheus for Prometheus-format metrics"}


_metrics = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    return _metrics
