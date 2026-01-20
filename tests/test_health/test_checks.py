"""Tests for health check utilities."""

from src.health.checks import HealthChecker


class TestHealthChecker:
    def test_full_health_check_returns_required_keys(self):
        result = HealthChecker.full_health_check()
        assert "status" in result
        assert "timestamp" in result
        assert "checks" in result

    def test_full_health_check_includes_all_services(self):
        result = HealthChecker.full_health_check()
        checks = result["checks"]
        assert "database" in checks
        assert "redis" in checks
        assert "model" in checks
        assert "data" in checks

    def test_each_check_has_status_and_service(self):
        result = HealthChecker.full_health_check()
        for name, check in result["checks"].items():
            assert "status" in check, f"{name} missing status"
            assert "service" in check, f"{name} missing service"

    def test_database_check_returns_dict(self):
        result = HealthChecker.check_database()
        assert isinstance(result, dict)
        assert result["service"] == "database"

    def test_redis_check_graceful_when_unavailable(self):
        """Redis check should return degraded, not crash."""
        result = HealthChecker.check_redis()
        assert result["status"] in ("healthy", "degraded", "unhealthy")

    def test_model_check_returns_status(self):
        result = HealthChecker.check_model()
        assert result["status"] in ("healthy", "unavailable", "unhealthy")

    def test_overall_status_is_valid(self):
        result = HealthChecker.full_health_check()
        assert result["status"] in ("healthy", "unhealthy")
