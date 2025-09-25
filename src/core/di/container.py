"""Dependency Injection Container implementation."""

import inspect
from typing import TypeVar, Type, Callable, Any, Optional, Dict
from .container_interface import IDependencyContainer, ServiceLifetime

T = TypeVar('T')


class ServiceRegistration:
    """Represents a service registration entry."""

    def __init__(self, service_type: Type, implementation: Type = None,
                 factory: Callable = None, instance: Any = None,
                 lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT):
        self.service_type = service_type
        self.implementation = implementation
        self.factory = factory
        self.instance = instance
        self.lifetime = lifetime


class DependencyContainer(IDependencyContainer):
    """Simple dependency injection container implementation."""

    def __init__(self, parent: Optional['DependencyContainer'] = None):
        self._services: Dict[Type, ServiceRegistration] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[Type, Any] = {}
        self._parent = parent

    def register(self, service_type: Type[T], implementation: Type[T],
                lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> None:
        """Register a service implementation for a given service type."""
        self._services[service_type] = ServiceRegistration(
            service_type=service_type,
            implementation=implementation,
            lifetime=lifetime
        )

    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """Register a specific instance for a service type (singleton)."""
        self._services[service_type] = ServiceRegistration(
            service_type=service_type,
            instance=instance,
            lifetime=ServiceLifetime.SINGLETON
        )
        self._singletons[service_type] = instance

    def register_factory(self, service_type: Type[T], factory: Callable[[], T],
                         lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT) -> None:
        """Register a factory function for creating service instances."""
        self._services[service_type] = ServiceRegistration(
            service_type=service_type,
            factory=factory,
            lifetime=lifetime
        )

    def resolve(self, service_type: Type[T]) -> T:
        """Resolve a service instance by its type."""
        instance = self.try_resolve(service_type)
        if instance is None:
            raise ValueError(f"Service {service_type.__name__} is not registered")
        return instance

    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """Try to resolve a service, returning None if not found."""
        # Check local registrations first
        if service_type in self._services:
            return self._create_instance(service_type)

        # Check parent container if exists
        if self._parent:
            return self._parent.try_resolve(service_type)

        return None

    def is_registered(self, service_type: Type[T]) -> bool:
        """Check if a service type is registered."""
        if service_type in self._services:
            return True
        if self._parent:
            return self._parent.is_registered(service_type)
        return False

    def create_scope(self) -> 'DependencyContainer':
        """Create a new scoped container for scoped service management."""
        return DependencyContainer(parent=self)

    def _create_instance(self, service_type: Type[T]) -> T:
        """Create an instance of the specified service type."""
        registration = self._services[service_type]

        # Handle singleton lifetime
        if registration.lifetime == ServiceLifetime.SINGLETON:
            if service_type in self._singletons:
                return self._singletons[service_type]

        # Handle scoped lifetime
        elif registration.lifetime == ServiceLifetime.SCOPED:
            if service_type in self._scoped_instances:
                return self._scoped_instances[service_type]

        # Create new instance
        instance = self._build_instance(registration)

        # Store based on lifetime
        if registration.lifetime == ServiceLifetime.SINGLETON:
            self._singletons[service_type] = instance
        elif registration.lifetime == ServiceLifetime.SCOPED:
            self._scoped_instances[service_type] = instance

        return instance

    def _build_instance(self, registration: ServiceRegistration) -> Any:
        """Build an instance from registration."""
        # Use pre-created instance
        if registration.instance is not None:
            return registration.instance

        # Use factory function
        if registration.factory is not None:
            return registration.factory()

        # Use implementation class
        if registration.implementation is not None:
            return self._instantiate_class(registration.implementation)

        raise ValueError(f"Cannot create instance for {registration.service_type.__name__}")

    def _instantiate_class(self, implementation_type: Type) -> Any:
        """Instantiate a class with dependency injection."""
        # Get constructor signature
        signature = inspect.signature(implementation_type.__init__)
        parameters = list(signature.parameters.values())[1:]  # Skip 'self'

        # Resolve dependencies
        args = []
        for param in parameters:
            if param.annotation != inspect.Parameter.empty and param.annotation != str:
                # Skip basic types like str, int, etc.
                dependency = self.try_resolve(param.annotation)
                if dependency is not None:
                    args.append(dependency)
                elif param.default != inspect.Parameter.empty:
                    # Use default value if dependency not found
                    continue
                else:
                    raise ValueError(f"Cannot resolve dependency {param.annotation.__name__} for {implementation_type.__name__}")
            elif param.default != inspect.Parameter.empty:
                # Skip parameters with defaults (like logger=None)
                continue

        return implementation_type(*args)