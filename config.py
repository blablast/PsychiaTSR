"""Clean configuration facade - eliminates anti-patterns using ConfigurationManager."""

from pathlib import Path
from typing import Dict, Any, Optional

from src.core.config.configuration_manager import ConfigurationManager


class Config:
    """
    Clean configuration facade using proper separation of concerns.

    Eliminates anti-patterns by:
    - No global state or module-level execution
    - Lazy loading with proper initialization
    - Testable with dependency injection
    - Single responsibility delegated to ConfigurationManager
    """

    _instance: Optional['Config'] = None
    _config_manager: Optional[ConfigurationManager] = None

    def __new__(cls):
        """Singleton pattern for configuration access."""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize configuration facade."""
        if self._config_manager is None:
            self._config_manager = ConfigurationManager()

    @classmethod
    def initialize(cls, config_file_path: Optional[str] = None) -> 'Config':
        """
        Initialize configuration with custom file path.

        Args:
            config_file_path: Path to configuration file (optional)

        Returns:
            Config instance
        """
        instance = cls()
        instance._config_manager = ConfigurationManager(config_file_path)
        instance._config_manager.load_configuration()
        return instance

    @classmethod
    def get_instance(cls) -> 'Config':
        """Get configuration instance (creates with defaults if not exists)."""
        if cls._instance is None or cls._instance._config_manager is None:
            return cls.initialize()
        return cls._instance

    # =====================================================================================
    # DIRECT ACCESS PROPERTIES (for backwards compatibility)
    # =====================================================================================

    @property
    def OPENAI_API_KEY(self) -> str:
        """Get OpenAI API key."""
        return self._config_manager.get_api_key("openai")

    @property
    def GOOGLE_API_KEY(self) -> str:
        """Get Google API key."""
        return self._config_manager.get_api_key("google")

    @property
    def DEFAULT_THERAPIST_PROVIDER(self) -> str:
        """Get default therapist provider."""
        return self._config_manager.get_agent_provider("therapist")

    @property
    def DEFAULT_THERAPIST_MODEL(self) -> str:
        """Get default therapist model."""
        return self._config_manager.get_agent_model("therapist")

    @property
    def DEFAULT_SUPERVISOR_PROVIDER(self) -> str:
        """Get default supervisor provider."""
        return self._config_manager.get_agent_provider("supervisor")

    @property
    def DEFAULT_SUPERVISOR_MODEL(self) -> str:
        """Get default supervisor model."""
        return self._config_manager.get_agent_model("supervisor")

    @property
    def DEFAULT_TEMPERATURE(self) -> float:
        """Get default temperature."""
        return self._config_manager.get_agent_parameters("therapist").get("temperature", 0.7)

    @property
    def DEFAULT_MAX_TOKENS(self) -> int:
        """Get default max tokens."""
        return self._config_manager.get_agent_parameters("therapist").get("max_tokens", 150)

    @property
    def DEFAULT_TOP_P(self) -> float:
        """Get default top_p."""
        return self._config_manager.get_agent_parameters("therapist").get("top_p", 0.9)

    @property
    def APP_TITLE(self) -> str:
        """Get application title."""
        return self._config_manager.get_app_title()

    @property
    def APP_ICON(self) -> str:
        """Get application icon."""
        return self._config_manager.get_app_icon()

    @property
    def LOGS_DIR(self) -> str:
        """Get logs directory."""
        return self._config_manager.get_logs_dir()

    @property
    def PROMPT_DIR(self) -> str:
        """Get prompt directory."""
        return self._config_manager.get_prompt_dir()

    @property
    def STAGES_DIR(self) -> str:
        """Get stages directory."""
        return self._config_manager.get_stages_dir()

    @property
    def MAX_THERAPIST_CONTEXT_MESSAGES(self) -> int:
        """Get max therapist context messages."""
        return self._config_manager.get_max_therapist_context_messages()

    @property
    def MAX_SUPERVISOR_CONTEXT_MESSAGES(self) -> int:
        """Get max supervisor context messages."""
        return self._config_manager.get_max_supervisor_context_messages()

    @property
    def ENABLE_CONVERSATION_SUMMARY(self) -> bool:
        """Check if conversation summary is enabled."""
        return self._config_manager.is_conversation_summary_enabled()

    @property
    def CONTEXT_COMPRESSION_THRESHOLD(self) -> int:
        """Get context compression threshold."""
        return self._config_manager.get_context_compression_threshold()

    # =====================================================================================
    # DELEGATE METHODS
    # =====================================================================================

    def get_llm_config(self, provider: str, agent_type: str = None) -> Dict[str, Any]:
        """Get LLM configuration for provider and agent."""
        return self._config_manager.get_llm_config(provider, agent_type)

    def get_agent_parameters(self, agent_type: str) -> Dict[str, Any]:
        """Get parameters for agent."""
        return self._config_manager.get_agent_parameters(agent_type)

    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """Get complete configuration for agent."""
        return self._config_manager.get_agent_config(agent_type)

    def get_agent_defaults(self) -> Dict[str, Any]:
        """Get default configuration for all agents."""
        return self._config_manager.get_all_agents_config()

    def ensure_directories(self) -> None:
        """Ensure all directories exist."""
        self._config_manager.ensure_directories()

    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration."""
        validation_result = self._config_manager.validate_configuration()
        return {
            "valid": validation_result.valid,
            "warnings": validation_result.warnings,
            "errors": validation_result.errors
        }

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        return self._config_manager.to_dict()

    def reload_configuration(self) -> bool:
        """Reload configuration from file."""
        return self._config_manager.load_configuration()

    def save_configuration(self, config_data: Optional[Dict[str, Any]] = None) -> bool:
        """Save configuration to file."""
        return self._config_manager.save_configuration(config_data)


