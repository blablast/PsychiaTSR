"""Configuration persistence manager."""

import json
from pathlib import Path
from typing import Dict, Any
from config import Config


class ConfigManager:
    """Manages persistent configuration settings - simplified for .env + app_config.json setup"""

    def __init__(self):
        self._config_file = Path(Config.BASE_DIR) / "config" / "json" / "app_config.json"

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from app_config.json"""
        if not self._config_file.exists():
            return self._get_default_config()

        try:
            with open(self._config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return self._get_default_config()

    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to app_config.json"""
        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

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

    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """Get default configuration values from app_config.json template"""
        return {
            "providers": {
                "therapist": {
                    "provider": "openai",
                    "model": "gpt-5-nano"
                },
                "supervisor": {
                    "provider": "gemini",
                    "model": "gemini-2.5-flash-lite"
                }
            },
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 150,
                "top_p": 0.9
            },
            "app": {
                "title": "Psychia - TSR Therapy Assistant",
                "icon": "🧠",
                "language": "pl"
            },
            "session": {
                "timeout": 3600,
                "max_history": 50
            },
            "safety": {
                "enable_checks": True,
                "strict_mode": False
            },
            "directories": {
                "data_dir": "./data",
                "prompt_dir": "./prompts",
                "stages_dir": "./stages"
            },
            "logging": {
                "level": "INFO",
                "detailed": True
            }
        }