"""UI notification interface for crisis situations - Core abstraction only."""

from abc import ABC, abstractmethod


class UICrisisNotifier(ABC):
    """Abstract interface for UI crisis notifications."""

    @abstractmethod
    def notify_crisis_detected(self) -> None:
        """Notify UI that a crisis has been detected."""
        pass

    @abstractmethod
    def show_crisis_message(self, message: str) -> None:
        """Display crisis message to user."""
        pass


class NoOpCrisisNotifier(UICrisisNotifier):
    """No-op implementation of crisis notifier for testing."""

    def notify_crisis_detected(self) -> None:
        """No-op implementation - does nothing."""
        pass

    def show_crisis_message(self, message: str) -> None:
        """No-op implementation - does nothing."""
        pass