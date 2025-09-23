"""Text formatter for human-readable log output."""

import json
from datetime import datetime
from typing import List

from ..interfaces.formatter_interface import IFormatter
from ..log_entry import LogEntry


class TextFormatter(IFormatter):
    """Text formatter for human-readable output."""

    def __init__(self, use_colors: bool = False, include_data: bool = True):
        """
        Initialize text formatter.

        Args:
            use_colors: Whether to use ANSI color codes
            include_data: Whether to include data field in output
        """
        self._use_colors = use_colors
        self._include_data = include_data

        # ANSI color codes
        self._colors = {
            'reset': '\033[0m',
            'red': '\033[91m',
            'green': '\033[92m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'magenta': '\033[95m',
            'cyan': '\033[96m',
            'white': '\033[97m'
        }

    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled."""
        if not self._use_colors:
            return text
        return f"{self._colors.get(color, '')}{text}{self._colors['reset']}"

    @staticmethod
    def _format_timestamp(timestamp: str) -> str:
        """Format timestamp for display."""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%H:%M:%S")
        except Exception:
            return timestamp

    @staticmethod
    def _get_event_color(event_type: str) -> str:
        """Get color for event type."""
        color_map = {
            "error": "red",
            "stage_transition": "magenta",
            "model_info": "yellow",
            "supervisor_request": "blue",
            "supervisor_response": "blue",
            "therapist_request": "green",
            "therapist_response": "green"
        }
        return color_map.get(event_type, "white")

    @staticmethod
    def _get_agent_color(agent_type: str) -> str:
        """Get color for agent type."""
        color_map = {
            "supervisor": "blue",
            "therapist": "green",
            "system": "cyan"
        }
        return color_map.get(agent_type, "white")

    def format(self, entry: LogEntry) -> str:
        """Format a single log entry as text."""
        timestamp = self._format_timestamp(entry.timestamp)
        agent_color = self._get_agent_color(entry.agent_type or "system")
        event_color = self._get_event_color(entry.event_type)

        # Format: [HH:MM:SS] [AGENT] EVENT_TYPE: message
        formatted = (
            f"[{self._colorize(timestamp, 'cyan')}] "
            f"[{self._colorize((entry.agent_type or 'SYSTEM').upper(), agent_color)}] "
            f"{self._colorize(entry.event_type.upper(), event_color)}: "
            f"{entry.message}"
        )

        # Add response time if available
        if entry.response_time_ms:
            formatted += f" ({entry.response_time_ms}ms)"

        # Add data if enabled and present
        if self._include_data and entry.data and len(str(entry.data)) < 200:
            data_str = json.dumps(entry.data, ensure_ascii=False, separators=(',', ':'))
            formatted += f"\n    {self._colorize('Data:', 'yellow')} {data_str}"

        return formatted

    def format_batch(self, entries: List[LogEntry]) -> str:
        """Format multiple log entries as text."""
        return "\n".join(self.format(entry) for entry in entries)