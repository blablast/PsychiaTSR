"""Logger factory with dependency injection."""

from typing import Optional

from .interfaces.logger_interface import ILogger
from .interfaces.formatter_interface import IFormatter
from .interfaces.storage_interface import IStorage
from .base_logger import BaseLogger
from .formatters import JsonFormatter, TextFormatter, StreamlitFormatter
from .storages import FileStorage, ConsoleStorage, StreamlitStorage, MemoryStorage, CompositeStorage, SessionStorage


class LoggerFactory:
    """
    Factory for creating loggers with different configurations.

    The LoggerFactory provides convenient methods for creating loggers with pre-configured
    combinations of formatters and storages. It supports dependency injection pattern
    for maximum flexibility.

    Examples:
        Basic usage with predefined configurations:

        >>> # Simple file logger with JSON format
        >>> logger = LoggerFactory.create_file_logger("app.log", format_type="json")
        >>> logger.log_info("Application started")

        >>> # Console logger with colors
        >>> logger = LoggerFactory.create_console_logger(use_colors=True)
        >>> logger.log_error("Something went wrong", {"error_code": 500})

        >>> # Multi-destination logger
        >>> logger = LoggerFactory.create_multi_logger(
        ...     file_path="app.log",
        ...     use_console=True,
        ...     use_streamlit=True
        ... )
        >>> logger.log_stage_transition("opening", "middle")

        Advanced usage with dependency injection:

        >>> from src.core.logging import JsonFormatter, MemoryStorage
        >>> formatter = JsonFormatter(indent=2)
        >>> storage = MemoryStorage(max_entries=100)
        >>> logger = LoggerFactory.create_logger(formatter, storage)
        >>> logger.log_model_info("gpt-4", "gpt-3.5", "openai", "openai")
    """

    @staticmethod
    def create_logger(formatter: IFormatter, storage: IStorage) -> ILogger:
        """
        Create a logger with custom formatter and storage (dependency injection).

        This is the core method that enables dependency injection. You provide
        any formatter and any storage implementation, and get a fully functional logger.

        Args:
            formatter: Formatter implementation (JsonFormatter, TextFormatter, etc.)
            storage: Storage implementation (FileStorage, MemoryStorage, etc.)

        Returns:
            Configured logger instance

        Example:
            >>> from src.core.logging import JsonFormatter, FileStorage
            >>> formatter = JsonFormatter(indent=2)
            >>> storage = FileStorage("custom.log", max_entries=500)
            >>> logger = LoggerFactory.create_logger(formatter, storage)
            >>> logger.log_info("Custom logger created")
        """
        return BaseLogger(formatter=formatter, storage=storage)

    @staticmethod
    def create_file_logger(file_path: str,
                          format_type: str = "json",
                          max_entries: int = 1000) -> ILogger:
        """
        Create a file logger with specified format.

        Args:
            file_path: Path to log file
            format_type: Format type ("json", "text")
            max_entries: Maximum entries before rotation

        Returns:
            File logger instance
        """
        # Choose formatter based on type
        if format_type == "json":
            formatter = JsonFormatter(indent=2)
        elif format_type == "text":
            formatter = TextFormatter(use_colors=False)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")

        # Create storage
        storage = FileStorage(file_path=file_path, max_entries=max_entries)

        return LoggerFactory.create_logger(formatter, storage)

    @staticmethod
    def create_console_logger(use_colors: bool = True,
                            include_data: bool = True,
                            keep_in_memory: bool = True,
                            max_entries: int = 100) -> ILogger:
        """
        Create a console logger with text formatting.

        Args:
            use_colors: Whether to use ANSI colors
            include_data: Whether to include data in output
            keep_in_memory: Whether to keep logs in memory for retrieval
            max_entries: Maximum entries to keep in memory

        Returns:
            Console logger instance
        """
        # Create formatter
        formatter = TextFormatter(use_colors=use_colors, include_data=include_data)

        # Create storage
        storage = ConsoleStorage(
            formatter=formatter,
            keep_in_memory=keep_in_memory,
            max_entries=max_entries
        )

        return LoggerFactory.create_logger(formatter, storage)

    @staticmethod
    def create_streamlit_logger(compact: bool = True,
                              max_entries: int = 50) -> ILogger:
        """
        Create a Streamlit logger with UI-friendly formatting.

        Args:
            compact: Whether to use compact formatting
            max_entries: Maximum entries to keep in session

        Returns:
            Streamlit logger instance
        """
        # Create formatter
        formatter = StreamlitFormatter(compact=compact)

        # Create storage
        storage = StreamlitStorage(max_entries=max_entries)

        return LoggerFactory.create_logger(formatter, storage)

    @staticmethod
    def create_memory_logger(max_entries: int = 100) -> ILogger:
        """
        Create an in-memory logger.

        Args:
            max_entries: Maximum entries to keep in memory

        Returns:
            Memory logger instance
        """
        # Use JSON formatter for structured data
        formatter = JsonFormatter(indent=None)  # Compact JSON

        # Create storage
        storage = MemoryStorage(max_entries=max_entries)

        return LoggerFactory.create_logger(formatter, storage)

    @staticmethod
    def create_multi_logger(file_path: Optional[str] = None,
                           use_console: bool = False,
                           use_streamlit: bool = True,
                           console_colors: bool = True,
                           max_entries: int = 100) -> ILogger:
        """
        Create a logger that writes to multiple destinations simultaneously.

        This is perfect for applications that need logging to multiple places at once.
        For example, log to both session data and Streamlit UI, or to console and memory.

        Args:
            file_path: Optional file path parameter (triggers session storage instead of file storage)
            use_console: Whether to include console output with colors
            use_streamlit: Whether to include Streamlit session storage
            console_colors: Whether to use ANSI colors in console output
            max_entries: Maximum entries per storage (except session storage)

        Returns:
            Logger that writes to all specified destinations

        Examples:
            >>> # Log to session data + Streamlit UI
            >>> logger = LoggerFactory.create_multi_logger(
            ...     file_path="sessions/session.json",
            ...     use_streamlit=True
            ... )

            >>> # Log to console + session + Streamlit
            >>> logger = LoggerFactory.create_multi_logger(
            ...     file_path="sessions/session.json",
            ...     use_console=True,
            ...     use_streamlit=True,
            ...     console_colors=True
            ... )
        """
        # Use JSON formatter for multi-storage (structured data)
        formatter = JsonFormatter(indent=2)

        # Create composite storage
        composite_storage = CompositeStorage()

        # Add Streamlit storage if requested
        if use_streamlit:
            streamlit_storage = StreamlitStorage(max_entries=max_entries)
            composite_storage.add_storage("streamlit", streamlit_storage)

        # Add session storage if path provided (consolidates to session data)
        if file_path:
            session_storage = SessionStorage()
            composite_storage.add_storage("session", session_storage)

        # Add console storage if requested
        if use_console:
            console_formatter = TextFormatter(use_colors=console_colors)
            console_storage = ConsoleStorage(
                formatter=console_formatter,
                keep_in_memory=False,  # Don't duplicate in memory
                max_entries=0
            )
            composite_storage.add_storage("console", console_storage)

        return LoggerFactory.create_logger(formatter, composite_storage)

    @staticmethod
    def create_default() -> ILogger:
        """
        Create the recommended default logger for therapy applications.

        Creates a logger that writes to both Streamlit UI and a file.
        This is the most common configuration for interactive therapy sessions.

        Returns:
            Logger configured for Streamlit UI + file storage

        Example:
            >>> logger = LoggerFactory.create_default()
            >>> logger.log_stage_transition("opening", "middle")
            >>> logger.log_model_info("gpt-4", "gpt-3.5")
        """
        return LoggerFactory.create_multi_logger(
            file_path="logs/therapy.log",
            use_console=False,
            use_streamlit=True,
            max_entries=50
        )

    @staticmethod
    def create_development() -> ILogger:
        """
        Create a logger optimized for development and debugging.

        Logs to both console (with colors) and file. Perfect for development
        where you want immediate console feedback and persistent file logs.

        Returns:
            Logger with console output and file storage

        Example:
            >>> logger = LoggerFactory.create_development()
            >>> logger.log_error("Database connection failed", {"host": "localhost"})
        """
        return LoggerFactory.create_multi_logger(
            file_path="logs/dev.log",
            use_console=True,
            use_streamlit=False,
            console_colors=True,
            max_entries=100
        )

    @staticmethod
    def create_production() -> ILogger:
        """
        Create a high-capacity logger for production environments.

        Logs only to file with high entry limits and JSON format.
        No console output to avoid performance overhead in production.

        Returns:
            File-only logger with high capacity (5000 entries)

        Example:
            >>> logger = LoggerFactory.create_production()
            >>> logger.log_error("Payment processing failed", {"transaction_id": "tx_123"})
        """
        return LoggerFactory.create_file_logger(
            file_path="logs/production.log",
            format_type="json",
            max_entries=5000
        )

    @staticmethod
    def create_full() -> ILogger:
        """
        Create full-featured logger (All storages).

        Returns:
            Full-featured logger instance
        """
        return LoggerFactory.create_multi_logger(
            file_path="logs/therapy.log",
            use_console=True,
            use_streamlit=True,
            console_colors=True,
            max_entries=50
        )