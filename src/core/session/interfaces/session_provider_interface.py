"""Interface for providing therapy agents from session storage."""

from abc import ABC, abstractmethod


class ISessionAgentProvider(ABC):
    """Interface for providing therapy agents from session storage."""

    @abstractmethod
    def get_therapist_agent(self):
        """Get the therapist agent instance from session storage."""
        pass

    @abstractmethod
    def get_supervisor_agent(self):
        """Get the supervisor agent instance from session storage."""
        pass

    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if agents are properly initialized in session storage."""
        pass