"""Interface for providing therapy agents."""

from abc import ABC, abstractmethod


class IAgentProvider(ABC):
    """Interface for providing therapy agents."""

    @abstractmethod
    def get_therapist_agent(self):
        """Get the therapist agent instance."""
        pass

    @abstractmethod
    def get_supervisor_agent(self):
        """Get the supervisor agent instance."""
        pass

    @abstractmethod
    def is_initialized(self) -> bool:
        """Check if agents are properly initialized."""
        pass