"""Streamlit session state storage implementation."""

from typing import List, Optional
import streamlit as st

from ...core.logging.interfaces.storage_interface import IStorage
from ...core.logging.log_entry import LogEntry


class StreamlitStorage(IStorage):
    """Streamlit session state storage for log entries."""

    def __init__(self, session_key: str = "technical_log", max_entries: int = 50):
        """
        Initialize Streamlit storage.

        Args:
            session_key: Key to use in Streamlit session state
            max_entries: Maximum number of entries to keep
        """
        self._session_key = session_key
        self._max_entries = max_entries
        self._initialize_session_state()

    def _initialize_session_state(self) -> None:
        """Initialize session state if needed."""
        if self._session_key not in st.session_state:
            st.session_state[self._session_key] = []

    def _get_entries_data(self) -> List[dict]:
        """Get entries from session state."""
        self._initialize_session_state()
        return st.session_state[self._session_key]

    def _set_entries_data(self, entries_data: List[dict]) -> None:
        """Set entries in session state."""
        st.session_state[self._session_key] = entries_data

    def store(self, entry: LogEntry) -> None:
        """Store a single log entry in session state."""
        try:
            entries_data = self._get_entries_data()

            # Add new entry as dict for JSON serialization
            entries_data.append(entry.to_dict())

            # Rotate if necessary
            if len(entries_data) > self._max_entries:
                entries_data = entries_data[-self._max_entries:]

            self._set_entries_data(entries_data)

        except Exception:
            # Silent fail - Streamlit issues shouldn't break logging
            pass

    def store_batch(self, entries: List[LogEntry]) -> None:
        """Store multiple log entries efficiently."""
        if not entries:
            return

        try:
            entries_data = self._get_entries_data()

            # Add new entries
            new_entries_data = [entry.to_dict() for entry in entries]
            all_entries_data = entries_data + new_entries_data

            # Rotate if necessary
            if len(all_entries_data) > self._max_entries:
                all_entries_data = all_entries_data[-self._max_entries:]

            self._set_entries_data(all_entries_data)

        except Exception:
            # Fallback: store each entry individually
            for entry in entries:
                self.store(entry)

    def retrieve(self, limit: Optional[int] = None) -> List[LogEntry]:
        """Retrieve log entries from session state."""
        try:
            entries_data = self._get_entries_data()

            # Convert to LogEntry objects
            entries = []
            for entry_data in entries_data:
                try:
                    entries.append(LogEntry.from_dict(entry_data))
                except Exception:
                    # Skip malformed entries
                    continue

            # Apply limit
            if limit is not None:
                entries = entries[-limit:]

            return entries

        except Exception:
            return []

    def clear(self) -> None:
        """Clear all stored log entries."""
        try:
            self._set_entries_data([])
        except Exception:
            # Silent fail
            pass

    def count(self) -> int:
        """Get the total number of stored log entries."""
        try:
            entries_data = self._get_entries_data()
            return len(entries_data)
        except Exception:
            return 0