"""Base configuration loader."""

import json
from pathlib import Path
from typing import Dict, Any


class BaseLoader:
    """Handles loading and parsing of configuration files."""

    def __init__(self, config_file_path: str = None):
        """Initialize with configuration file path."""
        if config_file_path is None:
            base_dir = Path(__file__).parent.parent.parent.parent
            self._config_file = base_dir / "config" / "json" / "app_config.json"
        else:
            self._config_file = Path(config_file_path)

        self._config_data = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        if self._config_file.exists():
            try:
                with open(self._config_file, "r", encoding="utf-8") as f:
                    self._config_data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                raise ValueError(f"Failed to load configuration from {self._config_file}: {e}")
        else:
            raise FileNotFoundError(f"Configuration file not found: {self._config_file}")

    def get_config_data(self) -> Dict[str, Any]:
        """Get the loaded configuration data."""
        return self._config_data.copy()

    def get_section(self, section_name: str) -> Dict[str, Any]:
        """Get a specific configuration section."""
        return self._config_data.get(section_name, {})

    def reload(self) -> None:
        """Reload configuration from file."""
        self._load_config()

    def save_config(self, config_data: Dict[str, Any]) -> bool:
        """Save configuration data to JSON file."""
        try:
            self._config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            self._config_data = config_data.copy()
            return True
        except (IOError, OSError) as e:
            print(f"Failed to save configuration to {self._config_file}: {e}")
            return False
