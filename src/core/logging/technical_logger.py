"""Main technical logger implementation."""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any

from .interfaces.technical_logger_interface import ITechnicalLogger
from .interfaces.log_storage_interface import ILogStorage
from .log_entry import LogEntry
from ...utils.schemas import SupervisorDecision


class TechnicalLogger(ITechnicalLogger):
    """
    Main technical logger implementation following Single Responsibility Principle.

    Handles all therapy session logging with structured data and proper separation
    of concerns between logging logic and storage.
    """

    def __init__(self, storage: ILogStorage):
        self._storage = storage

    def log_supervisor_request(self, prompt_info: Dict[str, Any]) -> None:
        """Log supervisor request with prompt information."""
        message = f"Prompt Used: {prompt_info.get('id', 'unknown')} | {prompt_info.get('created_at', '')}"

        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            event_type="supervisor_request",
            message=message,
            data=prompt_info,
            agent_type="supervisor"
        )

        self._storage.store_log(entry)

    def log_supervisor_response(self, decision: SupervisorDecision, response_time_ms: int) -> None:
        """Log supervisor response with decision and timing."""
        decision_data = {
            "decision": decision.decision,
            "reason": decision.reason,
            "handoff": decision.handoff,
            "safety_risk": decision.safety_risk
        }

        message = json.dumps(decision_data, ensure_ascii=False)

        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            event_type="supervisor_response",
            message=message,
            data=decision_data,
            response_time_ms=response_time_ms,
            agent_type="supervisor"
        )

        self._storage.store_log(entry)

    def log_therapist_request(self, prompt_info: Dict[str, Any]) -> None:
        """Log therapist request with prompt information."""
        message = f"Prompt Used: {prompt_info.get('id', 'unknown')} | {prompt_info.get('created_at', '')}"

        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            event_type="therapist_request",
            message=message,
            data=prompt_info,
            agent_type="therapist"
        )

        self._storage.store_log(entry)

    def log_therapist_response(self, response: str, response_time_ms: int) -> None:
        """Log therapist response with timing."""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            event_type="therapist_response",
            message=response,
            response_time_ms=response_time_ms,
            agent_type="therapist"
        )

        self._storage.store_log(entry)

    def log_stage_transition(self, from_stage: str, to_stage: str) -> None:
        """Log stage transition."""
        message = f"Stage transition: {from_stage} → {to_stage}"

        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            event_type="stage_transition",
            message=message,
            data={"from_stage": from_stage, "to_stage": to_stage}
        )

        self._storage.store_log(entry)

    def log_error(self, error_message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log error with optional context."""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            event_type="error",
            message=error_message,
            data=context
        )

        self._storage.store_log(entry)

    def log_info(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Log informational message."""
        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            event_type="info",
            message=message,
            data=data
        )

        self._storage.store_log(entry)

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

        message = f"🤖 Models: THR=[{therapist_provider.upper()}] {therapist_model} | SUP=[{supervisor_provider.upper()}] {supervisor_model}"

        entry = LogEntry(
            timestamp=datetime.now().isoformat(),
            event_type="model_info",
            message=message,
            data=model_info,
            agent_type="system"
        )

        self._storage.store_log(entry)

    def get_logs(self, limit: Optional[int] = None) -> List[LogEntry]:
        """Get logged entries with optional limit."""
        return self._storage.retrieve_logs(limit)

    def clear_logs(self) -> None:
        """Clear all logged entries."""
        self._storage.clear_all_logs()