"""Dependency Injection Container implementation."""

import inspect
from typing import TypeVar, Type, Callable, Any, Optional, Dict
from .container_interface import IDependencyContainer, ServiceLifetime

T = TypeVar("T")


class ServiceRegistration:
    """Represents a service registration entry in the DI container.

    Contains all information needed to create an instance of a registered
    service including its type, implementation, factory, or instance.

    Attributes:
        service_type: The interface or abstract type being registered
        implementation: Concrete implementation class (optional)
        factory: Factory function for creating instances (optional)
        instance: Pre-created instance for singleton services (optional)
        lifetime: Service lifetime management strategy
    """

    def __init__(
        self,
        service_type: Type,
        implementation: Type = None,
        factory: Callable = None,
        instance: Any = None,
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    ):
        """Initialize service registration.

        Args:
            service_type: The service interface or type to register
            implementation: Concrete implementation class
            factory: Factory function for instance creation
            instance: Pre-created instance for singletons
            lifetime: Service lifetime strategy (transient/scoped/singleton)
        """
        self.service_type = service_type
        self.implementation = implementation
        self.factory = factory
        self.instance = instance
        self.lifetime = lifetime


class DependencyContainer(IDependencyContainer):
    """Simple dependency injection container implementation.

    Provides service registration, resolution, and lifetime management
    with support for hierarchical container scoping.

    Features:
    - Service registration by type, factory, or instance
    - Automatic dependency injection via constructor inspection
    - Singleton, scoped, and transient lifetimes
    - Hierarchical container scoping
    """

    def __init__(self, parent: Optional["DependencyContainer"] = None):
        """Initialize dependency container.

        Args:
            parent: Optional parent container for hierarchical resolution
        """
        self._services: Dict[Type, ServiceRegistration] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scoped_instances: Dict[Type, Any] = {}
        self._parent = parent

    def register(
        self,
        service_type: Type[T],
        implementation: Type[T],
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    ) -> None:
        """Register a service implementation for a given service type.

        Args:
            service_type: The service interface or abstract type
            implementation: Concrete implementation class
            lifetime: Service lifetime management strategy
        """
        self._services[service_type] = ServiceRegistration(
            service_type=service_type, implementation=implementation, lifetime=lifetime
        )

    def register_instance(self, service_type: Type[T], instance: T) -> None:
        """Register a specific instance for a service type (singleton).

        Args:
            service_type: The service interface or type
            instance: Pre-created instance to register
        """
        self._services[service_type] = ServiceRegistration(
            service_type=service_type, instance=instance, lifetime=ServiceLifetime.SINGLETON
        )
        self._singletons[service_type] = instance

    def register_factory(
        self,
        service_type: Type[T],
        factory: Callable[[], T],
        lifetime: ServiceLifetime = ServiceLifetime.TRANSIENT,
    ) -> None:
        """Register a factory function for creating service instances.

        Args:
            service_type: The service interface or type
            factory: Factory function that creates instances
            lifetime: Service lifetime management strategy
        """
        self._services[service_type] = ServiceRegistration(
            service_type=service_type, factory=factory, lifetime=lifetime
        )

    def resolve(self, service_type: Type[T]) -> T:
        """Resolve a service instance by its type.

        Args:
            service_type: The service type to resolve

        Returns:
            Instance of the requested service

        Raises:
            ValueError: If service type is not registered
        """
        instance = self.try_resolve(service_type)
        if instance is None:
            raise ValueError(f"Service {service_type.__name__} is not registered")
        return instance

    def try_resolve(self, service_type: Type[T]) -> Optional[T]:
        """Try to resolve a service, returning None if not found.

        Args:
            service_type: The service type to resolve

        Returns:
            Instance of the requested service, or None if not registered
        """
        # Check local registrations first
        if service_type in self._services:
            return self._create_instance(service_type)

        # Check parent container if exists
        if self._parent:
            return self._parent.try_resolve(service_type)

        return None

    def is_registered(self, service_type: Type[T]) -> bool:
        """Check if a service type is registered.

        Args:
            service_type: The service type to check

        Returns:
            True if service is registered, False otherwise
        """
        if service_type in self._services:
            return True
        if self._parent:
            return self._parent.is_registered(service_type)
        return False

    def create_scope(self) -> "DependencyContainer":
        """Create a new scoped container for scoped service management.

        Returns:
            New container with this container as parent
        """
        return DependencyContainer(parent=self)

    def _create_instance(self, service_type: Type[T]) -> T:
        """Create an instance of the specified service type.

        Args:
            service_type: The service type to instantiate

        Returns:
            New or cached instance based on lifetime strategy
        """
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
        """Build an instance from registration.

        Args:
            registration: Service registration containing creation info

        Returns:
            New service instance

        Raises:
            ValueError: If instance cannot be created from registration
        """
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
        """Instantiate a class with automatic dependency injection.

        Uses constructor inspection to automatically resolve and inject
        dependencies based on type annotations.

        Args:
            implementation_type: The class type to instantiate

        Returns:
            New instance with dependencies injected

        Raises:
            ValueError: If required dependencies cannot be resolved
        """
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
                    raise ValueError(
                        f"Cannot resolve dependency {param.annotation.__name__} for {implementation_type.__name__}"
                    )
            elif param.default != inspect.Parameter.empty:
                # Skip parameters with defaults (like logger=None)
                continue

        return implementation_type(*args)
