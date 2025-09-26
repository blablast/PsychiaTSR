"""Crisis handler interface for dependency inversion."""

from abc import ABC, abstractmethod
from ...workflow.workflow_result import WorkflowResult


class ICrisisHandler(ABC):
    """Interface for crisis handling following DIP."""

    @abstractmethod
    def handle_crisis(self, user_message: str, supervisor_decision) -> WorkflowResult:
        """
        Handle crisis situation when safety_risk is detected.

        Args:
            user_message: User's message that triggered crisis
            supervisor_decision: Supervisor decision with safety_risk=True

        Returns:
            WorkflowResult with crisis response
        """
        pass

    @abstractmethod
    def is_crisis_active(self) -> bool:
        """Check if crisis mode is currently active."""
        pass

    @abstractmethod
    def get_crisis_contacts(self) -> dict:
        """Get emergency contact information."""
        pass
