"""Session manager interface for crisis handler dependency."""

from abc import ABC, abstractmethod


class ICrisisSessionManager(ABC):
    """Interface for session manager operations needed by crisis handler."""

    @abstractmethod
    def add_user_message(self, message: str) -> None:
        """Add user message to conversation."""
        pass

    @abstractmethod
    def add_assistant_message(self, message: str, prompt_used: str = "") -> None:
        """Add assistant message to conversation."""
        pass

    @abstractmethod
    def get_current_stage(self) -> str:
        """Get current therapy stage."""
        pass
