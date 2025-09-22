"""Interface for session state management."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class ISessionState(ABC):
    """Interface for session state management."""

    @abstractmethod
    def get_session_id(self) -> Optional[str]:
        """Get current session ID."""
        pass

    @abstractmethod
    def set_session_id(self, session_id: str) -> None:
        """Set current session ID."""
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
    def get_messages(self) -> List[Dict[str, Any]]:
        """Get conversation messages."""
        pass

    @abstractmethod
    def add_message(self, message: Dict[str, Any]) -> None:
        """Add message to conversation."""
        pass

    @abstractmethod
    def clear_messages(self) -> None:
        """Clear all conversation messages."""
        pass