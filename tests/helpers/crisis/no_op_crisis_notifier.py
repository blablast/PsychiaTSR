"""No-op crisis notifier for testing."""

from src.core.crisis.interfaces import UICrisisNotifier


class NoOpCrisisNotifier(UICrisisNotifier):
    """No-op implementation for testing or non-UI contexts."""

    def notify_crisis_detected(self) -> None:
        """Do nothing - for testing."""
        pass

    def show_crisis_message(self, message: str) -> None:
        """Do nothing - for testing."""
        pass