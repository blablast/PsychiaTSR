"""Base database loader - eliminates 90% duplication in database operations."""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class BaseDatabaseLoader:
    """
    Base class for all database-like JSON file operations.

    Eliminates code duplication by providing common CRUD operations
    for JSON-based configuration storage.
    """

    def __init__(self, database_file: Path, database_type: str, logger=None):
        """
        Initialize base database loader.

        Args:
            database_file: Path to JSON database file
            database_type: Type description for logging (e.g., "stage prompts")
            logger: Optional logger for operations tracking
        """
        self.database_file = database_file
        self.database_type = database_type
        self.logger = logger
        self._cache = None

    def load_database(self) -> Dict[str, Any]:
        """Load database with caching and string unescaping."""
        if self._cache is None:
            try:
                with open(self.database_file, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    self._cache = self._unescape_json_strings(raw_data)

                if self.logger:
                    self.logger.info(f"Loaded {self.database_type} database successfully")

            except FileNotFoundError:
                if self.logger:
                    self.logger.warning(f"{self.database_type.title()} database not found: {self.database_file}")
                self._cache = self._create_empty_database()

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error loading {self.database_type} database: {e}")
                self._cache = self._create_empty_database()

        return self._cache

    def save_database(self, database: Dict[str, Any]) -> bool:
        """Save database and update cache."""
        try:
            # Update timestamp
            if "metadata" in database:
                database["metadata"]["updated_at"] = datetime.now().isoformat()

            # Ensure parent directory exists
            self.database_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.database_file, 'w', encoding='utf-8') as f:
                json.dump(database, f, indent=2, ensure_ascii=False)

            # Update cache
            self._cache = database

            if self.logger:
                self.logger.info(f"{self.database_type.title()} database saved successfully")
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving {self.database_type} database: {e}")
            return False

    def get_record(self, record_key: str) -> Optional[Dict[str, Any]]:
        """Get record by database key."""
        try:
            database = self.load_database()
            return database.get("prompts", {}).get(record_key)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting record by key {record_key}: {e}")
            return None

    def save_record(self, record_key: str, record_data: Dict[str, Any]) -> bool:
        """Save single record to database."""
        try:
            database = self.load_database()
            database["prompts"][record_key] = record_data
            return self.save_database(database)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving record {record_key}: {e}")
            return False

    def delete_record(self, record_key: str) -> bool:
        """Delete record from database."""
        try:
            database = self.load_database()
            if record_key in database.get("prompts", {}):
                del database["prompts"][record_key]
                return self.save_database(database)
            return True  # Record doesn't exist - consider it deleted
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error deleting record {record_key}: {e}")
            return False

    def list_all_records(self) -> Dict[str, Any]:
        """List all records in database."""
        try:
            database = self.load_database()
            return database.get("prompts", {})
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error listing all records: {e}")
            return {}

    def find_records_by_metadata(self, metadata_filters: Dict[str, Any]) -> Dict[str, Any]:
        """Find records matching metadata criteria."""
        try:
            database = self.load_database()
            results = {}

            for key, record in database.get("prompts", {}).items():
                record_metadata = record.get("metadata", {})

                # Check if all filters match
                match = True
                for filter_key, filter_value in metadata_filters.items():
                    if record_metadata.get(filter_key) != filter_value:
                        match = False
                        break

                if match:
                    results[key] = record

            return results
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error finding records by metadata: {e}")
            return {}

    def find_next_global_id(self) -> int:
        """Find next globally unique ID across all records."""
        database = self.load_database()
        max_id = 0

        for record in database.get("prompts", {}).values():
            record_id = record.get("metadata", {}).get("id", 0)
            if isinstance(record_id, int):
                max_id = max(max_id, record_id)

        return max_id + 1

    def archive_active_records(self, metadata_filters: Dict[str, Any]) -> int:
        """Archive (mark as inactive) all active records matching criteria."""
        try:
            database = self.load_database()
            archived_count = 0

            # Add status=active to filters
            filters_with_active = {**metadata_filters, "status": "active"}

            for key, record in database.get("prompts", {}).items():
                record_metadata = record.get("metadata", {})

                # Check if all filters match
                match = True
                for filter_key, filter_value in filters_with_active.items():
                    if record_metadata.get(filter_key) != filter_value:
                        match = False
                        break

                if match:
                    # Mark as inactive
                    record["metadata"]["status"] = "inactive"
                    record["metadata"]["archived_at"] = datetime.now().isoformat()
                    archived_count += 1

            if archived_count > 0:
                self.save_database(database)

            return archived_count
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error archiving active records: {e}")
            return 0

    def clear_cache(self) -> None:
        """Clear cached database content."""
        self._cache = None

    def _create_empty_database(self) -> Dict[str, Any]:
        """Create empty database structure. Override in subclasses for specific structure."""
        return {
            "metadata": {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "description": f"{self.database_type.title()} database"
            },
            "prompts": {}
        }

    def _unescape_json_strings(self, data: Any) -> Any:
        """
        Recursively unescape JSON strings in data structure.
        Converts escaped strings: \\" to ", \\n to newline, etc.
        """
        if isinstance(data, dict):
            return {key: self._unescape_json_strings(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._unescape_json_strings(item) for item in data]
        elif isinstance(data, str):
            # Order matters - do \\\\ first to avoid double processing
            return (data.replace('\\\\', '\\')      # Double backslash to single
                       .replace('\\"', '"')        # Escaped quote
                       .replace("\\'", "'")        # Escaped single quote
                       .replace('\\n', '\n')       # Escaped newline
                       .replace('\\r', '\r')       # Escaped carriage return
                       .replace('\\t', '\t')       # Escaped tab
                       .replace('\\b', '\b')       # Escaped backspace
                       .replace('\\f', '\f')       # Escaped form feed
                       .replace('\\/', '/'))       # Escaped forward slash
        else:
            return data