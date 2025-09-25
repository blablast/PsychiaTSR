"""Service locator for global access to dependency container."""

from typing import TypeVar, Type, Optional
from .container_interface import IDependencyContainer
from .service_registry import ServiceRegistry

T = TypeVar('T')


class ServiceLocator:
    """Provides global access to the dependency injection container."""

    _container: Optional[IDependencyContainer] = None

    @classmethod
    def initialize(cls) -> None:
        """Initialize the service locator with a configured container."""
        if cls._container is None:
            cls._container = ServiceRegistry.create_configured_container()

    @classmethod
    def get_container(cls) -> IDependencyContainer:
        """Get the global dependency container."""
        if cls._container is None:
            cls.initialize()
        return cls._container

    @classmethod
    def resolve(cls, service_type: Type[T]) -> T:
        """Resolve a service from the global container."""
        return cls.get_container().resolve(service_type)

    @classmethod
    def try_resolve(cls, service_type: Type[T]) -> Optional[T]:
        """Try to resolve a service from the global container."""
        return cls.get_container().try_resolve(service_type)

    @classmethod
    def is_registered(cls, service_type: Type[T]) -> bool:
        """Check if a service is registered in the global container."""
        return cls.get_container().is_registered(service_type)

    @classmethod
    def create_scope(cls) -> IDependencyContainer:
        """Create a new scoped container from the global container."""
        return cls.get_container().create_scope()

    @classmethod
    def reset(cls) -> None:
        """Reset the service locator (mainly for testing)."""
        cls._container = None

    @classmethod
    def set_container(cls, container: IDependencyContainer) -> None:
        """Set a custom container (mainly for testing)."""
        cls._container = container