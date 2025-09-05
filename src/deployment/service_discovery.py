"""Service discovery and registration."""
import logging
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceStatus(str, Enum):
    """Service status values."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class ServiceInstance:
    """Registered service instance."""

    def __init__(
        self,
        name: str,
        host: str,
        port: int,
        metadata: Dict = None,
    ):
        """Initialize service instance.

        Args:
            name: Service name
            host: Service host
            port: Service port
            metadata: Additional metadata
        """
        self.name = name
        self.host = host
        self.port = port
        self.metadata = metadata or {}
        self.status = ServiceStatus.UNKNOWN
        self.registered_at = datetime.now()
        self.last_heartbeat = datetime.now()
        self.health_check_interval = 30  # seconds

    def get_url(self) -> str:
        """Get service URL."""
        return f"http://{self.host}:{self.port}"

    def is_healthy(self) -> bool:
        """Check if service is healthy."""
        return self.status == ServiceStatus.HEALTHY

    def update_heartbeat(self):
        """Update last heartbeat."""
        self.last_heartbeat = datetime.now()

    def is_stale(self, timeout: int = 60) -> bool:
        """Check if service heartbeat is stale."""
        elapsed = (datetime.now() - self.last_heartbeat).total_seconds()
        return elapsed > timeout

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "url": self.get_url(),
            "status": self.status.value,
            "metadata": self.metadata,
            "registered_at": self.registered_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
        }


class ServiceRegistry:
    """Registry for service discovery."""

    def __init__(self):
        """Initialize service registry."""
        self.services: Dict[str, List[ServiceInstance]] = {}

    def register(self, instance: ServiceInstance):
        """Register a service instance."""
        if instance.name not in self.services:
            self.services[instance.name] = []

        self.services[instance.name].append(instance)
        logger.info(
            f"Service registered: {instance.name} at {instance.get_url()}"
        )

    def deregister(self, name: str, host: str, port: int):
        """Deregister a service instance."""
        if name not in self.services:
            return

        self.services[name] = [
            s for s in self.services[name]
            if not (s.host == host and s.port == port)
        ]

        if not self.services[name]:
            del self.services[name]

        logger.info(f"Service deregistered: {name} from {host}:{port}")

    def get_service(self, name: str) -> Optional[ServiceInstance]:
        """Get a healthy instance of service."""
        if name not in self.services:
            return None

        # Return first healthy instance
        for instance in self.services[name]:
            if instance.is_healthy():
                return instance

        # Return first available if none healthy
        if self.services[name]:
            return self.services[name][0]

        return None

    def get_all_instances(self, name: str) -> List[ServiceInstance]:
        """Get all instances of service."""
        return self.services.get(name, [])

    def get_healthy_instances(self, name: str) -> List[ServiceInstance]:
        """Get all healthy instances of service."""
        if name not in self.services:
            return []

        return [s for s in self.services[name] if s.is_healthy()]

    def update_status(self, name: str, host: str, port: int, status: ServiceStatus):
        """Update service instance status."""
        if name not in self.services:
            return

        for instance in self.services[name]:
            if instance.host == host and instance.port == port:
                instance.status = status
                instance.update_heartbeat()
                logger.info(f"Service status updated: {name} -> {status.value}")
                break

    def heartbeat(self, name: str, host: str, port: int):
        """Record heartbeat for service instance."""
        if name not in self.services:
            return

        for instance in self.services[name]:
            if instance.host == host and instance.port == port:
                instance.update_heartbeat()
                if instance.status == ServiceStatus.UNKNOWN:
                    instance.status = ServiceStatus.HEALTHY
                break

    def cleanup_stale(self, timeout: int = 60):
        """Remove stale service instances."""
        removed = []

        for name, instances in list(self.services.items()):
            stale = [s for s in instances if s.is_stale(timeout)]

            for instance in stale:
                instances.remove(instance)
                removed.append(f"{name} at {instance.get_url()}")
                logger.warning(
                    f"Removed stale service: {name} from {instance.host}:{instance.port}"
                )

            if not instances:
                del self.services[name]

        return removed

    def get_service_catalog(self) -> Dict:
        """Get complete service catalog."""
        catalog = {}

        for name, instances in self.services.items():
            catalog[name] = {
                "instances": len(instances),
                "healthy": len([s for s in instances if s.is_healthy()]),
                "services": [s.to_dict() for s in instances],
            }

        return catalog

    def get_health_summary(self) -> dict:
        """Get health summary."""
        total_instances = sum(
            len(instances) for instances in self.services.values()
        )
        healthy_instances = sum(
            len([s for s in instances if s.is_healthy()])
            for instances in self.services.values()
        )

        return {
            "total_services": len(self.services),
            "total_instances": total_instances,
            "healthy_instances": healthy_instances,
            "health_percent": round(
                (healthy_instances / total_instances * 100) if total_instances > 0 else 0,
                2
            ),
        }


# Global service registry
_registry = ServiceRegistry()


def get_registry() -> ServiceRegistry:
    """Get global service registry."""
    return _registry


def register_service(name: str, host: str, port: int, metadata: Dict = None):
    """Register a service instance."""
    registry = get_registry()
    instance = ServiceInstance(name, host, port, metadata)
    registry.register(instance)
    return instance
