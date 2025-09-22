"""In-memory log storage implementation."""

from typing import List, Optional

from ..interfaces.log_storage_interface import ILogStorage
from ..log_entry import LogEntry


class InMemoryLogStorage(ILogStorage):
    """In-memory log storage implementation."""

    def __init__(self, max_entries: int = 100):
        self._entries: List[LogEntry] = []
        self._max_entries = max_entries

    def store_log(self, entry: LogEntry) -> None:
        """Store a log entry."""
        self._entries.append(entry)

        # Keep only the most recent entries
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]

    def retrieve_logs(self, limit: Optional[int] = None) -> List[LogEntry]:
        """Retrieve log entries with optional limit."""
        if limit is None:
            return self._entries.copy()
        return self._entries[-limit:] if limit > 0 else []

    def clear_all_logs(self) -> None:
        """Clear all stored logs."""
        self._entries.clear()