"""Dual storage - both Streamlit session state and file."""

from typing import List, Optional

from ..interfaces.log_storage_interface import ILogStorage
from ..log_entry import LogEntry
from .streamlit_log_storage import StreamlitLogStorage
from .file_log_storage import FileLogStorage


class DualLogStorage(ILogStorage):
    """Dual storage that writes to both Streamlit session state and file."""

    def __init__(self, file_path: str, max_entries_memory: int = 50, max_entries_file: int = 1000):
        self._streamlit_storage = StreamlitLogStorage(max_entries=max_entries_memory)
        self._file_storage = FileLogStorage(file_path, max_entries=max_entries_file)

    def store_log(self, entry: LogEntry) -> None:
        """Store log entry to both storages."""
        self._streamlit_storage.add_entry(entry)
        self._file_storage.add_entry(entry)

    def retrieve_logs(self, limit: Optional[int] = None) -> List[LogEntry]:
        """Retrieve logs from memory (faster for UI)."""
        entries = self._streamlit_storage.get_all_entries()
        if limit is not None:
            return entries[-limit:] if entries else []
        return entries

    def clear_all_logs(self) -> None:
        """Clear both storages."""
        self._streamlit_storage.clear()
        self._file_storage.clear()

    # Additional convenience methods
    def add_entry(self, entry: LogEntry) -> None:
        """Add entry to both storages."""
        self.store_log(entry)

    def get_all_entries(self) -> List[LogEntry]:
        """Get all entries from memory (faster for UI)."""
        return self.retrieve_logs()

    def get_recent_entries(self, count: int) -> List[LogEntry]:
        """Get recent entries from memory."""
        return self.retrieve_logs(count)

    def clear(self) -> None:
        """Clear both storages."""
        self.clear_all_logs()

    def get_file_entries(self) -> List[LogEntry]:
        """Get all entries from file storage."""
        return self._file_storage.get_all_entries()