"""Session-based storage for logging to session data."""

from typing import Optional
import streamlit as st
from ..interfaces.storage_interface import IStorage
from ..log_entry import LogEntry


class SessionStorage(IStorage):
    """Stores logs in session data via StorageProvider."""

    def __init__(self):
        self._storage_provider = None

    def _get_storage_provider(self):
        """Get StorageProvider instance."""
        if self._storage_provider is None:
            from src.infrastructure.storage import StorageProvider
            from config import Config
            config = Config.get_instance()
            self._storage_provider = StorageProvider(config.LOGS_DIR)
        return self._storage_provider

    @staticmethod
    def _get_current_session_id() -> Optional[str]:
        """Get current session ID from Streamlit session state."""
        return st.session_state.get('session_id')

    def store(self, entry: LogEntry) -> None:
        """Store log entry in session data."""
        try:
            session_id = self._get_current_session_id()
            if not session_id:
                return

            storage = self._get_storage_provider()

            # Convert LogEntry to dict format
            log_entry = {
                "timestamp": entry.timestamp,
                "event_type": entry.event_type,
                "message": entry.message,
                "data": entry.data,
                "response_time_ms": entry.response_time_ms,
                "agent_type": entry.agent_type
            }

            storage.add_technical_log(session_id, log_entry)

        except Exception:
            pass

    def store_batch(self, entries: list) -> None:
        """Store multiple log entries efficiently."""
        for entry in entries:
            self.store(entry)

    def retrieve(self, limit: Optional[int] = None) -> list:
        """Retrieve log entries with optional limit."""
        try:
            session_id = self._get_current_session_id()
            if not session_id:
                return []

            storage = self._get_storage_provider()
            session_data = storage.load_session(session_id)

            if not session_data or "technical_logs" not in session_data:
                return []

            logs = session_data["technical_logs"]

            if limit:
                return logs[-limit:]  # Get last N entries
            return logs

        except Exception:
            return []

    def count(self) -> int:
        """Get the total number of stored log entries."""
        try:
            logs = self.retrieve()
            return len(logs)
        except Exception:
            return 0

    def get_all_entries(self) -> list:
        """Get all log entries for current session."""
        try:
            session_id = self._get_current_session_id()
            if not session_id:
                return []

            storage = self._get_storage_provider()
            session_data = storage.load_session(session_id)

            if not session_data or "technical_logs" not in session_data:
                return []

            return session_data["technical_logs"]

        except Exception:
            return []

    def clear(self) -> bool:
        """Clear all log entries for current session."""
        try:
            session_id = self._get_current_session_id()
            if not session_id:
                return False

            storage = self._get_storage_provider()
            session_data = storage.load_session(session_id)

            if not session_data:
                return False

            # Clear technical logs
            session_data["technical_logs"] = []
            return storage.save_session(session_data)

        except Exception:
            return False