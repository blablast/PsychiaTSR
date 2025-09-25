"""File-based storage implementation."""

import json
from pathlib import Path
from typing import List, Optional

from ..interfaces.storage_interface import IStorage
from ..log_entry import LogEntry


class FileStorage(IStorage):
    """File-based storage for log entries."""

    def __init__(self, file_path: str, max_entries: int = 1000):
        """
        Initialize file storage.

        Args:
            file_path: Path to the log file
            max_entries: Maximum number of entries before rotation
        """
        self._file_path = Path(file_path)
        self._max_entries = max_entries
        self._ensure_directory_exists()

    def _ensure_directory_exists(self) -> None:
        """Create log directory if it doesn't exist."""
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

    def _read_entries(self) -> List[dict]:
        """Read existing entries from file."""
        if not self._file_path.exists():
            return []

        try:
            with open(self._file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                return json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_entries(self, entries: List[dict]) -> None:
        """Write entries to file."""
        try:
            with open(self._file_path, 'w', encoding='utf-8') as f:
                json.dump(entries, f, ensure_ascii=False, indent=2)
        except Exception:
            # Fallback: try to append as JSONL
            self._append_entry_jsonl(entries[-1] if entries else {})

    def _append_entry_jsonl(self, entry_dict: dict) -> None:
        """Fallback: append entry as JSON line."""
        try:
            with open(self._file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry_dict, ensure_ascii=False) + '\n')
        except Exception:
            # Silent fail - storage issues shouldn't break logging
            pass

    def store(self, entry: LogEntry) -> None:
        """Store a single log entry."""
        try:
            # Read existing entries
            entries = self._read_entries()

            # Add new entry
            entries.append(entry.to_dict())

            # Rotate if necessary
            if len(entries) > self._max_entries:
                entries = entries[-self._max_entries:]

            # Write back to file
            self._write_entries(entries)

        except Exception:
            # Fallback: try to append directly
            self._append_entry_jsonl(entry.to_dict())

    def store_batch(self, entries: List[LogEntry]) -> None:
        """Store multiple log entries efficiently."""
        if not entries:
            return

        try:
            # Read existing entries
            existing_entries = self._read_entries()

            # Add new entries
            new_entries = [entry.to_dict() for entry in entries]
            all_entries = existing_entries + new_entries

            # Rotate if necessary
            if len(all_entries) > self._max_entries:
                all_entries = all_entries[-self._max_entries:]

            # Write back to file
            self._write_entries(all_entries)

        except Exception:
            # Fallback: append each entry individually
            for entry in entries:
                self._append_entry_jsonl(entry.to_dict())

    def retrieve(self, limit: Optional[int] = None) -> List[LogEntry]:
        """Retrieve log entries with optional limit."""
        entries_data = self._read_entries()

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

    def clear(self) -> None:
        """Clear all stored log entries."""
        try:
            if self._file_path.exists():
                self._file_path.unlink()
        except Exception:
            # Silent fail - storage issues shouldn't break logging
            pass

    def count(self) -> int:
        """Get the total number of stored log entries."""
        try:
            entries = self._read_entries()
            return len(entries)
        except Exception:
            return 0