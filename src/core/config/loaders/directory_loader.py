"""Directory configuration loader."""

from pathlib import Path
from typing import Dict, Any


class DirectoryLoader:
    """Handles directory configuration and validation."""

    def __init__(self, config_data: Dict[str, Any]):
        """Initialize with configuration data."""
        self._directories_data = config_data.get("directories", {})

    def get_data_dir(self) -> str:
        """Get data directory path."""
        return self._directories_data.get("data_dir", "./data")

    def get_prompt_dir(self) -> str:
        """Get prompts directory path."""
        return self._directories_data.get("prompt_dir", "./config/prompts")

    def get_stages_dir(self) -> str:
        """Get stages directory path."""
        return self._directories_data.get("stages_dir", "./config/stages")

    def get_all_directories(self) -> Dict[str, str]:
        """Get all configured directories."""
        return {
            "data_dir": self.get_data_dir(),
            "prompt_dir": self.get_prompt_dir(),
            "stages_dir": self.get_stages_dir()
        }

    def ensure_directories_exist(self) -> None:
        """Ensure all configured directories exist."""
        directories = self.get_all_directories()

        for dir_name, dir_path in directories.items():
            path = Path(dir_path)
            path.mkdir(parents=True, exist_ok=True)

        # Create additional subdirectories
        data_path = Path(self.get_data_dir())
        (data_path / "sessions").mkdir(exist_ok=True)

    def validate_directories(self) -> Dict[str, Any]:
        """Validate directory configuration."""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        directories = self.get_all_directories()

        for dir_name, dir_path in directories.items():
            path = Path(dir_path)

            try:
                # Try to create the directory
                path.mkdir(parents=True, exist_ok=True)

                # Check if it's writable
                if not path.is_dir():
                    validation_result["errors"].append(f"Directory {dir_name} ({dir_path}) is not accessible")
                    validation_result["valid"] = False
                elif not self._is_writable(path):
                    validation_result["warnings"].append(f"Directory {dir_name} ({dir_path}) may not be writable")

            except Exception as e:
                validation_result["errors"].append(f"Failed to create directory {dir_name} ({dir_path}): {e}")
                validation_result["valid"] = False

        return validation_result

    @staticmethod
    def _is_writable(path: Path) -> bool:
        """Check if directory is writable."""
        try:
            test_file = path / ".write_test"
            test_file.touch()
            test_file.unlink()
            return True
        except Exception:
            return False