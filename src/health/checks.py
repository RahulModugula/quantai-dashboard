"""Health check utilities for production readiness."""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class HealthChecker:
    """Perform system health checks."""

    @staticmethod
    def check_database() -> dict:
        """Check database connectivity."""
        try:
            from src.data.storage import get_engine
            engine = get_engine()
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            return {"status": "healthy", "service": "database"}
        except Exception as e:
            logger.error(f"Database check failed: {e}")
            return {"status": "unhealthy", "service": "database", "error": str(e)}

    @staticmethod
    def check_redis() -> dict:
        """Check Redis connectivity."""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379)
            r.ping()
            return {"status": "healthy", "service": "redis"}
        except Exception as e:
            logger.warning(f"Redis check failed: {e}")
            return {"status": "unhealthy", "service": "redis", "error": str(e)}

    @staticmethod
    def check_model() -> dict:
        """Check ML model availability."""
        try:
            from src.api.dependencies import get_model_bundle
            bundle, meta = get_model_bundle()
            if bundle is None:
                return {"status": "unavailable", "service": "model"}
            return {"status": "healthy", "service": "model"}
        except Exception as e:
            logger.warning(f"Model check failed: {e}")
            return {"status": "unhealthy", "service": "model", "error": str(e)}

    @staticmethod
    def check_data() -> dict:
        """Check data availability."""
        try:
            from src.config import settings
            from src.data.storage import load_ohlcv

            ready_tickers = []
            for ticker in settings.tickers[:3]:
                try:
                    df = load_ohlcv(ticker)
                    if not df.empty:
                        ready_tickers.append(ticker)
                except:
                    pass

            status = "healthy" if len(ready_tickers) > 0 else "unavailable"
            return {"status": status, "service": "data", "tickers": len(ready_tickers)}
        except Exception as e:
            logger.warning(f"Data check failed: {e}")
            return {"status": "unhealthy", "service": "data", "error": str(e)}

    @classmethod
    def full_health_check(cls) -> dict:
        """Run all health checks."""
        checks = {
            "database": cls.check_database(),
            "redis": cls.check_redis(),
            "model": cls.check_model(),
            "data": cls.check_data(),
        }

        overall = "healthy" if all(c["status"] in ["healthy", "unavailable"] for c in checks.values()) else "unhealthy"

        return {
            "status": overall,
            "timestamp": datetime.now().isoformat(),
            "checks": checks,
        }
