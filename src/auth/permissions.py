"""Permission and authorization management."""

from enum import Enum


class Permission(str, Enum):
    """API permissions."""

    READ_PORTFOLIO = "read:portfolio"
    WRITE_PORTFOLIO = "write:portfolio"
    READ_PREDICTIONS = "read:predictions"
    RUN_BACKTEST = "backtest:run"
    ADMIN = "admin"


class Role(str, Enum):
    """User roles."""

    VIEWER = "viewer"
    TRADER = "trader"
    ADMIN = "admin"


ROLE_PERMISSIONS = {
    Role.VIEWER: [Permission.READ_PORTFOLIO, Permission.READ_PREDICTIONS],
    Role.TRADER: [
        Permission.READ_PORTFOLIO,
        Permission.READ_PREDICTIONS,
        Permission.RUN_BACKTEST,
    ],
    Role.ADMIN: [Permission.ADMIN],
}


def has_permission(user_role: Role, required_permission: Permission) -> bool:
    """Check if user has required permission."""
    if user_role == Role.ADMIN:
        return True
    return required_permission in ROLE_PERMISSIONS.get(user_role, [])
