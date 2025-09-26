"""Configuration manager - Legacy wrapper for backwards compatibility."""

from typing import Dict, Any
from .configuration_manager import ConfigurationManager


class ConfigManager:
    """Legacy configuration manager - delegates to new ConfigurationManager."""

    def __init__(self, config_file_path: str = None):
        """Initialize with ConfigurationManager."""
        self._config_manager = ConfigurationManager(config_file_path)
        self._config_manager.load_configuration()

    def load_config(self) -> Dict[str, Any]:
        """Load configuration."""
        return self._config_manager.to_dict()

    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration."""
        return self._config_manager.save_configuration(config)

    def get_agent_config(self, agent_type: str = None) -> Dict[str, Any]:
        """Get agent configuration."""
        if agent_type:
            return self._config_manager.get_agent_config(agent_type)
        else:
            return self._config_manager.get_all_agents_config()

    def reload_config(self) -> bool:
        """Reload configuration."""
        return self._config_manager.load_configuration()

    def get_directory_config(self) -> Dict[str, str]:
        """Get directory configuration."""
        return {
            "logs_dir": self._config_manager.get_logs_dir(),
            "prompt_dir": self._config_manager.get_prompt_dir(),
            "stages_dir": self._config_manager.get_stages_dir(),
        }

    def get_app_config(self) -> Dict[str, Any]:
        """Get application configuration."""
        return {
            "title": self._config_manager.get_app_title(),
            "icon": self._config_manager.get_app_icon(),
            "language": self._config_manager.get_app_language(),
        }

    def get_environment_config(self) -> Dict[str, Any]:
        """Get environment configuration."""
        return self._config_manager.get_all_api_keys()

    def update_model_config(
        self,
        therapist_model: str,
        therapist_provider: str,
        supervisor_model: str,
        supervisor_provider: str,
    ) -> bool:
        """Update model configuration in app_config.json"""
        config_dict = self._config_manager.to_dict()

        # Update agents section
        config_dict["agents"]["therapist"]["provider"] = therapist_provider
        config_dict["agents"]["therapist"]["model"] = therapist_model
        config_dict["agents"]["supervisor"]["provider"] = supervisor_provider
        config_dict["agents"]["supervisor"]["model"] = supervisor_model

        return self._config_manager.save_configuration(config_dict)

    def update_audio_config(self, enabled: bool, tts_config: Dict[str, Any] = None) -> bool:
        """Update audio configuration in app_config.json"""
        config_dict = self._config_manager.to_dict()

        # Initialize audio section if not exists
        if "audio" not in config_dict:
            config_dict["audio"] = {"enabled": False, "tts_config": {}}

        # Update audio settings
        config_dict["audio"]["enabled"] = enabled

        if tts_config:
            # Don't save API key for security
            safe_tts_config = {k: v for k, v in tts_config.items() if k != "api_key"}
            config_dict["audio"]["tts_config"].update(safe_tts_config)

        return self._config_manager.save_configuration(config_dict)

    def get_audio_config(self) -> Dict[str, Any]:
        """Get audio configuration from app_config.json"""
        config_dict = self._config_manager.to_dict()
        return config_dict.get("audio", {"enabled": False, "tts_config": {}})

    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """Get default configuration values from template file"""
        import json
        from pathlib import Path

        try:
            template_path = Path("config/templates/defaults/app_config_default.json")
            if template_path.exists():
                with open(template_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load default config template: {e}")

        # Fallback to minimal config if template loading fails
        return {
            "app": {"title": "Psychia - TSR Therapy Assistant", "icon": "🧠", "language": "pl"},
            "directories": {
                "logs_dir": "./logs",
                "prompt_dir": "./config/prompts",
                "stages_dir": "./config",
            },
        }