# =====================================================================================
# BACKWARDS COMPATIBILITY - Module-level instance
# =====================================================================================

# Create default instance for backwards compatibility
_default_instance = Config.initialize()

# Export properties for backwards compatibility
OPENAI_API_KEY = _default_instance.OPENAI_API_KEY
GOOGLE_API_KEY = _default_instance.GOOGLE_API_KEY
DEFAULT_THERAPIST_PROVIDER = _default_instance.DEFAULT_THERAPIST_PROVIDER
DEFAULT_THERAPIST_MODEL = _default_instance.DEFAULT_THERAPIST_MODEL
DEFAULT_SUPERVISOR_PROVIDER = _default_instance.DEFAULT_SUPERVISOR_PROVIDER
DEFAULT_SUPERVISOR_MODEL = _default_instance.DEFAULT_SUPERVISOR_MODEL
DEFAULT_TEMPERATURE = _default_instance.DEFAULT_TEMPERATURE
DEFAULT_MAX_TOKENS = _default_instance.DEFAULT_MAX_TOKENS
DEFAULT_TOP_P = _default_instance.DEFAULT_TOP_P
APP_TITLE = _default_instance.APP_TITLE
APP_ICON = _default_instance.APP_ICON
LOGS_DIR = _default_instance.LOGS_DIR
PROMPT_DIR = _default_instance.PROMPT_DIR
STAGES_DIR = _default_instance.STAGES_DIR
MAX_THERAPIST_CONTEXT_MESSAGES = _default_instance.MAX_THERAPIST_CONTEXT_MESSAGES
MAX_SUPERVISOR_CONTEXT_MESSAGES = _default_instance.MAX_SUPERVISOR_CONTEXT_MESSAGES
ENABLE_CONVERSATION_SUMMARY = _default_instance.ENABLE_CONVERSATION_SUMMARY
CONTEXT_COMPRESSION_THRESHOLD = _default_instance.CONTEXT_COMPRESSION_THRESHOLD


# Export functions for backwards compatibility
def get_llm_config(provider: str, agent_type: str = None) -> Dict[str, Any]:
    """Get LLM configuration."""
    return _default_instance.get_llm_config(provider, agent_type)


def get_agent_parameters(agent_type: str) -> Dict[str, Any]:
    """Get agent parameters."""
    return _default_instance.get_agent_parameters(agent_type)


def get_agent_config(agent_type: str) -> Dict[str, Any]:
    """Get agent configuration."""
    return _default_instance.get_agent_config(agent_type)


def get_agent_defaults() -> Dict[str, Any]:
    """Get agent defaults."""
    return _default_instance.get_agent_defaults()


def ensure_directories() -> None:
    """Ensure directories exist."""
    _default_instance.ensure_directories()


def validate_config() -> Dict[str, Any]:
    """Validate configuration."""
    return _default_instance.validate_config()


def to_dict() -> Dict[str, Any]:
    """Export configuration."""
    return _default_instance.to_dict()