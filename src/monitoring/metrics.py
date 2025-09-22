"""System metrics collection and monitoring."""
import time


class MetricsCollector:
    """Collect system and application metrics."""

    def __init__(self):
        self.metrics = {}
        self.start_time = time.time()

    def record_metric(self, name: str, value: float, unit: str = ""):
        """Record a metric value."""
        if name not in self.metrics:
            self.metrics[name] = []
        self.metrics[name].append({
            "value": value,
            "unit": unit,
            "timestamp": time.time(),
        })

    def get_average(self, metric_name: str) -> float:
        """Get average value of a metric."""
        if metric_name not in self.metrics:
            return 0.0
        values = [m["value"] for m in self.metrics[metric_name]]
        return sum(values) / len(values) if values else 0.0

    def get_latest(self, metric_name: str) -> dict:
        """Get latest value of a metric."""
        if metric_name not in self.metrics or not self.metrics[metric_name]:
            return {}
        return self.metrics[metric_name][-1]

    def uptime_seconds(self) -> float:
        """Get uptime in seconds."""
        return time.time() - self.start_time
