"""Dependency injection container."""
import logging
from typing import Any, Callable, Dict, Optional, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class Container:
    """Dependency injection container."""

    def __init__(self):
        """Initialize container."""
        self.services: Dict[str, Any] = {}
        self.factories: Dict[str, Callable] = {}
        self.singletons: Dict[str, Any] = {}

    def register(self, name: str, service: Any, singleton: bool = False):
        """Register a service.

        Args:
            name: Service name
            service: Service instance or factory
            singleton: Whether service is singleton
        """
        self.services[name] = service

        if singleton:
            self.singletons[name] = service

        logger.info(f"Service registered: {name} (singleton={singleton})")

    def register_factory(self, name: str, factory: Callable, singleton: bool = False):
        """Register a factory function.

        Args:
            name: Service name
            factory: Factory function
            singleton: Whether to cache result
        """
        self.factories[name] = factory

        logger.info(f"Factory registered: {name} (singleton={singleton})")

    def get(self, name: str, *args, **kwargs) -> Any:
        """Get a service.

        Args:
            name: Service name
            args: Positional arguments for factory
            kwargs: Keyword arguments for factory

        Returns:
            Service instance
        """
        # Check singleton cache first
        if name in self.singletons:
            return self.singletons[name]

        # Check registered services
        if name in self.services:
            service = self.services[name]

            # If it's callable and not registered as singleton
            if callable(service) and name not in self.singletons:
                return service(*args, **kwargs)

            return service

        # Check factories
        if name in self.factories:
            factory = self.factories[name]
            result = factory(*args, **kwargs)

            # Cache singleton factories
            if name in [k for k, v in self.services.items() if v == factory]:
                self.singletons[name] = result

            return result

        raise ValueError(f"Service not found: {name}")

    def has(self, name: str) -> bool:
        """Check if service exists."""
        return name in self.services or name in self.factories

    def list_services(self) -> list:
        """List all registered services."""
        return sorted(list(self.services.keys()) + list(self.factories.keys()))

    def clear(self):
        """Clear all services."""
        self.services.clear()
        self.factories.clear()
        self.singletons.clear()

        logger.info("Container cleared")


class ServiceProvider:
    """Base class for service providers."""

    def register(self, container: Container):
        """Register services with container."""
        raise NotImplementedError

    def boot(self, container: Container):
        """Boot services after registration."""
        pass


class ApplicationContainer:
    """Application-wide dependency injection container."""

    def __init__(self):
        """Initialize application container."""
        self.container = Container()
        self.providers = []

    def register_provider(self, provider: ServiceProvider):
        """Register a service provider."""
        self.providers.append(provider)

        logger.info(f"Service provider registered: {provider.__class__.__name__}")

    def boot(self):
        """Boot all services."""
        for provider in self.providers:
            provider.register(self.container)

        for provider in self.providers:
            provider.boot(self.container)

        logger.info("Application container booted")

    def get(self, name: str, *args, **kwargs) -> Any:
        """Get a service from container."""
        return self.container.get(name, *args, **kwargs)

    def has(self, name: str) -> bool:
        """Check if service exists."""
        return self.container.has(name)

    def list_services(self) -> list:
        """List all services."""
        return self.container.list_services()


# Global application container
_app_container = ApplicationContainer()


def get_container() -> ApplicationContainer:
    """Get global application container."""
    return _app_container


def register_service(name: str, service: Any, singleton: bool = False):
    """Register a service globally."""
    container = get_container()
    container.container.register(name, service, singleton)


def get_service(name: str, *args, **kwargs) -> Any:
    """Get a service globally."""
    container = get_container()
    return container.get(name, *args, **kwargs)


def boot_container():
    """Boot the global container."""
    container = get_container()
    container.boot()
