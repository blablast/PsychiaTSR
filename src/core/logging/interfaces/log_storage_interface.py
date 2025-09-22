"""Interface for log storage operations."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..log_entry import LogEntry


class ILogStorage(ABC):
    """Interface for log storage operations."""

    @abstractmethod
    def store_log(self, entry: LogEntry) -> None:
        """Store a log entry."""
        pass

    @abstractmethod
    def retrieve_logs(self, limit: Optional[int] = None) -> List[LogEntry]:
        """Retrieve log entries with optional limit."""
        pass

    @abstractmethod
    def clear_all_logs(self) -> None:
        """Clear all stored logs."""
        pass