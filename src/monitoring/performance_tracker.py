"""Performance tracking and latency monitoring."""
import logging
import time
from typing import Dict, List, Optional
from collections import defaultdict
from statistics import mean, median, stdev
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class LatencyRecord:
    """Record of a single request latency."""

    def __init__(self, endpoint: str, method: str, duration: float, status_code: int):
        """Initialize latency record."""
        self.endpoint = endpoint
        self.method = method
        self.duration = duration
        self.status_code = status_code
        self.timestamp = datetime.now()


class PerformanceTracker:
    """Track and analyze API performance metrics."""

    def __init__(self, window_size: int = 1000):
        """Initialize tracker.

        Args:
            window_size: Maximum number of records to keep in memory
        """
        self.window_size = window_size
        self.records: List[LatencyRecord] = []
        self.endpoint_stats: Dict[str, dict] = defaultdict(lambda: {
            "count": 0,
            "total_time": 0,
            "min": float("inf"),
            "max": 0,
            "errors": 0,
        })

    def record(self, endpoint: str, method: str, duration: float, status_code: int):
        """Record a request latency."""
        record = LatencyRecord(endpoint, method, duration, status_code)
        self.records.append(record)

        # Keep window size manageable
        if len(self.records) > self.window_size:
            self.records.pop(0)

        # Update endpoint statistics
        key = f"{method} {endpoint}"
        stats = self.endpoint_stats[key]
        stats["count"] += 1
        stats["total_time"] += duration
        stats["min"] = min(stats["min"], duration)
        stats["max"] = max(stats["max"], duration)

        if status_code >= 400:
            stats["errors"] += 1

    def get_endpoint_stats(self, endpoint: Optional[str] = None) -> Dict:
        """Get statistics for endpoint(s)."""
        if endpoint:
            return self._calculate_stats_for_endpoint(endpoint)

        # Return all endpoint stats
        result = {}
        for key, stats in self.endpoint_stats.items():
            result[key] = self._format_stats(stats)

        return result

    def _calculate_stats_for_endpoint(self, endpoint: str) -> Dict:
        """Calculate detailed stats for specific endpoint."""
        endpoint_records = [
            r for r in self.records if endpoint in r.endpoint
        ]

        if not endpoint_records:
            return {}

        durations = [r.duration for r in endpoint_records]

        return {
            "count": len(endpoint_records),
            "mean": round(mean(durations), 4),
            "median": round(median(durations), 4),
            "stdev": round(stdev(durations), 4) if len(durations) > 1 else 0,
            "min": round(min(durations), 4),
            "max": round(max(durations), 4),
            "p95": round(sorted(durations)[int(len(durations) * 0.95)], 4),
            "p99": round(sorted(durations)[int(len(durations) * 0.99)], 4),
        }

    def _format_stats(self, stats: dict) -> dict:
        """Format statistics for display."""
        avg = stats["total_time"] / stats["count"] if stats["count"] > 0 else 0
        error_rate = stats["errors"] / stats["count"] if stats["count"] > 0 else 0

        return {
            "requests": stats["count"],
            "avg_time": round(avg, 4),
            "min_time": round(stats["min"], 4),
            "max_time": round(stats["max"], 4),
            "error_rate": round(error_rate * 100, 2),
        }

    def get_slowest_endpoints(self, limit: int = 10) -> List[Dict]:
        """Get slowest endpoints by average latency."""
        stats_list = [
            {"endpoint": key, **self._format_stats(stats)}
            for key, stats in self.endpoint_stats.items()
        ]

        return sorted(
            stats_list, key=lambda x: x["avg_time"], reverse=True
        )[:limit]

    def get_recent_latencies(self, limit: int = 100) -> List[Dict]:
        """Get recent latency records."""
        recent = self.records[-limit:]
        return [
            {
                "endpoint": r.endpoint,
                "method": r.method,
                "duration": round(r.duration, 4),
                "status": r.status_code,
                "timestamp": r.timestamp.isoformat(),
            }
            for r in recent
        ]

    def reset(self):
        """Reset all statistics."""
        self.records = []
        self.endpoint_stats = defaultdict(lambda: {
            "count": 0,
            "total_time": 0,
            "min": float("inf"),
            "max": 0,
            "errors": 0,
        })
        logger.info("Performance statistics reset")


# Global performance tracker
_tracker = PerformanceTracker()


def get_tracker() -> PerformanceTracker:
    """Get global performance tracker."""
    return _tracker


def record_performance(endpoint: str, method: str, duration: float, status_code: int):
    """Record performance metric."""
    tracker = get_tracker()
    tracker.record(endpoint, method, duration, status_code)
