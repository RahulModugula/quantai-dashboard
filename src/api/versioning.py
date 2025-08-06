"""API versioning and backward compatibility."""
from enum import Enum
from packaging import version


class APIVersion(str, Enum):
    """API versions."""

    V1 = "v1"
    V2 = "v2"


CURRENT_VERSION = APIVersion.V1
SUPPORTED_VERSIONS = {APIVersion.V1, APIVersion.V2}
DEPRECATED_VERSIONS = set()


def is_version_supported(v: str) -> bool:
    """Check if version is supported."""
    try:
        return APIVersion(v) in SUPPORTED_VERSIONS
    except ValueError:
        return False


def is_version_deprecated(v: str) -> bool:
    """Check if version is deprecated."""
    try:
        return APIVersion(v) in DEPRECATED_VERSIONS
    except ValueError:
        return False


def get_version_info() -> dict:
    """Get API version information."""
    return {
        "current": CURRENT_VERSION.value,
        "supported": [v.value for v in SUPPORTED_VERSIONS],
        "deprecated": [v.value for v in DEPRECATED_VERSIONS],
    }
