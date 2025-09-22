"""Logging interfaces package."""

from .technical_logger_interface import ITechnicalLogger
from .log_storage_interface import ILogStorage

__all__ = [
    'ITechnicalLogger',
    'ILogStorage',
]