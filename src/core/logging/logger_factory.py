"""Factory for creating different logger implementations."""

from .interfaces.technical_logger_interface import ITechnicalLogger
from .interfaces.log_storage_interface import ILogStorage
from .technical_logger import TechnicalLogger
from .storage.in_memory_log_storage import InMemoryLogStorage
from .storage.streamlit_log_storage import StreamlitLogStorage
from .storage.dual_log_storage import DualLogStorage


class LoggerFactory:
    """Factory for creating logger instances with different storage backends."""

    @staticmethod
    def create_in_memory_logger(max_entries: int = 100) -> ITechnicalLogger:
        """Create a logger with in-memory storage."""
        storage = InMemoryLogStorage(max_entries)
        return TechnicalLogger(storage)

    @staticmethod
    def create_streamlit_logger(max_entries: int = 50) -> ITechnicalLogger:
        """Create a logger with Streamlit session state storage."""
        storage = StreamlitLogStorage(max_entries=max_entries)
        return TechnicalLogger(storage)

    @staticmethod
    def create_dual_logger(log_file_path: str, max_entries_memory: int = 50, max_entries_file: int = 1000) -> ITechnicalLogger:
        """Create a logger that saves to both Streamlit session state and file."""
        storage = DualLogStorage(log_file_path, max_entries_memory, max_entries_file)
        return TechnicalLogger(storage)

    @staticmethod
    def create_logger_with_storage(storage: ILogStorage) -> ITechnicalLogger:
        """Create a logger with custom storage implementation."""
        return TechnicalLogger(storage)


