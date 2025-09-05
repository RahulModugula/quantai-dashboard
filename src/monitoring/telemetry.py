"""Telemetry collection for system monitoring."""
import logging
import psutil
from typing import Dict
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class SystemMetrics:
    """Collect system metrics."""

    def __init__(self, window_size: int = 100):
        """Initialize metrics collector.

        Args:
            window_size: Number of samples to keep
        """
        self.window_size = window_size
        self.cpu_samples = deque(maxlen=window_size)
        self.memory_samples = deque(maxlen=window_size)
        self.disk_samples = deque(maxlen=window_size)

    def collect(self) -> dict:
        """Collect current system metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.cpu_samples.append(cpu_percent)
        except Exception as e:
            logger.warning(f"Failed to collect CPU metrics: {e}")
            cpu_percent = 0

        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.memory_samples.append(memory_percent)
        except Exception as e:
            logger.warning(f"Failed to collect memory metrics: {e}")
            memory_percent = 0
            memory = None

        try:
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent
            self.disk_samples.append(disk_percent)
        except Exception as e:
            logger.warning(f"Failed to collect disk metrics: {e}")
            disk_percent = 0
            disk = None

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "percent": round(cpu_percent, 2),
                "count": psutil.cpu_count(),
            },
            "memory": {
                "percent": round(memory_percent, 2),
                "available": round(memory.available / (1024 ** 3), 2) if memory else 0,
                "used": round(memory.used / (1024 ** 3), 2) if memory else 0,
            } if memory else {},
            "disk": {
                "percent": round(disk_percent, 2),
                "free": round(disk.free / (1024 ** 3), 2) if disk else 0,
                "total": round(disk.total / (1024 ** 3), 2) if disk else 0,
            } if disk else {},
        }

        return metrics

    def get_averages(self) -> dict:
        """Get average metrics over window."""
        def avg(samples):
            return round(sum(samples) / len(samples), 2) if samples else 0

        return {
            "cpu_avg": avg(self.cpu_samples),
            "memory_avg": avg(self.memory_samples),
            "disk_avg": avg(self.disk_samples),
        }

    def get_peaks(self) -> dict:
        """Get peak metrics over window."""
        return {
            "cpu_max": round(max(self.cpu_samples), 2) if self.cpu_samples else 0,
            "memory_max": round(max(self.memory_samples), 2) if self.memory_samples else 0,
            "disk_max": round(max(self.disk_samples), 2) if self.disk_samples else 0,
        }

    def get_report(self) -> dict:
        """Get comprehensive metrics report."""
        current = self.collect()
        averages = self.get_averages()
        peaks = self.get_peaks()

        return {
            "current": current,
            "averages": averages,
            "peaks": peaks,
            "samples": {
                "cpu": len(self.cpu_samples),
                "memory": len(self.memory_samples),
                "disk": len(self.disk_samples),
            },
        }


class ApplicationTelemetry:
    """Collect application telemetry."""

    def __init__(self):
        """Initialize telemetry."""
        self.start_time = datetime.now()
        self.request_count = 0
        self.error_count = 0
        self.total_request_time = 0.0

    def record_request(self, duration: float, success: bool = True):
        """Record request telemetry."""
        self.request_count += 1
        self.total_request_time += duration

        if not success:
            self.error_count += 1

    def get_uptime(self) -> float:
        """Get uptime in seconds."""
        return (datetime.now() - self.start_time).total_seconds()

    def get_stats(self) -> dict:
        """Get application statistics."""
        uptime = self.get_uptime()
        avg_request_time = (
            self.total_request_time / self.request_count
            if self.request_count > 0
            else 0
        )

        error_rate = (
            (self.error_count / self.request_count * 100)
            if self.request_count > 0
            else 0
        )

        requests_per_second = self.request_count / uptime if uptime > 0 else 0

        return {
            "uptime_seconds": round(uptime, 2),
            "total_requests": self.request_count,
            "total_errors": self.error_count,
            "error_rate": round(error_rate, 2),
            "avg_request_time": round(avg_request_time, 4),
            "requests_per_second": round(requests_per_second, 2),
        }


class TelemetryCollector:
    """Unified telemetry collector."""

    def __init__(self):
        """Initialize collector."""
        self.system = SystemMetrics()
        self.application = ApplicationTelemetry()

    def collect_all(self) -> dict:
        """Collect all telemetry."""
        return {
            "timestamp": datetime.now().isoformat(),
            "system": self.system.get_report(),
            "application": self.application.get_stats(),
        }

    def get_health_status(self) -> Dict[str, bool]:
        """Determine health status from telemetry."""
        current_metrics = self.system.collect()
        app_stats = self.application.get_stats()

        return {
            "cpu_healthy": current_metrics["cpu"]["percent"] < 90,
            "memory_healthy": current_metrics["memory"]["percent"] < 85,
            "disk_healthy": current_metrics["disk"]["percent"] < 90,
            "error_rate_healthy": app_stats["error_rate"] < 5,
            "overall_healthy": (
                current_metrics["cpu"]["percent"] < 90
                and current_metrics["memory"]["percent"] < 85
                and current_metrics["disk"]["percent"] < 90
                and app_stats["error_rate"] < 5
            ),
        }


# Global telemetry collector
_collector = TelemetryCollector()


def get_telemetry() -> TelemetryCollector:
    """Get global telemetry collector."""
    return _collector


def record_request(duration: float, success: bool = True):
    """Record request to telemetry."""
    collector = get_telemetry()
    collector.application.record_request(duration, success)
