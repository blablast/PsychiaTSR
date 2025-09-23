"""JSON formatter for log entries."""

import json
from typing import List

from ..interfaces.formatter_interface import IFormatter
from ..log_entry import LogEntry


class JsonFormatter(IFormatter):
    """JSON formatter for structured logging."""

    def __init__(self, indent: int = 2, ensure_ascii: bool = False):
        """
        Initialize JSON formatter.

        Args:
            indent: Indentation level for pretty printing
            ensure_ascii: Whether to escape non-ASCII characters
        """
        self._indent = indent
        self._ensure_ascii = ensure_ascii

    def format(self, entry: LogEntry) -> str:
        """Format a single log entry as JSON."""
        return json.dumps(
            entry.to_dict(),
            indent=self._indent,
            ensure_ascii=self._ensure_ascii
        )

    def format_batch(self, entries: List[LogEntry]) -> str:
        """Format multiple log entries as JSON array."""
        entries_data = [entry.to_dict() for entry in entries]
        return json.dumps(
            entries_data,
            indent=self._indent,
            ensure_ascii=self._ensure_ascii
        )