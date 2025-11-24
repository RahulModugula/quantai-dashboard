"""Feature flags for gradual rollout of new functionality."""

import logging
from typing import Dict, Set, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class RolloutStrategy(str, Enum):
    """Feature rollout strategies."""

    ALL_USERS = "all_users"
    PERCENTAGE = "percentage"
    WHITELIST = "whitelist"
    BETA = "beta"


class FeatureFlag:
    """Single feature flag with rollout control."""

    def __init__(
        self,
        name: str,
        enabled: bool = False,
        strategy: RolloutStrategy = RolloutStrategy.ALL_USERS,
        percentage: int = 100,
        whitelist: Optional[Set[str]] = None,
    ):
        """Initialize feature flag.

        Args:
            name: Feature name
            enabled: Whether feature is enabled
            strategy: Rollout strategy
            percentage: Percentage of users (for percentage strategy)
            whitelist: Whitelisted users (for whitelist strategy)
        """
        self.name = name
        self.enabled = enabled
        self.strategy = strategy
        self.percentage = percentage
        self.whitelist = whitelist or set()
        self.created_at = datetime.now()
        self.last_modified = datetime.now()

    def is_enabled_for_user(self, user_id: str) -> bool:
        """Check if feature is enabled for user."""
        if not self.enabled:
            return False

        if self.strategy == RolloutStrategy.ALL_USERS:
            return True

        if self.strategy == RolloutStrategy.WHITELIST:
            return user_id in self.whitelist

        if self.strategy == RolloutStrategy.PERCENTAGE:
            # Simple hash-based percentage rollout
            user_hash = hash(user_id) % 100
            return user_hash < self.percentage

        if self.strategy == RolloutStrategy.BETA:
            return user_id in self.whitelist

        return False

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "strategy": self.strategy.value,
            "percentage": self.percentage,
            "whitelist_size": len(self.whitelist),
            "created_at": self.created_at.isoformat(),
            "last_modified": self.last_modified.isoformat(),
        }


class FeatureFlagManager:
    """Manage application feature flags."""

    def __init__(self):
        """Initialize feature flag manager."""
        self.flags: Dict[str, FeatureFlag] = {}
        self._setup_default_flags()

    def _setup_default_flags(self):
        """Setup default feature flags."""
        # Model features
        self.register_flag("ENABLE_LSTM_MODEL", enabled=True)
        self.register_flag("ENABLE_ENSEMBLE", enabled=True)
        self.register_flag("ENABLE_XGBOOST", enabled=True)

        # Data features
        self.register_flag("ENABLE_INTRADAY_DATA", enabled=False)
        self.register_flag("ENABLE_CRYPTO", enabled=False)
        self.register_flag("ENABLE_FOREX", enabled=False)

        # Trading features
        self.register_flag("ENABLE_MARGIN_TRADING", enabled=False)
        self.register_flag("ENABLE_OPTIONS", enabled=False)
        self.register_flag("ENABLE_SHORTING", enabled=False)

        # API features
        self.register_flag("ENABLE_WEBHOOKS", enabled=False)
        self.register_flag("ENABLE_REAL_TIME_PRICES", enabled=False)
        self.register_flag("ENABLE_STREAMING_API", enabled=False)

        # Dashboard features
        self.register_flag("ENABLE_ADVANCED_CHARTS", enabled=True)
        self.register_flag("ENABLE_CUSTOM_INDICATORS", enabled=False)
        self.register_flag("ENABLE_STRATEGY_BUILDER", enabled=False)

    def register_flag(
        self,
        name: str,
        enabled: bool = False,
        strategy: RolloutStrategy = RolloutStrategy.ALL_USERS,
        **kwargs,
    ) -> FeatureFlag:
        """Register a new feature flag."""
        flag = FeatureFlag(name, enabled, strategy, **kwargs)
        self.flags[name] = flag
        logger.info(f"Feature flag registered: {name} (enabled={enabled})")
        return flag

    def get_flag(self, name: str) -> Optional[FeatureFlag]:
        """Get feature flag by name."""
        return self.flags.get(name)

    def is_enabled(self, name: str, user_id: str = None) -> bool:
        """Check if feature is enabled."""
        flag = self.get_flag(name)
        if not flag:
            logger.warning(f"Unknown feature flag: {name}")
            return False

        if user_id:
            return flag.is_enabled_for_user(user_id)

        return flag.enabled

    def enable_flag(self, name: str):
        """Enable a feature flag."""
        flag = self.get_flag(name)
        if flag:
            flag.enabled = True
            flag.last_modified = datetime.now()
            logger.info(f"Feature flag enabled: {name}")

    def disable_flag(self, name: str):
        """Disable a feature flag."""
        flag = self.get_flag(name)
        if flag:
            flag.enabled = False
            flag.last_modified = datetime.now()
            logger.info(f"Feature flag disabled: {name}")

    def set_percentage(self, name: str, percentage: int):
        """Set rollout percentage."""
        if not (0 <= percentage <= 100):
            raise ValueError("Percentage must be between 0 and 100")

        flag = self.get_flag(name)
        if flag:
            flag.percentage = percentage
            flag.last_modified = datetime.now()
            logger.info(f"Feature {name} rollout set to {percentage}%")

    def get_all_flags(self) -> Dict[str, dict]:
        """Get all feature flags."""
        return {name: flag.to_dict() for name, flag in self.flags.items()}

    def get_user_features(self, user_id: str) -> Dict[str, bool]:
        """Get features enabled for user."""
        return {name: flag.is_enabled_for_user(user_id) for name, flag in self.flags.items()}


# Global feature flag manager
_manager = FeatureFlagManager()


def get_feature_manager() -> FeatureFlagManager:
    """Get global feature flag manager."""
    return _manager


def is_feature_enabled(feature_name: str, user_id: str = None) -> bool:
    """Check if feature is enabled."""
    manager = get_feature_manager()
    return manager.is_enabled(feature_name, user_id)


# Legacy API for backward compatibility
class FeatureFlags:
    """Centralized feature flag management (legacy API)."""

    @classmethod
    def is_enabled(cls, feature_name: str) -> bool:
        """Check if a feature is enabled."""
        return is_feature_enabled(feature_name)

    @classmethod
    def enable_feature(cls, feature_name: str):
        """Enable a feature dynamically."""
        manager = get_feature_manager()
        manager.enable_flag(feature_name)

    @classmethod
    def disable_feature(cls, feature_name: str):
        """Disable a feature dynamically."""
        manager = get_feature_manager()
        manager.disable_flag(feature_name)
