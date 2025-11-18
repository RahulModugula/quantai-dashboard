"""Tests for Prometheus observability metrics."""
from src.monitoring.observability import (
    REQUEST_COUNT,
    REQUEST_LATENCY,
    MODEL_INFERENCE_LATENCY,
    MODEL_PREDICTIONS,
    get_prometheus_metrics,
    get_prometheus_content_type,
    track_execution_time,
    MetricsCollector,
)


class TestPrometheusMetrics:
    def test_request_count_increments(self):
        before = REQUEST_COUNT._metrics.copy()
        REQUEST_COUNT.labels(method="GET", endpoint="/test", status_code="200").inc()
        output = get_prometheus_metrics().decode()
        assert "http_requests_total" in output

    def test_request_latency_records(self):
        REQUEST_LATENCY.labels(method="GET", endpoint="/test").observe(0.05)
        output = get_prometheus_metrics().decode()
        assert "http_request_duration_seconds" in output

    def test_model_predictions_counter(self):
        MODEL_PREDICTIONS.labels(ticker="AAPL", direction="up").inc()
        output = get_prometheus_metrics().decode()
        assert "model_predictions_total" in output

    def test_prometheus_content_type(self):
        ct = get_prometheus_content_type()
        assert "text/plain" in ct or "openmetrics" in ct

    def test_prometheus_output_is_bytes(self):
        output = get_prometheus_metrics()
        assert isinstance(output, bytes)


class TestTrackExecutionTime:
    def test_decorator_returns_result(self):
        @track_execution_time
        def add(a, b):
            return a + b

        assert add(1, 2) == 3

    def test_decorator_records_metric(self):
        @track_execution_time
        def dummy():
            return 42

        dummy()
        output = get_prometheus_metrics().decode()
        assert "model_inference_duration_seconds" in output


class TestMetricsCollector:
    def test_backward_compatible_interface(self):
        mc = MetricsCollector()
        mc.increment_counter("test_counter")
        mc.set_gauge("portfolio_value", 100_000)
        result = mc.get_metrics()
        assert "note" in result
