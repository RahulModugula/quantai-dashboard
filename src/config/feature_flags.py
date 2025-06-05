"""Feature flags for gradual rollout of new functionality."""


class FeatureFlags:
    """Centralized feature flag management."""

    # Model features
    ENABLE_LSTM_MODEL = True
    ENABLE_ENSEMBLE = True
    ENABLE_XGBOOST = True

    # Data features
    ENABLE_INTRADAY_DATA = False
    ENABLE_CRYPTO = False
    ENABLE_FOREX = False

    # Trading features
    ENABLE_MARGIN_TRADING = False
    ENABLE_OPTIONS = False
    ENABLE_SHORTING = False

    # API features
    ENABLE_WEBHOOKS = False
    ENABLE_REAL_TIME_PRICES = False
    ENABLE_STREAMING_API = False

    # Dashboard features
    ENABLE_ADVANCED_CHARTS = True
    ENABLE_CUSTOM_INDICATORS = False
    ENABLE_STRATEGY_BUILDER = False

    @classmethod
    def is_enabled(cls, feature_name: str) -> bool:
        """Check if a feature is enabled."""
        return getattr(cls, feature_name, False)

    @classmethod
    def enable_feature(cls, feature_name: str):
        """Enable a feature dynamically."""
        setattr(cls, feature_name, True)

    @classmethod
    def disable_feature(cls, feature_name: str):
        """Disable a feature dynamically."""
        setattr(cls, feature_name, False)
