"""File-based log storage implementation."""

import json
from pathlib import Path
from typing import List, Optional

from ..interfaces.log_storage_interface import ILogStorage
from ..log_entry import LogEntry


class FileLogStorage(ILogStorage):
    """File-based log storage implementation."""

    def __init__(self, log_file_path: str, max_entries: int = 1000):
        self._log_file_path = Path(log_file_path)
        self._max_entries = max_entries
        self._ensure_log_directory()

    def store_log(self, entry: LogEntry) -> None:
        """Store log entry to file."""
        try:
            # Read existing entries
            entries = self.retrieve_logs()

            # Add new entry
            entries.append(entry)

            # Keep only last max_entries
            if len(entries) > self._max_entries:
                entries = entries[-self._max_entries:]

            # Write back to file
            self._write_entries_to_file(entries)

        except Exception as e:
            # Fallback: try to append single entry
            self._append_entry_to_file(entry)

    def retrieve_logs(self, limit: Optional[int] = None) -> List[LogEntry]:
        """Retrieve log entries from file."""
        if not self._log_file_path.exists():
            return []

        try:
            with open(self._log_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                entries = [LogEntry.from_dict(entry_dict) for entry_dict in data]
                if limit is not None:
                    return entries[-limit:] if entries else []
                return entries
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def clear_all_logs(self) -> None:
        """Clear all log entries."""
        if self._log_file_path.exists():
            self._log_file_path.unlink()

    # Additional convenience methods for backward compatibility
    def add_entry(self, entry: LogEntry) -> None:
        """Add log entry to file."""
        self.store_log(entry)

    def get_all_entries(self) -> List[LogEntry]:
        """Get all log entries from file."""
        return self.retrieve_logs()

    def get_recent_entries(self, count: int) -> List[LogEntry]:
        """Get most recent log entries."""
        return self.retrieve_logs(count)

    def clear(self) -> None:
        """Clear all log entries."""
        self.clear_all_logs()

    def _ensure_log_directory(self) -> None:
        """Ensure log directory exists."""
        self._log_file_path.parent.mkdir(parents=True, exist_ok=True)

    def _write_entries_to_file(self, entries: List[LogEntry]) -> None:
        """Write all entries to file."""
        with open(self._log_file_path, 'w', encoding='utf-8') as f:
            json.dump([entry.to_dict() for entry in entries], f, indent=2, ensure_ascii=False)

    def _append_entry_to_file(self, entry: LogEntry) -> None:
        """Append single entry to file (fallback method)."""
        # Simple append mode - just add one line
        with open(self._log_file_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + '\n')