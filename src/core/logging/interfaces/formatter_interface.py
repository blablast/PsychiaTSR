"""Interface for log formatters."""

from abc import ABC, abstractmethod

from ..log_entry import LogEntry


class IFormatter(ABC):
    """Interface for formatting log entries into specific output formats."""

    @abstractmethod
    def format(self, entry: LogEntry) -> str:
        """
        Format a log entry into a string representation.

        Args:
            entry: The log entry to format

        Returns:
            Formatted string representation of the log entry
        """
        pass

    @abstractmethod
    def format_batch(self, entries: list[LogEntry]) -> str:
        """
        Format multiple log entries.

        Args:
            entries: List of log entries to format

        Returns:
            Formatted string representation of all entries
        """
        pass
