"""Console-based storage implementation."""

from typing import List, Optional

from ..interfaces.storage_interface import IStorage
from ..interfaces.formatter_interface import IFormatter
from ..log_entry import LogEntry


class ConsoleStorage(IStorage):
    """Console storage that prints logs immediately."""

    def __init__(self, formatter: IFormatter, keep_in_memory: bool = True, max_entries: int = 100):
        """
        Initialize console storage.

        Args:
            formatter: Formatter to use for console output
            keep_in_memory: Whether to keep entries in memory for retrieval
            max_entries: Maximum entries to keep in memory
        """
        self._formatter = formatter
        self._keep_in_memory = keep_in_memory
        self._max_entries = max_entries
        self._entries: List[LogEntry] = []

    def store(self, entry: LogEntry) -> None:
        """Store (print) a single log entry."""
        # Print to console
        try:
            formatted = self._formatter.format(entry)
            print(formatted)
        except UnicodeEncodeError:
            # Handle Unicode encoding issues by replacing problematic characters
            try:
                formatted = self._formatter.format(entry)
                # Remove or replace Unicode characters that can't be displayed
                safe_formatted = formatted.encode("ascii", errors="replace").decode("ascii")
                print(safe_formatted)
            except Exception:
                # Final fallback to basic print with safe encoding
                safe_message = entry.message.encode("ascii", errors="replace").decode("ascii")
                print(f"[{entry.timestamp}] {entry.event_type}: {safe_message}")
        except Exception:
            # Fallback to basic print
            try:
                safe_message = entry.message.encode("ascii", errors="replace").decode("ascii")
                print(f"[{entry.timestamp}] {entry.event_type}: {safe_message}")
            except Exception:
                print(f"[{entry.timestamp}] {entry.event_type}: [message encoding error]")

        # Keep in memory if enabled
        if self._keep_in_memory:
            self._entries.append(entry)
            if len(self._entries) > self._max_entries:
                self._entries = self._entries[-self._max_entries :]

    def store_batch(self, entries: List[LogEntry]) -> None:
        """Store (print) multiple log entries."""
        if not entries:
            return

        try:
            # Print batch using formatter
            formatted = self._formatter.format_batch(entries)
            print(formatted)
        except UnicodeEncodeError:
            # Handle Unicode encoding issues
            try:
                formatted = self._formatter.format_batch(entries)
                safe_formatted = formatted.encode("ascii", errors="replace").decode("ascii")
                print(safe_formatted)
            except Exception:
                # Fallback: print each entry individually
                for entry in entries:
                    self.store(entry)
                return  # Avoid double storage in memory
        except Exception:
            # Fallback: print each entry individually
            for entry in entries:
                self.store(entry)
            return  # Avoid double storage in memory

        # Keep in memory if enabled
        if self._keep_in_memory:
            self._entries.extend(entries)
            if len(self._entries) > self._max_entries:
                self._entries = self._entries[-self._max_entries :]

    def retrieve(self, limit: Optional[int] = None) -> List[LogEntry]:
        """Retrieve log entries from memory."""
        if not self._keep_in_memory:
            return []

        if limit is not None:
            return self._entries[-limit:]
        return self._entries.copy()

    def clear(self) -> None:
        """Clear stored log entries from memory."""
        if self._keep_in_memory:
            self._entries.clear()

    def count(self) -> int:
        """Get the total number of stored log entries."""
        return len(self._entries) if self._keep_in_memory else 0
