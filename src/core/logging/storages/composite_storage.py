"""Composite storage for multiple storage backends."""

from typing import List, Optional, Dict

from ..interfaces.storage_interface import IStorage
from ..log_entry import LogEntry


class CompositeStorage(IStorage):
    """Composite storage that delegates to multiple storage backends."""

    def __init__(self):
        """Initialize composite storage."""
        self._storages: Dict[str, IStorage] = {}

    def add_storage(self, name: str, storage: IStorage) -> "CompositeStorage":
        """
        Add a storage backend.

        Args:
            name: Name identifier for the storage
            storage: Storage backend to add

        Returns:
            Self for fluent interfaces
        """
        self._storages[name] = storage
        return self

    def remove_storage(self, name: str) -> bool:
        """
        Remove a storage backend.

        Args:
            name: Name of storage to remove

        Returns:
            True if storage was removed, False if not found
        """
        return self._storages.pop(name, None) is not None

    def get_storage(self, name: str) -> Optional[IStorage]:
        """
        Get a specific storage backend.

        Args:
            name: Name of storage to get

        Returns:
            Storage backend or None if not found
        """
        return self._storages.get(name)

    def list_storages(self) -> List[str]:
        """
        List all storage names.

        Returns:
            List of storage names
        """
        return list(self._storages.keys())

    @staticmethod
    def _handle_storage_error(storage_name: str, storage: IStorage, error: Exception) -> None:
        """Handle individual storage failures."""
        # Log error but don't raise - one storage failure shouldn't break others
        print(f"Storage '{storage_name}' ({type(storage).__name__}) failed: {error}")

    def store(self, entry: LogEntry) -> None:
        """Store log entry to all storage backends."""
        for name, storage in self._storages.items():
            try:
                storage.store(entry)
            except Exception as e:
                self._handle_storage_error(name, storage, e)

    def store_batch(self, entries: List[LogEntry]) -> None:
        """Store multiple log entries to all storage backends."""
        for name, storage in self._storages.items():
            try:
                storage.store_batch(entries)
            except Exception as e:
                self._handle_storage_error(name, storage, e)

    def retrieve(self, limit: Optional[int] = None) -> List[LogEntry]:
        """
        Retrieve log entries from first available storage.

        Priority order: streamlit -> file -> memory -> any other

        Returns:
            Log entries from first working storage
        """
        # Define priority order for retrieval
        priority_order = ["streamlit", "file", "memory"]

        # Try priority storages first
        for storage_name in priority_order:
            if storage_name in self._storages:
                try:
                    return self._storages[storage_name].retrieve(limit)
                except Exception as e:
                    self._handle_storage_error(storage_name, self._storages[storage_name], e)

        # If no priority storages available, try any storage
        for name, storage in self._storages.items():
            try:
                return storage.retrieve(limit)
            except Exception as e:
                self._handle_storage_error(name, storage, e)

        return []

    def clear(self) -> None:
        """Clear all log entries from all storage backends."""
        for name, storage in self._storages.items():
            try:
                storage.clear()
            except Exception as e:
                self._handle_storage_error(name, storage, e)

    def count(self) -> int:
        """
        Get count from first available storage.

        Returns:
            Count from first working storage
        """
        # Use same priority order as retrieve
        priority_order = ["streamlit", "file", "memory"]

        # Try priority storages first
        for storage_name in priority_order:
            if storage_name in self._storages:
                try:
                    return self._storages[storage_name].count()
                except Exception as e:
                    self._handle_storage_error(storage_name, self._storages[storage_name], e)

        # If no priority storages available, try any storage
        for name, storage in self._storages.items():
            try:
                return storage.count()
            except Exception as e:
                self._handle_storage_error(name, storage, e)

        return 0
