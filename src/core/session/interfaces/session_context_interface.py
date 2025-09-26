"""Session context interface - decouples core logic from UI framework."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ISessionContext(ABC):
    """Interface for accessing session context (replaces direct Streamlit coupling)."""

    @abstractmethod
    def get_session_value(self, key: str, default: Any = None) -> Any:
        """Get value from session state."""
        pass

    @abstractmethod
    def set_session_value(self, key: str, value: Any) -> None:
        """Set value in session state."""
        pass

    @abstractmethod
    def has_session_value(self, key: str) -> bool:
        """Check if key exists in session state."""
        pass

    @abstractmethod
    def get_session_id(self) -> Optional[str]:
        """Get current session ID."""
        pass

    @abstractmethod
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get conversation messages."""
        pass

    @abstractmethod
    def add_message(self, message: Dict[str, Any]) -> None:
        """Add message to conversation."""
        pass

    @abstractmethod
    def get_current_stage(self) -> str:
        """Get current therapy stage."""
        pass

    @abstractmethod
    def set_current_stage(self, stage: str) -> None:
        """Set current therapy stage."""
        pass

    @abstractmethod
    def get_agent_config(self, agent_type: str) -> Dict[str, Any]:
        """Get agent configuration (model, provider, parameters)."""
        pass


class IUINotifier(ABC):
    """Interface for UI notifications (decouples from Streamlit st.success/error)."""

    @abstractmethod
    def show_success(self, message: str) -> None:
        """Show success message."""
        pass

    @abstractmethod
    def show_error(self, message: str) -> None:
        """Show error message."""
        pass

    @abstractmethod
    def show_info(self, message: str) -> None:
        """Show info message."""
        pass

    @abstractmethod
    def show_warning(self, message: str) -> None:
        """Show warning message."""
        pass
