"""Configuration manager - Centralized facade for all configuration loading."""

from pathlib import Path
from typing import Dict, Any
from config import Config
from .loaders import BaseLoader, AgentLoader, AppLoader, DirectoryLoader, EnvironmentLoader


class ConfigManager:
    """Manages persistent configuration settings - Facade for specialized loaders"""

    def __init__(self):
        self._config_file = Path(Config.BASE_DIR) / "config" / "app_config.json"
        self._base_loader = BaseLoader(str(self._config_file))
        self._environment_loader = EnvironmentLoader()
        self._cached_config = None

    def load_config(self) -> Dict[str, Any]:
        """Load configuration using base loader"""
        if self._cached_config is None:
            self._cached_config = self._base_loader.get_config_data()
            if not self._cached_config:
                self._cached_config = self._get_default_config()
        return self._cached_config

    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration using base loader"""
        self._cached_config = None  # Clear cache
        return self._base_loader.save_config(config)

    def get_agent_config(self, agent_type: str = None) -> Dict[str, Any]:
        """Get agent configuration using AgentLoader"""
        config = self.load_config()
        agent_loader = AgentLoader(config)
        return agent_loader.get_agent_config(agent_type) if agent_type else agent_loader.get_all_agents_config()

    def get_app_config(self) -> Dict[str, Any]:
        """Get application configuration using AppLoader"""
        config = self.load_config()
        app_loader = AppLoader(config)
        return {
            "app": app_loader.get_app_settings(),
            "session": app_loader.get_session_settings(),
            "safety": app_loader.get_safety_settings(),
            "logging": app_loader.get_logging_settings()
        }

    def get_directory_config(self) -> Dict[str, Any]:
        """Get directory configuration using DirectoryLoader"""
        config = self.load_config()
        directory_loader = DirectoryLoader(config)
        return directory_loader.get_all_directories()

    def get_environment_config(self) -> Dict[str, Any]:
        """Get environment configuration using EnvironmentLoader"""
        return self._environment_loader.get_all_api_keys()

    def update_model_config(self,
                          therapist_model: str,
                          therapist_provider: str,
                          supervisor_model: str,
                          supervisor_provider: str) -> bool:
        """Update model configuration in app_config.json"""
        config = self.load_config()

        # Update providers section
        if "providers" not in config:
            config["providers"] = {}

        config["providers"]["therapist"] = {
            "provider": therapist_provider,
            "model": therapist_model
        }
        config["providers"]["supervisor"] = {
            "provider": supervisor_provider,
            "model": supervisor_model
        }

        return self.save_config(config)

    def update_audio_config(self, enabled: bool, tts_config: Dict[str, Any] = None) -> bool:
        """Update audio configuration in app_config.json"""
        config = self.load_config()

        # Initialize audio section if not exists
        if "audio" not in config:
            config["audio"] = {"enabled": False, "tts_config": {}}

        # Update audio settings
        config["audio"]["enabled"] = enabled

        if tts_config:
            # Don't save API key for security
            safe_tts_config = {k: v for k, v in tts_config.items() if k != "api_key"}
            config["audio"]["tts_config"].update(safe_tts_config)

        return self.save_config(config)

    def get_audio_config(self) -> Dict[str, Any]:
        """Get audio configuration from app_config.json"""
        config = self.load_config()
        return config.get("audio", {"enabled": False, "tts_config": {}})

    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """Get default configuration values from template file"""
        import json
        from pathlib import Path

        try:
            template_path = Path("config/templates/defaults/app_config_default.json")
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load default config template: {e}")

        # Fallback to minimal config if template loading fails
        return {
            "app": {
                "title": "Psychia - TSR Therapy Assistant",
                "icon": "🧠",
                "language": "pl"
            },
            "directories": {
                "data_dir": "./data",
                "prompt_dir": "./config/prompts",
                "stages_dir": "./config/stages"
            }
        }