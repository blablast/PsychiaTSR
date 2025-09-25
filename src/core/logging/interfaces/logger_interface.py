"""Base logging interfaces for all logger implementations."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

from ..log_entry import LogEntry
from ...models.schemas import SupervisorDecision


class ILogger(ABC):
    """
    Universal logging interfaces for therapy session applications.

    This interfaces defines all logging operations needed for therapy applications,
    including specialized methods for supervisor/therapist interactions, stage
    transitions, and model configurations. All loggers implement this interfaces
    regardless of their storage mechanism (file, console, Streamlit, memory).

    Common Usage Patterns:
        >>> logger = LoggerFactory.create_default()

        # Log user interactions
        >>> logger.log_info("User started session")
        >>> logger.log_error("Invalid input", {"input": "bad_data"})

        # Log therapy-specific events
        >>> logger.log_stage_transition("opening", "middle")
        >>> logger.log_therapist_response("How are you feeling?", response_time_ms=150)
        >>> logger.log_model_info("gpt-4", "gpt-3.5", "openai", "openai")

        # Access logger state
        >>> print(f"Entries: {logger.entry_count}")
        >>> print(f"Empty: {logger.is_empty}")
        >>> recent_logs = logger.get_logs(limit=10)
    """

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
    def log_therapist_response(self, response: str, response_time_ms: int, first_chunk_time_ms: int = None) -> None:
        """Log therapist response with timing and optional first chunk timing."""
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
    def log_warning(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message."""
        pass

    @abstractmethod
    def log_model_info(self, therapist_model: str, supervisor_model: str,
                      therapist_provider: str = "openai", supervisor_provider: str = "gemini") -> None:
        """Log information about currently used models."""
        pass

    @abstractmethod
    def log_system_prompt(self, agent_type: str, prompt_content: str, description: str) -> None:
        """Log system prompt configuration."""
        pass

    @abstractmethod
    def log_stage_prompt(self, agent_type: str, stage_id: str, prompt_content: str, description: str) -> None:
        """Log stage-specific prompt configuration."""
        pass

    @abstractmethod
    def get_logs(self, limit: Optional[int] = None) -> List[LogEntry]:
        """Get logged entries with optional limit."""
        pass

    @abstractmethod
    def clear_logs(self) -> None:
        """Clear all logged entries."""
        pass

    @property
    @abstractmethod
    def entry_count(self) -> int:
        """Get the total number of logged entries."""
        pass

    @property
    @abstractmethod
    def is_empty(self) -> bool:
        """Check if logger has no entries."""
        pass