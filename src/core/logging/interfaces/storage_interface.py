"""Interface for log storage."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..log_entry import LogEntry


class IStorage(ABC):
    """Interface for persisting and retrieving log entries."""

    @abstractmethod
    def store(self, entry: LogEntry) -> None:
        """
        Store a single log entry.

        Args:
            entry: The log entry to store
        """
        pass

    @abstractmethod
    def store_batch(self, entries: List[LogEntry]) -> None:
        """
        Store multiple log entries efficiently.

        Args:
            entries: List of log entries to store
        """
        pass

    @abstractmethod
    def retrieve(self, limit: Optional[int] = None) -> List[LogEntry]:
        """
        Retrieve log entries with optional limit.

        Args:
            limit: Maximum number of entries to retrieve

        Returns:
            List of log entries
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all stored log entries."""
        pass

    @abstractmethod
    def count(self) -> int:
        """
        Get the total number of stored log entries.

        Returns:
            Number of stored entries
        """
        pass
