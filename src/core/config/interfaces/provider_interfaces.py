"""Segregated interfaces for provider configuration following ISP."""

from abc import ABC, abstractmethod
from typing import List, Optional
from ..domain import ProviderType, ProviderCredentials, ProviderConfiguration, AgentProviderMapping


class ICredentialsProvider(ABC):
    """Interface for providing LLM provider credentials."""

    @abstractmethod
    def get_credentials(self, provider: ProviderType) -> Optional[ProviderCredentials]:
        """Get credentials for specified provider."""
        pass

    @abstractmethod
    def has_credentials(self, provider: ProviderType) -> bool:
        """Check if credentials exist for provider."""
        pass


class IProviderConfigurationBuilder(ABC):
    """Interface for building provider configurations."""

    @abstractmethod
    def build_configuration(
        self, provider: ProviderType, model: str, credentials: ProviderCredentials
    ) -> ProviderConfiguration:
        """Build complete provider configuration."""
        pass

    @abstractmethod
    def build_agent_mapping(
        self, agent_type: str, provider_config: ProviderConfiguration
    ) -> AgentProviderMapping:
        """Build agent to provider mapping."""
        pass

    def build_agent_configuration(self, agent_type) -> ProviderConfiguration:
        """Build configuration for specific agent type."""
        pass


class IProviderValidator(ABC):
    """Interface for validating provider configurations."""

    @abstractmethod
    def validate_credentials(self, credentials: ProviderCredentials) -> bool:
        """Validate provider credentials."""
        pass

    @abstractmethod
    def validate_configuration(self, config: ProviderConfiguration) -> bool:
        """Validate complete provider configuration."""
        pass

    def get_validation_errors(self, config) -> List[str]:
        """Get validation errors for a given configuration."""
        pass

    def validate_agent_configuration(self, agent_type, config) -> bool:
        """Validate configuration for a specific agent type."""
        pass


class IProviderDiscovery(ABC):
    """Interface for discovering available providers."""

    @abstractmethod
    def get_available_providers(self) -> List[ProviderType]:
        """Get list of available providers with valid credentials."""
        pass

    @abstractmethod
    def get_supported_providers(self) -> List[ProviderType]:
        """Get list of all supported provider types."""
        pass

    def get_provider_status(self) -> dict:
        """Get comprehensive status of all providers."""
        pass
