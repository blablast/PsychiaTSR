"""Configuration adapter for legacy Config class.

This adapter implements IConfiguration interface while delegating
to the existing Config singleton, eliminating circular dependencies.
"""

from typing import Dict, Any, Optional
from ..interfaces.configuration_interface import IConfiguration


class ConfigAdapter(IConfiguration):
    """Adapter that wraps the legacy Config singleton.

    This adapter allows services to depend on IConfiguration interface
    instead of directly importing the Config class, breaking circular dependencies.
    """

    def __init__(self):
        """Initialize adapter.

        Note: Config import is deferred to avoid circular dependencies.
        """
        self._config = None

    def _get_config(self):
        """Get Config instance with lazy loading to avoid circular imports."""
        if self._config is None:
            # Import here to avoid circular dependency
            from config import Config
            self._config = Config.get_instance()
        return self._config

    @property
    def LOGS_DIR(self) -> str:
        """Get logs directory path."""
        return self._get_config().LOGS_DIR

    @property
    def PROMPTS_DIR(self) -> str:
        """Get prompts directory path."""
        return self._get_config().PROMPT_DIR

    @property
    def STAGES_DIR(self) -> str:
        """Get stages directory path."""
        return self._get_config().STAGES_DIR

    @property
    def CONFIG_DIR(self) -> str:
        """Get config directory path (defaults to 'config')."""
        return "config"

    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """Get configuration for a specific agent type.

        Args:
            agent_type: Type of agent (e.g., 'therapist', 'supervisor')

        Returns:
            Dictionary containing agent-specific configuration

        Raises:
            ValueError: If agent_type is not found in configuration
        """
        config = self._get_config()

        # Map to legacy config method names
        if agent_type.lower() == "therapist":
            return {
                "model": config.THERAPIST_MODEL,
                "provider": config.THERAPIST_PROVIDER,
                "temperature": getattr(config, 'THERAPIST_TEMPERATURE', 0.7),
                "max_tokens": getattr(config, 'THERAPIST_MAX_TOKENS', 150)
            }
        elif agent_type.lower() == "supervisor":
            return {
                "model": config.SUPERVISOR_MODEL,
                "provider": config.SUPERVISOR_PROVIDER,
                "temperature": getattr(config, 'SUPERVISOR_TEMPERATURE', 0.3),
                "max_tokens": getattr(config, 'SUPERVISOR_MAX_TOKENS', 100)
            }
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

    def get_llm_config(self, provider_name: str) -> Dict[str, Any]:
        """Get LLM provider configuration.

        Args:
            provider_name: Name of the LLM provider (e.g., 'openai', 'gemini')

        Returns:
            Dictionary containing provider-specific configuration

        Raises:
            ValueError: If provider is not configured
        """
        config = self._get_config()

        if provider_name.lower() == "openai":
            return {
                "api_key": config.OPENAI_API_KEY,
                "base_url": getattr(config, 'OPENAI_BASE_URL', 'https://api.openai.com/v1'),
                "organization": getattr(config, 'OPENAI_ORGANIZATION', None)
            }
        elif provider_name.lower() == "gemini":
            return {
                "api_key": config.GEMINI_API_KEY,
                "base_url": getattr(config, 'GEMINI_BASE_URL', None)
            }
        else:
            raise ValueError(f"Unknown LLM provider: {provider_name}")

    def get_api_key(self, service_name: str) -> Optional[str]:
        """Get API key for external service.

        Args:
            service_name: Name of the external service

        Returns:
            API key if configured, None otherwise
        """
        config = self._get_config()

        # Map service names to config attributes
        key_mapping = {
            "openai": "OPENAI_API_KEY",
            "gemini": "GEMINI_API_KEY"
        }

        attr_name = key_mapping.get(service_name.lower())
        if attr_name:
            return getattr(config, attr_name, None)

        return None

    def get_app_settings(self) -> Dict[str, Any]:
        """Get general application settings.

        Returns:
            Dictionary containing app title, language, theme, etc.
        """
        config = self._get_config()

        return {
            "title": getattr(config, 'APP_TITLE', 'PsychiaTSR'),
            "language": getattr(config, 'APP_LANGUAGE', 'pl'),
            "theme": getattr(config, 'APP_THEME', 'light'),
            "debug": getattr(config, 'DEBUG', False)
        }

    def get_directory_paths(self) -> Dict[str, str]:
        """Get all configured directory paths.

        Returns:
            Dictionary mapping directory names to their paths
        """
        return {
            "logs": self.LOGS_DIR,
            "prompts": self.PROMPTS_DIR,
            "stages": self.STAGES_DIR,
            "config": self.CONFIG_DIR
        }

    def reload(self) -> bool:
        """Reload configuration from source.

        Returns:
            True if reload was successful, False otherwise
        """
        try:
            # Clear cached config to force reload
            self._config = None
            # Access config to trigger reload
            self._get_config()
            return True
        except Exception:
            return False


# Singleton instance for dependency injection
_config_adapter_instance: Optional[ConfigAdapter] = None


def get_config_adapter() -> ConfigAdapter:
    """Get singleton ConfigAdapter instance.

    Returns:
        Singleton ConfigAdapter instance for dependency injection
    """
    global _config_adapter_instance
    if _config_adapter_instance is None:
        _config_adapter_instance = ConfigAdapter()
    return _config_adapter_instance