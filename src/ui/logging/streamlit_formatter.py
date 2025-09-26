"""Streamlit-specific formatter for UI display."""

import json
from datetime import datetime
from typing import List

from ...core.logging.interfaces.formatter_interface import IFormatter
from ...core.logging.log_entry import LogEntry


class StreamlitFormatter(IFormatter):
    """Streamlit formatter for UI-friendly output."""

    def __init__(self, compact: bool = True):
        """
        Initialize Streamlit formatter.

        Args:
            compact: Whether to use compact formatting
        """
        self._compact = compact

    @staticmethod
    def _format_timestamp(timestamp: str) -> str:
        """Format timestamp for Streamlit display."""
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%H:%M:%S")
        except Exception:
            return timestamp

    @staticmethod
    def _get_emoji(event_type: str, agent_type: str) -> str:
        """Get emoji for event/agent type."""
        emoji_map = {
            ("supervisor_request", "supervisor"): "🔍",
            ("supervisor_response", "supervisor"): "🎯",
            ("therapist_request", "therapist"): "💬",
            ("therapist_response", "therapist"): "🗨️",
            ("stage_transition", "system"): "🔄",
            ("model_info", "system"): "🤖",
            ("error", "system"): "❌",
            ("info", "system"): "ℹ️",
        }
        return emoji_map.get((event_type, agent_type or "system"), "📝")

    def format(self, entry: LogEntry) -> str:
        """Format a single log entry for Streamlit."""
        timestamp = self._format_timestamp(entry.timestamp)
        emoji = self._get_emoji(entry.event_type, entry.agent_type)

        if self._compact:
            # Compact format for UI
            formatted = f"{emoji} **[{timestamp}]** {entry.message}"

            # Add response time if available
            if entry.response_time_ms:
                formatted += f" _{entry.response_time_ms}ms_"

        else:
            # Detailed format
            agent = (entry.agent_type or "system").title()
            event = entry.event_type.replace("_", " ").title()

            formatted = f"{emoji} **{agent} - {event}** _{timestamp}_\n{entry.message}"

            if entry.response_time_ms:
                formatted += f"\n⏱️ Response time: {entry.response_time_ms}ms"

            if entry.data and len(str(entry.data)) < 1000:  # Zwiększony limit z 300 na 1000
                data_preview = json.dumps(entry.data, ensure_ascii=False, indent=2)
                formatted += f"\n```json\n{data_preview}\n```"

        return formatted

    def format_batch(self, entries: List[LogEntry]) -> str:
        """Format multiple log entries for Streamlit."""
        if not entries:
            return "No log entries available."

        formatted_entries = []
        for i, entry in enumerate(entries):
            formatted = self.format(entry)
            if i < len(entries) - 1:  # Add separator except for last entry
                formatted += "\n---"
            formatted_entries.append(formatted)

        return "\n".join(formatted_entries)
