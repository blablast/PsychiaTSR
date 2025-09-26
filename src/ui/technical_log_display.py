"""Technical log display for Streamlit UI - Refactored with component architecture.

Reduced from 550+ lines to ~100 lines by eliminating redundancy and using components.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, Optional, List

from .logging.renderers.renderer_factory import RendererFactory


class TechnicalLogDisplay:
    """
    Streamlined technical log display using component architecture.

    Old: 550+ lines God Object with massive redundancy
    New: ~100 lines orchestrator using specialized components
    """

    def __init__(self, session_key: str = "technical_log", max_entries: int = None):
        self._session_key = session_key
        self._max_entries = max_entries  # None = no limit!
        self._renderer_factory = RendererFactory()
        self._initialize_session_state()

    def add_log_entry(
        self, event_type: str, data: str, response_time_ms: Optional[int] = None
    ) -> None:
        """Add entry to technical log."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data,
            "response_time_ms": response_time_ms,
        }

        st.session_state[self._session_key].append(log_entry)

    def display(self) -> None:
        """Display technical log in UI - simplified with new component architecture."""
        if not st.session_state[self._session_key]:
            st.info("Brak logów technicznych")
            return

        log_entries = st.session_state[self._session_key]
        converted_entries = self._convert_entries(log_entries)

        if not converted_entries:
            st.info("Brak logów technicznych")
            return

        # Display all log entries using new renderer system
        for log_entry in converted_entries:
            self._renderer_factory.render_entry(log_entry)

    @staticmethod
    def _convert_entries(log_entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert entries to unified format."""
        converted_entries = []

        for entry in log_entries:
            if isinstance(entry, dict):
                if "message" in entry:
                    # New LogEntry format - use message directly for display
                    display_data = entry.get("message", "")

                    # For prompt requests, don't add JSON data (it's in enhanced message)
                    event_type = entry.get("event_type", "")
                    if event_type not in ["supervisor_request", "therapist_request"]:
                        if entry.get("data") and isinstance(entry["data"], dict) and entry["data"]:
                            import json

                            data_str = json.dumps(entry["data"], ensure_ascii=False, indent=2)
                            display_data = f"{display_data}\n\nData: {data_str}"

                    converted_entry = {
                        "timestamp": entry.get("timestamp", ""),
                        "event_type": entry.get("event_type", ""),
                        "data": display_data,
                        "response_time_ms": entry.get("response_time_ms"),
                        "agent_type": entry.get("agent_type", "system"),
                    }
                    converted_entries.append(converted_entry)
                else:
                    # Old format - use as is
                    converted_entries.append(entry)

        return converted_entries

    def clear(self) -> None:
        """Clear all log entries."""
        st.session_state[self._session_key] = []

    def _initialize_session_state(self) -> None:
        """Initialize session state if needed."""
        if self._session_key not in st.session_state:
            st.session_state[self._session_key] = []

    def copy_logs_to_clipboard(self) -> None:
        """Copy all logs to clipboard as formatted text."""
        if not st.session_state[self._session_key]:
            st.warning("Brak logów do skopiowania")
            return

        # Format logs as plain text
        formatted_logs = []
        for log_entry in st.session_state[self._session_key]:
            timestamp = self._format_timestamp_simple(log_entry.get("timestamp", ""))
            event_type = log_entry.get("event_type", "")
            data = log_entry.get("data", "")
            response_time = log_entry.get("response_time_ms")

            time_info = self._format_response_time_simple(response_time)
            formatted_logs.append(f"[{timestamp}{time_info}] {event_type}: {data}")

        logs_text = "\n".join(formatted_logs)

        # Use Streamlit's built-in clipboard functionality
        st.code(logs_text, language="text")
        st.success("📋 Logi sformatowane powyżej - użyj Ctrl+A, Ctrl+C aby skopiować")

    @staticmethod
    def _format_timestamp_simple(timestamp: str) -> str:
        """Simple timestamp formatting for clipboard."""
        if not timestamp:
            return ""
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.strftime("%H:%M:%S.%f")[:-3]
        except Exception:
            return timestamp

    @staticmethod
    def _format_response_time_simple(response_time_ms: Optional[int]) -> str:
        """Simple response time formatting for clipboard."""
        if response_time_ms is None:
            return ""

        if response_time_ms < 1000:
            return f" ({response_time_ms}ms)"
        else:
            return f" ({response_time_ms/1000:.1f}s)"


# Convenience functions for backward compatibility
def add_technical_log(event_type: str, message: str, response_time_ms: int = None) -> None:
    """Add entry to technical log using current session state."""
    from datetime import datetime

    session_key = "technical_log"

    # Initialize if needed
    if session_key not in st.session_state:
        st.session_state[session_key] = []

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "message": message,
        "data": message,
        "response_time_ms": response_time_ms,
    }

    st.session_state[session_key].append(log_entry)


def display_technical_log() -> None:
    """Display technical log using TechnicalLogDisplay class."""
    display = TechnicalLogDisplay()
    display.display()


def copy_technical_logs() -> None:
    """Copy all technical logs to clipboard."""
    display = TechnicalLogDisplay()
    display.copy_logs_to_clipboard()
