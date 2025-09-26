"""Configuration interface for dependency injection."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class IConfiguration(ABC):
    """Interface for configuration management.

    This interface allows services to depend on configuration without
    creating circular dependencies. Different implementations can provide
    configuration from files, environment variables, or other sources.
    """

    @property
    @abstractmethod
    def LOGS_DIR(self) -> str:
        """Get logs directory path."""
        pass

    @property
    @abstractmethod
    def PROMPTS_DIR(self) -> str:
        """Get prompts directory path."""
        pass

    @property
    @abstractmethod
    def STAGES_DIR(self) -> str:
        """Get stages directory path."""
        pass

    @property
    @abstractmethod
    def CONFIG_DIR(self) -> str:
        """Get config directory path."""
        pass

    @abstractmethod
    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """Get configuration for a specific agent type.

        Args:
            agent_type: Type of agent (e.g., 'therapist', 'supervisor')

        Returns:
            Dictionary containing agent-specific configuration

        Raises:
            ValueError: If agent_type is not found in configuration
        """
        pass

    @abstractmethod
    def get_llm_config(self, provider_name: str) -> Dict[str, Any]:
        """Get LLM provider configuration.

        Args:
            provider_name: Name of the LLM provider (e.g., 'openai', 'gemini')

        Returns:
            Dictionary containing provider-specific configuration

        Raises:
            ValueError: If provider is not configured
        """
        pass

    @abstractmethod
    def get_api_key(self, service_name: str) -> Optional[str]:
        """Get API key for external service.

        Args:
            service_name: Name of the external service

        Returns:
            API key if configured, None otherwise
        """
        pass

    @abstractmethod
    def get_app_settings(self) -> Dict[str, Any]:
        """Get general application settings.

        Returns:
            Dictionary containing app title, language, theme, etc.
        """
        pass

    @abstractmethod
    def get_directory_paths(self) -> Dict[str, str]:
        """Get all configured directory paths.

        Returns:
            Dictionary mapping directory names to their paths
        """
        pass

    @abstractmethod
    def reload(self) -> bool:
        """Reload configuration from source.

        Returns:
            True if reload was successful, False otherwise
        """
        pass
