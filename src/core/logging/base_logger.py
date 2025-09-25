"""Base logger implementation with dependency injection."""

import json
from datetime import datetime
from typing import Dict, Any, Optional, List

from .interfaces.logger_interface import ILogger
from .interfaces.formatter_interface import IFormatter
from .interfaces.storage_interface import IStorage
from .log_entry import LogEntry
from ..models.schemas import SupervisorDecision


class BaseLogger(ILogger):
    """
    Standard logger implementation using dependency injection pattern.

    This is the main logger implementation that coordinates between formatters
    and storages. It receives a formatter (how to format log entries) and a
    storage (where to store log entries) and combines them into a functional logger.

    You typically don't create this directly - use LoggerFactory methods instead.

    Architecture:
        BaseLogger receives:
        - IFormatter: Defines how log entries are formatted (JSON, text, Streamlit)
        - IStorage: Defines where log entries are stored (file, console, memory)

    Example (advanced usage):
        >>> from src.core.logging import JsonFormatter, FileStorage
        >>> formatter = JsonFormatter(indent=2)
        >>> storage = FileStorage("app.log")
        >>> logger = BaseLogger(formatter, storage)
        >>> logger.log_info("Logger created with dependency injection")
    """

    def __init__(self, formatter: IFormatter, storage: IStorage):
        """
        Initialize logger with injected dependencies.

        Args:
            formatter: Formatter to use for log entries
            storage: Storage to use for persisting logs
        """
        self._formatter = formatter
        self._storage = storage

    @staticmethod
    def _create_entry(event_type: str, message: str,
                      data: Optional[Dict[str, Any]] = None,
                      response_time_ms: Optional[int] = None,
                      agent_type: str = "system") -> LogEntry:
        """Create a standardized log entry."""
        return LogEntry(
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            message=message,
            data=data or {},
            response_time_ms=response_time_ms,
            agent_type=agent_type
        )

    def log_supervisor_request(self, prompt_info: Dict[str, Any]) -> None:
        """Log supervisor request with full prompt content for debugging."""
        prompt_id = prompt_info.get('id', 'unknown')
        full_prompt = prompt_info.get('full_prompt')

        if full_prompt:
            # Enhanced message with full content for display
            stage_info = f" - {prompt_info.get('stage')}" if prompt_info.get('stage') else ""
            preview = full_prompt[:200] + "..." if len(full_prompt) > 200 else full_prompt
            enhanced_message = f"📝 SUPERVISOR PROMPT - {prompt_id.upper()}{stage_info}\nFull content: {full_prompt}"

            data = {
                "id": prompt_id,
                "stage": prompt_info.get('stage'),
                "history_summary": prompt_info.get('history_summary'),
                "last_user_message": prompt_info.get('last_user_message'),
                "full_prompt": full_prompt,
                "prompt_length": len(full_prompt)
            }
            message = enhanced_message
        else:
            # Fallback for old minimal logging
            message = f"Prompt: {prompt_id}"
            data = {"id": prompt_id}

        entry = self._create_entry(
            event_type="supervisor_request",
            message=message,
            data=data,
            agent_type="supervisor"
        )

        self._storage.store(entry)

    def log_supervisor_response(self, decision: SupervisorDecision, response_time_ms: int) -> None:
        """Log supervisor response with decision and timing."""
        # Simplified logging - only key decision info, not full JSON
        message = f"Decision: {decision.decision}"
        if decision.safety_risk:
            message += f" | SAFETY RISK"

        # Store only essential data, not full supervisor response
        data = {
            "response_time_ms": response_time_ms,
            "decision": decision.decision,
            "safety_risk": decision.safety_risk
        }

        entry = self._create_entry(
            event_type="supervisor_response",
            message=message,
            data=data,
            response_time_ms=response_time_ms,
            agent_type="supervisor"
        )

        self._storage.store(entry)

    def log_therapist_request(self, prompt_info: Dict[str, Any]) -> None:
        """Log therapist request with full prompt content for debugging."""
        prompt_id = prompt_info.get('id', 'unknown')
        full_prompt = prompt_info.get('full_prompt')

        if full_prompt:
            # Enhanced message with full content for display
            stage_info = f" - {prompt_info.get('stage')}" if prompt_info.get('stage') else ""
            enhanced_message = f"📝 THERAPIST PROMPT - {prompt_id.upper()}{stage_info}\nFull content: {full_prompt}"

            data = {
                "id": prompt_id,
                "stage": prompt_info.get('stage'),
                "user_message": prompt_info.get('user_message'),
                "full_prompt": full_prompt,
                "prompt_length": len(full_prompt)
            }
            message = enhanced_message
        else:
            # Fallback for old minimal logging
            if prompt_id.startswith('therapist_'):
                stage_id = prompt_id.replace('therapist_', '')
            else:
                stage_id = 'unknown'
            message = f"Prompt: {prompt_id}"
            data = {"id": prompt_id, "stage": stage_id}

        entry = self._create_entry(
            event_type="therapist_request",
            message=message,
            data=data,
            agent_type="therapist"
        )

        self._storage.store(entry)

    def log_therapist_response(self, response: str, response_time_ms: int, first_chunk_time_ms: int = None) -> None:
        """Log therapist response with timing and optional first chunk timing."""

        data = {"response_time_ms": response_time_ms}
        if first_chunk_time_ms is not None:
            data["first_chunk_time_ms"] = first_chunk_time_ms

        entry = self._create_entry(
            event_type="therapist_response",
            message=response,
            data=data,
            response_time_ms=response_time_ms,
            agent_type="therapist"
        )

        self._storage.store(entry)

    def log_stage_transition(self, from_stage: str, to_stage: str) -> None:
        """Log stage transition."""
        message = f"Stage transition: {from_stage} → {to_stage}"

        entry = self._create_entry(
            event_type="stage_transition",
            message=message,
            data={"from_stage": from_stage, "to_stage": to_stage},
            agent_type="system"
        )

        self._storage.store(entry)

    def log_error(self, error_message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log error with optional context."""
        entry = self._create_entry(
            event_type="error",
            message=error_message,
            data=context,
            agent_type="system"
        )

        self._storage.store(entry)

    def log_info(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log informational message."""
        entry = self._create_entry(
            event_type="info",
            message=message,
            data=data,
            agent_type="system"
        )

        self._storage.store(entry)

    def log_warning(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message."""
        entry = self._create_entry(
            event_type="warning",
            message=message,
            data=data,
            agent_type="system"
        )

        self._storage.store(entry)

    def log_model_info(self, therapist_model: str, supervisor_model: str,
                      therapist_provider: str = "openai", supervisor_provider: str = "gemini") -> None:
        """Log information about currently used models."""
        model_info = {
            "therapist": {
                "model": therapist_model,
                "provider": therapist_provider
            },
            "supervisor": {
                "model": supervisor_model,
                "provider": supervisor_provider
            }
        }

        message = f"Models: Therapist={therapist_provider}/{therapist_model}, Supervisor={supervisor_provider}/{supervisor_model}"

        entry = self._create_entry(
            event_type="model_info",
            message=message,
            data=model_info,
            agent_type="system"
        )

        self._storage.store(entry)

    def get_logs(self, limit: Optional[int] = None) -> List[LogEntry]:
        """Get logged entries with optional limit."""
        return self._storage.retrieve(limit)

    def clear_logs(self) -> None:
        """Clear all logged entries."""
        self._storage.clear()

    @property
    def entry_count(self) -> int:
        """Get the total number of logged entries."""
        if hasattr(self._storage, 'count'):
            return self._storage.count()
        # Fallback for storages without count method
        return len(self._storage.retrieve())

    @property
    def is_empty(self) -> bool:
        """Check if logger has no entries."""
        return self.entry_count == 0

    def add_log_entry(self, entry_type: str, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Add generic log entry with custom type."""
        entry = self._create_entry(
            event_type=entry_type,
            message=message,
            data=data,
            agent_type="system"
        )
        self._storage.store(entry)

    def log_system_prompt(self, agent_type: str, prompt_content: str, description: str) -> None:
        """Log system prompt configuration."""
        # Create enhanced message with full content for display
        preview = prompt_content[:200] + "..." if len(prompt_content) > 200 else prompt_content
        enhanced_message = f"📝 SYSTEM PROMPT - {agent_type.upper()}\nFull content: {prompt_content}"

        data = {
            "description": description,
            "content_preview": preview,
            "full_length": len(prompt_content),
            "full_content": prompt_content,
            "agent_type": agent_type
        }

        entry = self._create_entry(
            event_type="system_prompt_set",
            message=enhanced_message,
            data=data,
            agent_type=agent_type
        )

        self._storage.store(entry)

    def log_stage_prompt(self, agent_type: str, stage_id: str, prompt_content: str, description: str) -> None:
        """Log stage-specific prompt configuration."""
        # Create enhanced message with full content for display
        preview = prompt_content[:200] + "..." if len(prompt_content) > 200 else prompt_content
        enhanced_message = f"📝 STAGE PROMPT - {agent_type.upper()} - {stage_id}\nFull content: {prompt_content}"

        data = {
            "stage_id": stage_id,
            "description": description,
            "content_preview": preview,
            "full_length": len(prompt_content),
            "full_content": prompt_content,
            "agent_type": agent_type
        }

        entry = self._create_entry(
            event_type="stage_prompt_set",
            message=enhanced_message,
            data=data,
            agent_type=agent_type
        )

        self._storage.store(entry)