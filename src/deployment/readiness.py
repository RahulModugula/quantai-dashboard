"""Deployment readiness checks."""
import logging
from typing import Dict, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class CheckStatus(str, Enum):
    """Check status values."""

    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


class ReadinessCheck:
    """Single readiness check result."""

    def __init__(self, name: str, status: CheckStatus, message: str, details: Dict = None):
        """Initialize check result."""
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


class DeploymentReadinessChecker:
    """Check system readiness for deployment."""

    def __init__(self):
        """Initialize checker."""
        self.checks: List[ReadinessCheck] = []

    def check_python_version(self, required_version: str = "3.11") -> ReadinessCheck:
        """Check Python version."""
        import sys

        version = f"{sys.version_info.major}.{sys.version_info.minor}"
        passed = version.startswith(required_version)

        check = ReadinessCheck(
            "python_version",
            CheckStatus.PASS if passed else CheckStatus.FAIL,
            f"Python {version} (required: {required_version}+)",
            {"version": version, "required": required_version},
        )
        self.checks.append(check)
        return check

    def check_dependencies(self, dependencies: Dict[str, str] = None) -> ReadinessCheck:
        """Check if all dependencies are installed."""
        if dependencies is None:
            dependencies = {
                "fastapi": "0.109.0",
                "pydantic": "2.6.0",
                "sqlalchemy": "2.0.0",
                "pandas": "2.2.0",
            }

        missing = []
        for package, version in dependencies.items():
            try:
                __import__(package)
            except ImportError:
                missing.append(package)

        passed = len(missing) == 0

        check = ReadinessCheck(
            "dependencies",
            CheckStatus.PASS if passed else CheckStatus.FAIL,
            "All dependencies installed" if passed else f"Missing: {', '.join(missing)}",
            {"required": dependencies, "missing": missing},
        )
        self.checks.append(check)
        return check

    def check_configuration(self, required_configs: List[str] = None) -> ReadinessCheck:
        """Check if required configurations are present."""
        if required_configs is None:
            required_configs = [
                "DATABASE_URL",
                "API_KEY",
                "LOG_LEVEL",
            ]

        import os

        missing = [cfg for cfg in required_configs if not os.getenv(cfg)]
        passed = len(missing) == 0

        check = ReadinessCheck(
            "configuration",
            CheckStatus.PASS if passed else CheckStatus.WARN,
            "All configs present" if passed else f"Missing: {', '.join(missing)}",
            {"required": required_configs, "missing": missing},
        )
        self.checks.append(check)
        return check

    def check_database_connection(self, database_url: str = None) -> ReadinessCheck:
        """Check database connectivity."""
        if database_url is None:
            import os
            database_url = os.getenv("DATABASE_URL", "")

        if not database_url:
            check = ReadinessCheck(
                "database_connection",
                CheckStatus.WARN,
                "Database URL not configured",
                {"database_url": "not_set"},
            )
            self.checks.append(check)
            return check

        try:
            from sqlalchemy import create_engine
            engine = create_engine(database_url)
            with engine.connect() as conn:
                conn.execute("SELECT 1")

            check = ReadinessCheck(
                "database_connection",
                CheckStatus.PASS,
                "Database connection successful",
                {"database_type": database_url.split(":")[0]},
            )
        except Exception as e:
            check = ReadinessCheck(
                "database_connection",
                CheckStatus.FAIL,
                f"Database connection failed: {str(e)}",
                {"error": str(e)},
            )

        self.checks.append(check)
        return check

    def check_logging_configuration(self) -> ReadinessCheck:
        """Check logging configuration."""
        import logging

        configured = len(logging.root.handlers) > 0

        check = ReadinessCheck(
            "logging_configuration",
            CheckStatus.PASS if configured else CheckStatus.WARN,
            "Logging configured" if configured else "Logging not configured",
            {"handlers": len(logging.root.handlers)},
        )
        self.checks.append(check)
        return check

    def check_security_settings(self, required_settings: List[str] = None) -> ReadinessCheck:
        """Check security settings."""
        if required_settings is None:
            required_settings = [
                "SECRET_KEY",
                "CORS_ORIGINS",
            ]

        import os

        configured = all(os.getenv(setting) for setting in required_settings)

        check = ReadinessCheck(
            "security_settings",
            CheckStatus.PASS if configured else CheckStatus.WARN,
            "Security settings configured" if configured else "Some settings missing",
            {"required_settings": required_settings},
        )
        self.checks.append(check)
        return check

    def get_report(self) -> Dict:
        """Get deployment readiness report."""
        if not self.checks:
            return {"status": "no_checks", "message": "No checks performed"}

        passed = sum(1 for c in self.checks if c.status == CheckStatus.PASS)
        failed = sum(1 for c in self.checks if c.status == CheckStatus.FAIL)
        warnings = sum(1 for c in self.checks if c.status == CheckStatus.WARN)

        total = len(self.checks)
        ready = failed == 0

        return {
            "ready": ready,
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "status": "ready" if ready else "not_ready",
            "checks": [c.to_dict() for c in self.checks],
        }

    def reset(self):
        """Reset all checks."""
        self.checks = []
        logger.info("Deployment readiness checks reset")


# Global readiness checker
_checker = DeploymentReadinessChecker()


def get_checker() -> DeploymentReadinessChecker:
    """Get global deployment readiness checker."""
    return _checker


def perform_all_checks() -> Dict:
    """Perform all deployment readiness checks."""
    checker = get_checker()
    checker.reset()

    checker.check_python_version()
    checker.check_dependencies()
    checker.check_configuration()
    checker.check_database_connection()
    checker.check_logging_configuration()
    checker.check_security_settings()

    return checker.get_report()
