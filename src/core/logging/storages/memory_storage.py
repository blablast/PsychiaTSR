"""In-memory storage implementation."""

from typing import List, Optional

from ..interfaces.storage_interface import IStorage
from ..log_entry import LogEntry


class MemoryStorage(IStorage):
    """In-memory storage for log entries."""

    def __init__(self, max_entries: int = 100):
        """
        Initialize memory storage.

        Args:
            max_entries: Maximum number of entries to keep in memory
        """
        self._max_entries = max_entries
        self._entries: List[LogEntry] = []

    def store(self, entry: LogEntry) -> None:
        """Store a single log entry in memory."""
        self._entries.append(entry)

        # Rotate if necessary
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]

    def store_batch(self, entries: List[LogEntry]) -> None:
        """Store multiple log entries efficiently."""
        if not entries:
            return

        self._entries.extend(entries)

        # Rotate if necessary
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]

    def retrieve(self, limit: Optional[int] = None) -> List[LogEntry]:
        """Retrieve log entries from memory."""
        if limit is not None:
            return self._entries[-limit:]
        return self._entries.copy()

    def clear(self) -> None:
        """Clear all stored log entries."""
        self._entries.clear()

    def count(self) -> int:
        """Get the total number of stored log entries."""
        return len(self._entries)