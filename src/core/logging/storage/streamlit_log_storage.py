"""Streamlit session state log storage implementation."""

from typing import List, Optional
import streamlit as st

from ..interfaces.log_storage_interface import ILogStorage
from ..log_entry import LogEntry


class StreamlitLogStorage(ILogStorage):
    """Streamlit session state log storage implementation."""

    def __init__(self, session_key: str = "technical_log", max_entries: int = 50):
        self._session_key = session_key
        self._max_entries = max_entries
        self._initialize_session_state()

    def store_log(self, entry: LogEntry) -> None:
        """Store a log entry in Streamlit session state."""
        # Convert LogEntry to dict for JSON serialization
        log_dict = {
            "timestamp": entry.timestamp,
            "event_type": entry.event_type,
            "data": entry.message,  # Keep legacy field name for compatibility
            "response_time_ms": entry.response_time_ms,
            "agent_type": entry.agent_type
        }

        st.session_state[self._session_key].append(log_dict)

        # Keep only recent entries
        if len(st.session_state[self._session_key]) > self._max_entries:
            st.session_state[self._session_key] = st.session_state[self._session_key][-self._max_entries:]

        # Set flag for UI to detect new logs
        self._mark_logs_updated()

    def retrieve_logs(self, limit: Optional[int] = None) -> List[LogEntry]:
        """Retrieve log entries from Streamlit session state."""
        log_dicts = st.session_state.get(self._session_key, [])

        # Convert dicts back to LogEntry objects
        entries = [
            LogEntry(
                timestamp=log_dict["timestamp"],
                event_type=log_dict["event_type"],
                message=log_dict["data"],  # Legacy field name
                response_time_ms=log_dict.get("response_time_ms"),
                agent_type=log_dict.get("agent_type")
            )
            for log_dict in log_dicts
        ]

        if limit is None:
            return entries
        return entries[-limit:] if limit > 0 else []

    def clear_all_logs(self) -> None:
        """Clear all stored logs."""
        st.session_state[self._session_key] = []

    # Additional convenience methods for backward compatibility
    def add_entry(self, entry: LogEntry) -> None:
        """Add entry (convenience method)."""
        self.store_log(entry)

    def get_all_entries(self) -> List[LogEntry]:
        """Get all entries (convenience method)."""
        return self.retrieve_logs()

    def get_recent_entries(self, count: int) -> List[LogEntry]:
        """Get recent entries (convenience method)."""
        return self.retrieve_logs(count)

    def clear(self) -> None:
        """Clear logs (convenience method)."""
        self.clear_all_logs()

    def _initialize_session_state(self) -> None:
        """Initialize session state if needed."""
        if self._session_key not in st.session_state:
            st.session_state[self._session_key] = []

    def _mark_logs_updated(self) -> None:
        """Mark that logs have been updated for UI detection."""
        try:
            import time
            # Set timestamp for when logs were last updated
            st.session_state[f'{self._session_key}_last_updated'] = time.time()
        except Exception:
            # Silently fail if not in Streamlit context
            pass

    def get_last_update_time(self) -> float:
        """Get timestamp of last log update."""
        return st.session_state.get(f'{self._session_key}_last_updated', 0)