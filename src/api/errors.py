"""Enhanced error responses with actionable hints for users."""

import logging

logger = logging.getLogger(__name__)


class APIErrorWithHints:
    """Build error responses with helpful debugging hints."""

    @staticmethod
    def no_model() -> dict:
        """Error when no trained model is available."""
        return {
            "status_code": 503,
            "detail": "No trained model available.",
            "hints": [
                "1. Run: python -m scripts.train_model",
                "2. Check QUANTAI_DATA_DIR for feature files",
                "3. Ensure seed_data.py has been run first",
            ],
            "doc": "https://github.com/example/profile-max#training",
        }

    @staticmethod
    def no_feature_data(ticker: str) -> dict:
        """Error when ticker has no feature data."""
        return {
            "status_code": 404,
            "detail": f"No feature data for {ticker}.",
            "hints": [
                f"1. Run: python -m scripts.seed_data --ticker {ticker}",
                "2. Check API status at GET /api/status/data",
                "3. Ensure raw price data exists in QUANTAI_DATA_DIR",
            ],
            "doc": "https://github.com/example/profile-max#data-setup",
        }

    @staticmethod
    def invalid_config() -> dict:
        """Error when configuration is invalid."""
        return {
            "status_code": 400,
            "detail": "Configuration validation failed.",
            "hints": [
                "1. Check ensemble_weights sum to 1.0",
                "2. Verify buy_threshold > sell_threshold",
                "3. Run: GET /api/diagnostics/validate-config",
                "4. Edit .env file and restart API",
            ],
            "doc": ".env.example",
        }

    @staticmethod
    def data_stale(days_old: int, max_days: int = 7) -> dict:
        """Error when data is too stale."""
        return {
            "status_code": 410,
            "detail": f"Data is {days_old} days old (max: {max_days} days).",
            "hints": [
                "1. Download latest market data",
                "2. Run: python -m scripts.seed_data",
                "3. Check internet connection if auto-fetch is enabled",
                "4. Verify QUANTAI_DATA_DIR has write permissions",
            ],
            "doc": "Check GET /api/status/data for freshness",
        }

    @staticmethod
    def invalid_parameter(param: str, reason: str) -> dict:
        """Error for invalid request parameter."""
        return {
            "status_code": 400,
            "detail": f"Invalid parameter '{param}': {reason}",
            "hints": [
                f"1. Check valid range for {param}",
                "2. Ensure ticker symbols are uppercase (e.g., AAPL)",
                "3. Verify date format is YYYY-MM-DD",
                "4. Check API docs at GET /api/docs",
            ],
            "doc": "See endpoint documentation for parameter specs",
        }

    @staticmethod
    def redis_unavailable() -> dict:
        """Error when Redis cache is unavailable."""
        return {
            "status_code": 503,
            "detail": "Cache service unavailable.",
            "hints": [
                "1. API can continue without Redis (slower)",
                "2. Start Redis: redis-server",
                "3. Check QUANTAI_REDIS_URL in .env",
                "4. Verify network connectivity to Redis host",
            ],
            "recovery": "API will fallback to in-memory cache",
        }

    @staticmethod
    def backtest_error(reason: str) -> dict:
        """Error during backtest execution."""
        return {
            "status_code": 400,
            "detail": f"Backtest failed: {reason}",
            "hints": [
                "1. Check start_date < end_date",
                "2. Ensure at least 100 days of data",
                "3. Verify ticker symbols exist",
                "4. Check QUANTAI_MIN_SAMPLES setting",
            ],
            "doc": "GET /api/diagnostics/validate-config",
        }

    @staticmethod
    def insufficient_capital(required: float, available: float) -> dict:
        """Error when insufficient capital for operation."""
        return {
            "status_code": 400,
            "detail": f"Insufficient capital. Required: ${required:.2f}, Available: ${available:.2f}",
            "hints": [
                f"1. Deposit more capital (need ${required - available:.2f} more)",
                "2. Reduce position size",
                "3. Check for open positions requiring margin",
                "4. Review commission costs",
            ],
            "doc": "Portfolio management guide",
        }
