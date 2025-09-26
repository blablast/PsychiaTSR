"""
Professional logging system for therapy applications.

This package provides a flexible, dependency-injection based logging system
designed specifically for therapy session applications. It supports multiple
output formats (JSON, text, Streamlit UI) and multiple storage backends
(file, console, memory, composite).

Quick Start:
    >>> from src.core.logging import LoggerFactory

    # Simple file logging
    >>> logger = LoggerFactory.create_file_logger("app.log")
    >>> logger.log_info("Application started")

    # Multi-destination logging (file + Streamlit UI)
    >>> logger = LoggerFactory.create_default()
    >>> logger.log_stage_transition("opening", "middle")

    # Development logging (console + file)
    >>> logger = LoggerFactory.create_development()
    >>> logger.log_error("Debug info", {"user_id": 123})

Key Components:
    - LoggerFactory: Creates pre-configured loggers
    - ILogger: Universal logging interfaces
    - Formatters: JsonFormatter, TextFormatter
    - Storages: FileStorage, ConsoleStorage, MemoryStorage, CompositeStorage

Architecture:
    The system uses dependency injection where loggers receive:
    - IFormatter: How to format log entries
    - IStorage: Where to store log entries

    This allows any formatter to work with any storage, creating maximum flexibility.
"""

# Main API
from .logger_factory import LoggerFactory
from .base_logger import BaseLogger
from .interfaces.logger_interface import ILogger
from .interfaces.formatter_interface import IFormatter
from .interfaces.storage_interface import IStorage
from .log_entry import LogEntry

# Formatters
from .formatters import JsonFormatter, TextFormatter

# Storages
from .storages import FileStorage, ConsoleStorage, MemoryStorage, CompositeStorage

__all__ = [
    # Main API
    "LoggerFactory",
    "BaseLogger",
    "ILogger",
    "IFormatter",
    "IStorage",
    "LogEntry",
    # Formatters
    "JsonFormatter",
    "TextFormatter",
    # Storages
    "FileStorage",
    "ConsoleStorage",
    "MemoryStorage",
    "CompositeStorage",
]
