"""Enhanced API versioning with migration support."""

import logging
from typing import Callable, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class APIVersionState(str, Enum):
    """Version state."""

    BETA = "beta"
    STABLE = "stable"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"


class VersionedEndpoint:
    """Endpoint available in multiple versions."""

    def __init__(self, path: str, versions: List[str]):
        """Initialize versioned endpoint.

        Args:
            path: Endpoint path
            versions: List of API versions that support this endpoint
        """
        self.path = path
        self.versions = versions
        self.deprecated_versions = []
        self.migrations = {}

    def mark_deprecated(self, version: str):
        """Mark version as deprecated."""
        if version in self.versions:
            self.deprecated_versions.append(version)

    def add_migration(self, from_version: str, to_version: str, mapper: Callable):
        """Add data migration between versions."""
        key = f"{from_version}->{to_version}"
        self.migrations[key] = mapper

    def migrate_data(self, from_version: str, to_version: str, data: Dict):
        """Migrate data between versions."""
        key = f"{from_version}->{to_version}"

        if key in self.migrations:
            return self.migrations[key](data)

        return data

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "path": self.path,
            "versions": self.versions,
            "deprecated_versions": self.deprecated_versions,
        }


class VersionManager:
    """Manage API versions and migrations."""

    def __init__(self):
        """Initialize version manager."""
        self.endpoints: Dict[str, VersionedEndpoint] = {}
        self.version_states: Dict[str, APIVersionState] = {}

    def register_endpoint(self, path: str, versions: List[str]) -> VersionedEndpoint:
        """Register a versioned endpoint.

        Args:
            path: Endpoint path
            versions: List of API versions

        Returns:
            Versioned endpoint
        """
        endpoint = VersionedEndpoint(path, versions)
        self.endpoints[path] = endpoint

        logger.info(f"Endpoint registered: {path} for versions {versions}")

        return endpoint

    def set_version_state(self, version: str, state: APIVersionState):
        """Set version state."""
        self.version_states[version] = state

        logger.info(f"Version state set: {version} -> {state.value}")

    def get_version_state(self, version: str) -> Optional[APIVersionState]:
        """Get version state."""
        return self.version_states.get(version)

    def is_version_supported(self, version: str) -> bool:
        """Check if version is supported."""
        state = self.get_version_state(version)

        if not state:
            return False

        return state in (APIVersionState.BETA, APIVersionState.STABLE)

    def migrate_request(self, path: str, from_version: str, to_version: str, data: Dict) -> Dict:
        """Migrate request data between versions."""
        if path not in self.endpoints:
            return data

        endpoint = self.endpoints[path]
        return endpoint.migrate_data(from_version, to_version, data)

    def get_endpoint_versions(self, path: str) -> List[str]:
        """Get versions that support endpoint."""
        if path in self.endpoints:
            return self.endpoints[path].versions

        return []

    def get_active_endpoints(self, version: str) -> List[Dict]:
        """Get all endpoints active in version."""
        endpoints = []

        for endpoint in self.endpoints.values():
            if version in endpoint.versions:
                endpoints.append(endpoint.to_dict())

        return endpoints

    def get_migration_path(self, from_version: str, to_version: str) -> Optional[List[str]]:
        """Get migration path between versions."""
        # Simple path finding: direct or through intermediate versions
        if from_version == to_version:
            return [from_version]

        # Check if direct migration exists
        for endpoint in self.endpoints.values():
            key = f"{from_version}->{to_version}"
            if key in endpoint.migrations:
                return [from_version, to_version]

        # TODO: Implement complex path finding for multiple-step migrations
        return None


# Global version manager
_manager = VersionManager()


def get_manager() -> VersionManager:
    """Get global version manager."""
    return _manager


def register_versioned_endpoint(path: str, versions: List[str]) -> VersionedEndpoint:
    """Register versioned endpoint globally."""
    manager = get_manager()
    return manager.register_endpoint(path, versions)
