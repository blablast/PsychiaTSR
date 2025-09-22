"""Interface for technical logging operations."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from ..log_entry import LogEntry
from ....utils.schemas import SupervisorDecision


class ITechnicalLogger(ABC):
    """Interface for technical logging operations."""

    @abstractmethod
    def log_supervisor_request(self, prompt_info: Dict[str, Any]) -> None:
        """Log supervisor request with prompt information."""
        pass

    @abstractmethod
    def log_supervisor_response(self, decision: SupervisorDecision, response_time_ms: int) -> None:
        """Log supervisor response with decision and timing."""
        pass

    @abstractmethod
    def log_therapist_request(self, prompt_info: Dict[str, Any]) -> None:
        """Log therapist request with prompt information."""
        pass

    @abstractmethod
    def log_therapist_response(self, response: str, response_time_ms: int) -> None:
        """Log therapist response with timing."""
        pass

    @abstractmethod
    def log_stage_transition(self, from_stage: str, to_stage: str) -> None:
        """Log stage transition."""
        pass

    @abstractmethod
    def log_error(self, error_message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log error with optional context."""
        pass

    @abstractmethod
    def log_info(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log informational message."""
        pass

    @abstractmethod
    def log_model_info(self, therapist_model: str, supervisor_model: str,
                      therapist_provider: str = "openai", supervisor_provider: str = "gemini") -> None:
        """Log information about currently used models."""
        pass

    @abstractmethod
    def get_logs(self, limit: Optional[int] = None) -> List[LogEntry]:
        """Get logged entries with optional limit."""
        pass

    @abstractmethod
    def clear_logs(self) -> None:
        """Clear all logged entries."""
        pass