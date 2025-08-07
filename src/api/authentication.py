"""Authentication and authorization for API endpoints."""
import logging
from typing import Optional
from datetime import datetime, timedelta
import hashlib
import hmac
from fastapi import HTTPException, Header, Depends
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class TokenPayload(BaseModel):
    """Token payload."""

    api_key: str
    created_at: datetime
    expires_at: Optional[datetime] = None


class AuthenticationManager:
    """Manage API key authentication."""

    def __init__(self):
        self.valid_keys = set()
        self.revoked_keys = set()

    def add_api_key(self, key: str):
        """Add a valid API key."""
        self.valid_keys.add(key)
        logger.info(f"API key added")

    def revoke_api_key(self, key: str):
        """Revoke an API key."""
        if key in self.valid_keys:
            self.valid_keys.remove(key)
            self.revoked_keys.add(key)
            logger.info(f"API key revoked")

    def validate_api_key(self, key: str) -> bool:
        """Validate an API key."""
        if not key:
            return False
        return key in self.valid_keys and key not in self.revoked_keys

    def generate_api_key(self, identifier: str) -> str:
        """Generate a new API key."""
        data = f"{identifier}:{datetime.now().isoformat()}"
        api_key = hashlib.sha256(data.encode()).hexdigest()
        self.add_api_key(api_key)
        return api_key


# Global authentication manager
_auth_manager = AuthenticationManager()


def get_auth_manager() -> AuthenticationManager:
    """Get the global authentication manager."""
    return _auth_manager


async def verify_api_key(x_api_key: str = Header(None)) -> str:
    """Dependency to verify API key from header."""
    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_manager = get_auth_manager()
    if not auth_manager.validate_api_key(x_api_key):
        logger.warning(f"Invalid API key attempt")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return x_api_key


class RoleBasedAccess:
    """Role-based access control."""

    ROLES = {
        "admin": {"read", "write", "delete", "manage_users"},
        "trader": {"read", "write"},
        "viewer": {"read"},
    }

    def __init__(self):
        self.user_roles = {}

    def assign_role(self, user: str, role: str):
        """Assign role to user."""
        if role not in self.ROLES:
            raise ValueError(f"Invalid role: {role}")
        self.user_roles[user] = role
        logger.info(f"Role assigned to user: {role}")

    def has_permission(self, user: str, permission: str) -> bool:
        """Check if user has permission."""
        role = self.user_roles.get(user, "viewer")
        return permission in self.ROLES.get(role, set())

    def require_permission(self, permission: str):
        """Dependency to require specific permission."""

        async def check_permission(api_key: str = Depends(verify_api_key)):
            # In real implementation, extract user from API key
            # For now, check against stored permissions
            user = api_key[:8]  # Placeholder
            if not self.has_permission(user, permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Missing required permission: {permission}",
                )
            return user

        return check_permission


# Global RBAC manager
_rbac = RoleBasedAccess()


def get_rbac() -> RoleBasedAccess:
    """Get the global RBAC manager."""
    return _rbac
