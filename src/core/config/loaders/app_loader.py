"""Application settings loader."""

from typing import Dict, Any


class AppLoader:
    """Handles application-level settings."""

    def __init__(self, config_data: Dict[str, Any]):
        """Initialize with configuration data."""
        self._app_data = config_data.get("app", {})
        self._session_data = config_data.get("session", {})
        self._safety_data = config_data.get("safety", {})
        self._logging_data = config_data.get("logging", {})

    def get_app_title(self) -> str:
        """Get application title."""
        return self._app_data.get("title", "Psychia - TSR Therapy Assistant")

    def get_app_icon(self) -> str:
        """Get application icon."""
        return self._app_data.get("icon", "🧠")

    def get_default_language(self) -> str:
        """Get default application language."""
        return self._app_data.get("language", "pl")

    def get_session_timeout(self) -> int:
        """Get session timeout in seconds."""
        return self._session_data.get("timeout", 3600)

    def get_max_conversation_history(self) -> int:
        """Get maximum conversation history entries."""
        return self._session_data.get("max_history", 50)

    def is_safety_enabled(self) -> bool:
        """Check if safety checks are enabled."""
        return self._safety_data.get("enable_checks", True)

    def is_strict_safety_mode(self) -> bool:
        """Check if strict safety mode is enabled."""
        return self._safety_data.get("strict_mode", False)

    def get_log_level(self) -> str:
        """Get logging level."""
        return self._logging_data.get("level", "INFO")

    def is_detailed_logging_enabled(self) -> bool:
        """Check if detailed logging is enabled."""
        return self._logging_data.get("detailed", True)

    def get_app_settings(self) -> Dict[str, Any]:
        """Get all application settings."""
        return {
            "title": self.get_app_title(),
            "icon": self.get_app_icon(),
            "language": self.get_default_language()
        }

    def get_session_settings(self) -> Dict[str, Any]:
        """Get all session settings."""
        return {
            "timeout": self.get_session_timeout(),
            "max_history": self.get_max_conversation_history()
        }

    def get_safety_settings(self) -> Dict[str, Any]:
        """Get all safety settings."""
        return {
            "enable_checks": self.is_safety_enabled(),
            "strict_mode": self.is_strict_safety_mode()
        }

    def get_logging_settings(self) -> Dict[str, Any]:
        """Get all logging settings."""
        return {
            "level": self.get_log_level(),
            "detailed": self.is_detailed_logging_enabled()
        }