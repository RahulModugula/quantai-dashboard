"""Multi-tenancy support."""
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TenantPlan(str, Enum):
    """Tenant subscription plans."""

    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class TenantStatus(str, Enum):
    """Tenant status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class Tenant:
    """Tenant/customer."""

    def __init__(self, tenant_id: str, name: str, plan: TenantPlan = TenantPlan.FREE):
        """Initialize tenant.

        Args:
            tenant_id: Unique tenant ID
            name: Tenant name
            plan: Subscription plan
        """
        self.tenant_id = tenant_id
        self.name = name
        self.plan = plan
        self.status = TenantStatus.ACTIVE
        self.created_at = datetime.now()
        self.features: Set[str] = self._get_plan_features(plan)
        self.data_limit_gb = self._get_data_limit(plan)
        self.api_rate_limit = self._get_api_rate_limit(plan)
        self.users: Set[str] = set()
        self.metadata: Dict = {}

    def _get_plan_features(self, plan: TenantPlan) -> Set[str]:
        """Get features for plan."""
        features_map = {
            TenantPlan.FREE: {"basic_analytics", "single_model"},
            TenantPlan.BASIC: {
                "basic_analytics",
                "multiple_models",
                "api_access",
            },
            TenantPlan.PROFESSIONAL: {
                "advanced_analytics",
                "custom_models",
                "api_access",
                "real_time_data",
            },
            TenantPlan.ENTERPRISE: {
                "advanced_analytics",
                "custom_models",
                "api_access",
                "real_time_data",
                "custom_sso",
                "dedicated_support",
            },
        }
        return features_map.get(plan, set())

    def _get_data_limit(self, plan: TenantPlan) -> float:
        """Get data limit for plan."""
        limits = {
            TenantPlan.FREE: 1,
            TenantPlan.BASIC: 10,
            TenantPlan.PROFESSIONAL: 100,
            TenantPlan.ENTERPRISE: float("inf"),
        }
        return limits.get(plan, 1)

    def _get_api_rate_limit(self, plan: TenantPlan) -> int:
        """Get API rate limit for plan."""
        limits = {
            TenantPlan.FREE: 100,
            TenantPlan.BASIC: 1000,
            TenantPlan.PROFESSIONAL: 10000,
            TenantPlan.ENTERPRISE: float("inf"),
        }
        return limits.get(plan, 100)

    def has_feature(self, feature: str) -> bool:
        """Check if tenant has feature."""
        return feature in self.features

    def add_user(self, user_id: str):
        """Add user to tenant."""
        self.users.add(user_id)

    def remove_user(self, user_id: str):
        """Remove user from tenant."""
        self.users.discard(user_id)

    def upgrade_plan(self, new_plan: TenantPlan):
        """Upgrade tenant plan."""
        self.plan = new_plan
        self.features = self._get_plan_features(new_plan)
        self.data_limit_gb = self._get_data_limit(new_plan)
        self.api_rate_limit = self._get_api_rate_limit(new_plan)
        logger.info(f"Tenant upgraded: {self.tenant_id} to {new_plan.value}")

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "plan": self.plan.value,
            "status": self.status.value,
            "features": list(self.features),
            "data_limit_gb": self.data_limit_gb,
            "api_rate_limit": self.api_rate_limit,
            "user_count": len(self.users),
            "created_at": self.created_at.isoformat(),
        }


class TenantManager:
    """Manage tenants."""

    def __init__(self):
        """Initialize tenant manager."""
        self.tenants: Dict[str, Tenant] = {}
        self.user_to_tenant: Dict[str, str] = {}

    def create_tenant(
        self,
        tenant_id: str,
        name: str,
        plan: TenantPlan = TenantPlan.FREE,
    ) -> Tenant:
        """Create a new tenant.

        Args:
            tenant_id: Unique tenant ID
            name: Tenant name
            plan: Subscription plan

        Returns:
            Tenant instance
        """
        if tenant_id in self.tenants:
            raise ValueError(f"Tenant already exists: {tenant_id}")

        tenant = Tenant(tenant_id, name, plan)
        self.tenants[tenant_id] = tenant

        logger.info(f"Tenant created: {tenant_id}")

        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        return self.tenants.get(tenant_id)

    def get_tenant_for_user(self, user_id: str) -> Optional[Tenant]:
        """Get tenant for user."""
        tenant_id = self.user_to_tenant.get(user_id)
        if tenant_id:
            return self.tenants.get(tenant_id)
        return None

    def assign_user_to_tenant(self, user_id: str, tenant_id: str) -> bool:
        """Assign user to tenant."""
        if tenant_id not in self.tenants:
            logger.error(f"Tenant not found: {tenant_id}")
            return False

        tenant = self.tenants[tenant_id]
        tenant.add_user(user_id)
        self.user_to_tenant[user_id] = tenant_id

        logger.info(f"User assigned to tenant: {user_id} -> {tenant_id}")

        return True

    def remove_user_from_tenant(self, user_id: str) -> bool:
        """Remove user from tenant."""
        if user_id not in self.user_to_tenant:
            return False

        tenant_id = self.user_to_tenant[user_id]
        tenant = self.tenants[tenant_id]
        tenant.remove_user(user_id)
        del self.user_to_tenant[user_id]

        logger.info(f"User removed from tenant: {user_id} <- {tenant_id}")

        return True

    def upgrade_tenant(self, tenant_id: str, new_plan: TenantPlan) -> bool:
        """Upgrade tenant plan."""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return False

        tenant.upgrade_plan(new_plan)
        return True

    def suspend_tenant(self, tenant_id: str):
        """Suspend a tenant."""
        tenant = self.get_tenant(tenant_id)
        if tenant:
            tenant.status = TenantStatus.SUSPENDED
            logger.warning(f"Tenant suspended: {tenant_id}")

    def list_tenants(self) -> List[Dict]:
        """List all tenants."""
        return [t.to_dict() for t in self.tenants.values()]

    def get_stats(self) -> dict:
        """Get tenant statistics."""
        return {
            "total_tenants": len(self.tenants),
            "total_users": len(self.user_to_tenant),
            "by_plan": {
                plan.value: len(
                    [t for t in self.tenants.values() if t.plan == plan]
                )
                for plan in TenantPlan
            },
            "by_status": {
                status.value: len(
                    [t for t in self.tenants.values() if t.status == status]
                )
                for status in TenantStatus
            },
        }


# Global tenant manager
_manager = TenantManager()


def get_manager() -> TenantManager:
    """Get global tenant manager."""
    return _manager


def create_tenant(
    tenant_id: str,
    name: str,
    plan: TenantPlan = TenantPlan.FREE,
) -> Tenant:
    """Create tenant globally."""
    manager = get_manager()
    return manager.create_tenant(tenant_id, name, plan)


def get_tenant(tenant_id: str) -> Optional[Tenant]:
    """Get tenant globally."""
    manager = get_manager()
    return manager.get_tenant(tenant_id)
