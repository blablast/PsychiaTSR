"""Dependency Injection Container interfaces."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import TypeVar, Type, Callable, Optional

T = TypeVar("T")


class ServiceLifetime(Enum):
    """Service lifetime management options."""

    SINGLETON = "singleton"
    TRANSIENT = "transient"
    SCOPED = "scoped"


class IDependencyContainer(ABC):
    """Interface for dependency injection container."""

    @abstractmethod
    def register(
        self,
        service_type: Type[T],
        implementation: Type[T],
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    ) -> None:
        """Register a service implementation for a given service type."""
        pass

    @abstractmethod
    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """Register a specific instance for a service type (singleton)."""
        pass

    @abstractmethod
    def register_factory(
        self,
        service_type: Type[T],
        factory: Callable[[], T],
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    ) -> None:
        """Register a factory function for creating service instances."""
        pass

    @abstractmethod
    def resolve(self, service_type: Type[T]) -> T:
        """Resolve a service instance by its type."""
        pass

    @abstractmethod
    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """Try to resolve a service, returning None if not found."""
        pass

    @abstractmethod
    def is_registered(self, service_type: Type[T]) -> bool:
        """Check if a service type is registered."""
        pass

    @abstractmethod
    def create_scope(self) -> "IDependencyContainer":
        """Create a new scoped container for scoped service management."""
        pass
