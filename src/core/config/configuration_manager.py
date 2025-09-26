"""Clean configuration manager - eliminates anti-patterns."""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .loaders.app_loader import AppLoader
from .loaders.agent_loader import AgentLoader
from .loaders.directory_loader import DirectoryLoader
from .loaders.environment_loader import EnvironmentLoader


@dataclass
class ConfigurationValidationResult:
    """Configuration validation result."""

    valid: bool
    warnings: List[str]
    errors: List[str]


class ConfigurationManager:
    """
    Clean configuration manager using proper separation of concerns.

    Eliminates anti-patterns by:
    - Separating loading, validation, and access
    - No global state or module-level execution
    - Testable components with dependency injection
    - Single responsibility per loader
    """

    def __init__(self, config_file_path: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            config_file_path: Path to configuration file (optional)
        """
        self._config_file = self._resolve_config_file(config_file_path)
        self._config_data = {}
        self._is_loaded = False

        # Initialize loaders (lazy initialization)
        self._app_loader = None
        self._agent_loader = None
        self._directory_loader = None
        self._environment_loader = None

    def load_configuration(self) -> bool:
        """
        Load configuration from file.

        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            if self._config_file.exists():
                with open(self._config_file, "r", encoding="utf-8") as f:
                    self._config_data = json.load(f)
            else:
                # Use default configuration
                self._config_data = self._get_default_configuration()

            # Initialize loaders with loaded data
            self._initialize_loaders()
            self._is_loaded = True
            return True

        except Exception as e:
            print(f"Error loading configuration: {e}")
            self._config_data = self._get_default_configuration()
            self._initialize_loaders()
            self._is_loaded = True
            return False

    def save_configuration(self, config_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save configuration to file.

        Args:
            config_data: Configuration data to save (optional, uses current if None)

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            data_to_save = config_data if config_data is not None else self._config_data

            # Ensure parent directory exists
            self._config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)

            # Always reload after saving to ensure consistency
            return self.load_configuration()

        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False

    def validate_configuration(self) -> ConfigurationValidationResult:
        """
        Validate current configuration.

        Returns:
            Validation result with errors and warnings
        """
        if not self._is_loaded:
            self.load_configuration()

        result = ConfigurationValidationResult(valid=True, warnings=[], errors=[])

        # Validate API keys
        if not self.get_api_key("openai") and not self.get_api_key("google"):
            result.errors.append("No API keys configured")
            result.valid = False

        # Validate directories
        try:
            self.ensure_directories()
        except Exception as e:
            result.errors.append(f"Failed to create directories: {e}")
            result.valid = False

        # Validate directory configuration
        if self._directory_loader:
            dir_validation = self._directory_loader.validate_directories()
            result.errors.extend(dir_validation.get("errors", []))
            result.warnings.extend(dir_validation.get("warnings", []))

            if not dir_validation.get("valid", True):
                result.valid = False

        # Check model configurations
        for agent_type in ["therapist", "supervisor"]:
            model = self.get_agent_model(agent_type)
            if not model:
                result.warnings.append(f"No model configured for {agent_type}")

        # Check optional API keys
        if not self.get_api_key("openai"):
            result.warnings.append("OpenAI API key not configured")

        if not self.get_api_key("google"):
            result.warnings.append("Google API key not configured")

        return result

    def ensure_directories(self) -> None:
        """Ensure all configured directories exist."""
        if not self._is_loaded:
            self.load_configuration()

        if self._directory_loader:
            self._directory_loader.ensure_directories_exist()

    # =====================================================================================
    # APPLICATION SETTINGS
    # =====================================================================================

    def get_app_title(self) -> str:
        """Get application title."""
        self._ensure_loaded()
        return (
            self._app_loader.get_app_title()
            if self._app_loader
            else "Psychia - TSR Therapy Assistant"
        )

    def get_app_icon(self) -> str:
        """Get application icon."""
        self._ensure_loaded()
        return self._app_loader.get_app_icon() if self._app_loader else "🧠"

    def get_app_language(self) -> str:
        """Get default application language."""
        self._ensure_loaded()
        return self._app_loader.get_default_language() if self._app_loader else "pl"

    def get_session_timeout(self) -> int:
        """Get session timeout in seconds."""
        self._ensure_loaded()
        return self._app_loader.get_session_timeout() if self._app_loader else 3600

    def get_max_conversation_history(self) -> int:
        """Get maximum conversation history entries."""
        self._ensure_loaded()
        return self._app_loader.get_max_conversation_history() if self._app_loader else 50

    # =====================================================================================
    # AGENT SETTINGS
    # =====================================================================================

    def get_agent_provider(self, agent_type: str) -> str:
        """Get provider for agent."""
        self._ensure_loaded()
        return self._agent_loader.get_agent_provider(agent_type) if self._agent_loader else "openai"

    def get_agent_model(self, agent_type: str) -> str:
        """Get model for agent."""
        self._ensure_loaded()
        return (
            self._agent_loader.get_agent_model(agent_type) if self._agent_loader else "gpt-4o-mini"
        )

    def get_agent_parameters(self, agent_type: str) -> Dict[str, Any]:
        """Get parameters for agent."""
        self._ensure_loaded()
        return (
            self._agent_loader.get_agent_parameters(agent_type)
            if self._agent_loader
            else {"temperature": 0.7, "max_tokens": 150, "top_p": 0.9}
        )

    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """Get complete configuration for agent."""
        return {
            "provider": self.get_agent_provider(agent_type),
            "model": self.get_agent_model(agent_type),
            "parameters": self.get_agent_parameters(agent_type),
        }

    def get_all_agents_config(self) -> Dict[str, Dict[str, Any]]:
        """Get configuration for all agents."""
        return {
            "therapist": self.get_agent_config("therapist"),
            "supervisor": self.get_agent_config("supervisor"),
        }

    # =====================================================================================
    # DIRECTORY SETTINGS
    # =====================================================================================

    def get_logs_dir(self) -> str:
        """Get logs directory."""
        self._ensure_loaded()
        return self._directory_loader.get_logs_dir() if self._directory_loader else "./logs"

    def get_prompt_dir(self) -> str:
        """Get prompts directory."""
        self._ensure_loaded()
        return self._directory_loader.get_prompt_dir() if self._directory_loader else "./config"

    def get_stages_dir(self) -> str:
        """Get stages directory."""
        self._ensure_loaded()
        return self._directory_loader.get_stages_dir() if self._directory_loader else "./config"

    # =====================================================================================
    # ENVIRONMENT SETTINGS
    # =====================================================================================

    def get_api_key(self, provider: str) -> str:
        """Get API key for provider."""
        self._ensure_loaded()
        return self._environment_loader.get_api_key(provider) if self._environment_loader else ""

    def get_all_api_keys(self) -> Dict[str, str]:
        """Get all API keys."""
        self._ensure_loaded()
        return self._environment_loader.get_all_api_keys() if self._environment_loader else {}

    def has_api_key(self, provider: str) -> bool:
        """Check if API key exists for provider."""
        return bool(self.get_api_key(provider))

    def get_configured_providers(self) -> List[str]:
        """Get list of providers with API keys."""
        self._ensure_loaded()
        return (
            self._environment_loader.get_configured_providers() if self._environment_loader else []
        )

    # =====================================================================================
    # LLM CONFIGURATION
    # =====================================================================================

    def get_llm_config(self, provider: str, agent_type: Optional[str] = None) -> Dict[str, Any]:
        """Get LLM configuration for provider and agent."""
        config = {"api_key": self.get_api_key(provider)}

        if agent_type:
            config.update(self.get_agent_parameters(agent_type))
        else:
            # Use default parameters
            config.update({"temperature": 0.7, "max_tokens": 150, "top_p": 0.9})

        return config

    # =====================================================================================
    # MEMORY CONFIGURATION
    # =====================================================================================

    def get_max_therapist_context_messages(self) -> int:
        """Get max therapist context messages."""
        self._ensure_loaded()
        return self._config_data.get("memory", {}).get("max_therapist_messages", 20)

    def get_max_supervisor_context_messages(self) -> int:
        """Get max supervisor context messages."""
        self._ensure_loaded()
        return self._config_data.get("memory", {}).get("max_supervisor_messages", 15)

    def is_conversation_summary_enabled(self) -> bool:
        """Check if conversation summarization is enabled."""
        self._ensure_loaded()
        return self._config_data.get("memory", {}).get("enable_summary", True)

    def get_context_compression_threshold(self) -> int:
        """Get context compression threshold."""
        self._ensure_loaded()
        return self._config_data.get("memory", {}).get("compression_threshold", 100)

    # =====================================================================================
    # EXPORT METHODS
    # =====================================================================================

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        self._ensure_loaded()
        return {
            "app": {
                "title": self.get_app_title(),
                "icon": self.get_app_icon(),
                "language": self.get_app_language(),
            },
            "agents": self.get_all_agents_config(),
            "directories": {
                "logs_dir": self.get_logs_dir(),
                "prompt_dir": self.get_prompt_dir(),
                "stages_dir": self.get_stages_dir(),
            },
            "memory": {
                "max_therapist_messages": self.get_max_therapist_context_messages(),
                "max_supervisor_messages": self.get_max_supervisor_context_messages(),
                "enable_summary": self.is_conversation_summary_enabled(),
                "compression_threshold": self.get_context_compression_threshold(),
            },
            "providers": self.get_configured_providers(),
        }

    # =====================================================================================
    # PRIVATE METHODS
    # =====================================================================================

    def _resolve_config_file(self, config_file_path: Optional[str]) -> Path:
        """Resolve configuration file path."""
        if config_file_path:
            return Path(config_file_path)

        # Default location
        base_dir = Path(__file__).parent.parent.parent.parent
        return base_dir / "config" / "app_config.json"

    def _ensure_loaded(self) -> None:
        """Ensure configuration is loaded."""
        if not self._is_loaded:
            self.load_configuration()

    def _initialize_loaders(self) -> None:
        """Initialize specialized loaders with configuration data."""
        self._app_loader = AppLoader(self._config_data)
        self._agent_loader = AgentLoader(self._config_data)
        self._directory_loader = DirectoryLoader(self._config_data)
        self._environment_loader = EnvironmentLoader()

    def _get_default_configuration(self) -> Dict[str, Any]:
        """Get default configuration structure."""
        return {
            "app": {"title": "Psychia - TSR Therapy Assistant", "icon": "🧠", "language": "pl"},
            "agents": {
                "therapist": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "parameters": {"temperature": 0.7, "max_tokens": 150, "top_p": 0.9},
                },
                "supervisor": {
                    "provider": "gemini",
                    "model": "gemini-1.5-flash",
                    "parameters": {"temperature": 0.7, "max_tokens": 150, "top_p": 0.9},
                },
            },
            "directories": {
                "logs_dir": "./logs",
                "prompt_dir": "./config",
                "stages_dir": "./config",
            },
            "memory": {
                "max_therapist_messages": 20,
                "max_supervisor_messages": 15,
                "enable_summary": True,
                "compression_threshold": 100,
            },
            "session": {"timeout": 3600, "max_history": 50},
            "safety": {"enable_checks": True, "strict_mode": False},
            "logging": {"level": "INFO", "detailed": True},
        }
