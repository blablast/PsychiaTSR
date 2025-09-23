"""Technical log display for Streamlit UI."""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, Any, Optional, List


class TechnicalLogDisplay:
    """Handles display of technical logs in Streamlit UI."""

    def __init__(self, session_key: str = "technical_log", max_entries: int = None):
        self._session_key = session_key
        self._max_entries = max_entries  # None = no limit!
        self._initialize_session_state()

    def add_log_entry(self, event_type: str, data: str, response_time_ms: Optional[int] = None) -> None:
        """Add entry to technical log."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data,
            "response_time_ms": response_time_ms
        }

        st.session_state[self._session_key].append(log_entry)

        # No limits - keep ALL entries!


    def display(self) -> None:
        """Display technical log in UI."""
        if not st.session_state[self._session_key]:
            st.info("Brak logów technicznych")
            return


        # Group logs by user interactions
        log_blocks = self._group_logs_by_user_messages()

        if not log_blocks:
            # Fallback to old display if no blocks
            for log_entry in st.session_state[self._session_key]:
                self._render_log_entry(log_entry)
        else:
            self._display_log_blocks(log_blocks)

    def clear(self) -> None:
        """Clear all log entries."""
        st.session_state[self._session_key] = []

    def _initialize_session_state(self) -> None:
        """Initialize session state if needed."""
        if self._session_key not in st.session_state:
            st.session_state[self._session_key] = []

    def _render_log_entry(self, log_entry: Dict[str, Any]) -> None:
        """Render a single log entry."""
        timestamp = self._format_timestamp(log_entry["timestamp"])
        event_type = log_entry["event_type"]
        data = log_entry["data"]
        response_time = log_entry.get("response_time_ms")

        style_info = self._get_style_info(event_type, data)
        time_info = self._format_response_time(response_time)

        if event_type == "supervisor_response" and self._is_json_data(data):
            self._render_json_entry(style_info, timestamp, time_info, data)
        elif self._is_prompt_data(data):
            self._render_prompt_entry(style_info, timestamp, time_info, data)
        else:
            self._render_standard_entry(style_info, timestamp, time_info, data)

    @staticmethod
    def _format_timestamp(timestamp: str) -> str:
        """Format timestamp with milliseconds."""
        if not timestamp:
            return ""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%H:%M:%S.%f")[:-3]
        except:
            return timestamp

    @staticmethod
    def _create_style_dict(bg_color: str, border_color: str, icon: str, agent_label: str) -> Dict[str, str]:
        """Create style dictionary for log entry."""
        return {
            "bg_color": bg_color,
            "border_color": border_color,
            "icon": icon,
            "agent_label": agent_label
        }

    def _get_style_info(self, event_type: str, data: str) -> Dict[str, str]:
        """Get styling information for log entry."""
        if event_type == "supervisor_request":
            return self._create_style_dict("rgba(233, 30, 99, 0.1)", "#e91e63", "→", "SUP")
        elif event_type == "supervisor_response":
            return self._create_style_dict("rgba(233, 30, 99, 0.15)", "#e91e63", "←", "SUP")
        elif event_type == "therapist_request":
            return self._create_style_dict("rgba(33, 150, 243, 0.1)", "#2196f3", "→", "THR")
        elif event_type == "therapist_response":
            return self._create_style_dict("rgba(33, 150, 243, 0.15)", "#2196f3", "←", "THR")
        elif "👤 Użytkownik:" in data:
            return self._create_style_dict("rgba(255, 152, 0, 0.1)", "#ff9800", "💬", "USR")
        elif "🔍 Supervisor decision:" in data:
            return self._create_style_dict("rgba(255, 152, 0, 0.15)", "#ff9800", "🔍", "DEC")
        elif "🎯 ZMIANA ETAPU TERAPII:" in data:
            return self._create_style_dict("rgba(76, 175, 80, 0.2)", "#4caf50", "🎯", "STAGE")
        elif "🔍 Rozpoczynam konsultację z supervisorem" in data:
            return self._create_style_dict("rgba(156, 39, 176, 0.1)", "#9c27b0", "🔄", "PHASE")
        elif "💬 Generuję odpowiedź terapeuty" in data:
            return self._create_style_dict("rgba(156, 39, 176, 0.1)", "#9c27b0", "🔄", "PHASE")
        elif "🚨" in data and ("KRYZYS" in data or "PROTOKÓŁ" in data):
            return self._create_style_dict("rgba(244, 67, 54, 0.2)", "#f44336", "🚨", "CRISIS")
        elif "📝" in data and ("PROMPT" in data or "Prompt content" in data):
            return self._create_style_dict("rgba(121, 85, 72, 0.1)", "#795548", "📝", "PROMPT")
        elif event_type == "stage_transition":
            return self._create_style_dict("rgba(76, 175, 80, 0.1)", "#4caf50", "🔄", "STAGE")
        elif event_type == "model_info":
            return self._create_style_dict("rgba(156, 39, 176, 0.1)", "#9c27b0", "🤖", "MODEL")
        elif event_type == "error":
            return self._create_style_dict("rgba(244, 67, 54, 0.1)", "#f44336", "❌", "ERR")
        else:
            return self._create_style_dict("rgba(158, 158, 158, 0.1)", "#999", "ℹ️", "INFO")

    def _format_response_time(self, response_time: Optional[int]) -> str:
        """Format response time for display."""
        if response_time is None:
            return ""

        if response_time < 1000:
            return f" ({response_time}ms)"
        else:
            return f" ({response_time/1000:.1f}s)"

    @staticmethod
    def _is_json_data(data: str) -> bool:
        """Check if data is valid JSON."""
        try:
            json.loads(data)
            return True
        except:
            return False

    @staticmethod
    def _is_prompt_data(data: str) -> bool:
        """Check if data contains prompt content."""
        prompt_indicators = [
            "📝 Full system prompt:",
            "📝 Current user prompt:",
            "📝 Complete supervisor prompt with context:",
            "📝 Complete therapist prompt with context:"
        ]
        return any(indicator in data for indicator in prompt_indicators)

    @staticmethod
    def _render_json_entry(style_info: Dict[str, str], timestamp: str, time_info: str, data: str) -> None:
        """Render log entry with JSON data."""
        st.markdown(
            f'<div style="'
            f'background: {style_info["bg_color"]}; '
            f'border-left: 3px solid {style_info["border_color"]}; '
            f'padding: 4px 6px; '
            f'margin: 2px 0; '
            f'border-radius: 3px; '
            f'font-size: 0.75em; '
            f'">'
            f'<strong>{style_info["agent_label"]} {style_info["icon"]} {timestamp}{time_info}</strong>'
            f'</div>',
            unsafe_allow_html=True
        )

        with st.expander("📋 JSON", expanded=False):
            st.json(json.loads(data))

    @staticmethod
    def _render_prompt_entry(style_info: Dict[str, str], timestamp: str, time_info: str, data: str) -> None:
        """Render log entry with prompt data in expandable container."""
        # Split the data to get header and prompt content
        lines = data.split('\n', 1)
        header = lines[0] if lines else data
        prompt_content = lines[1] if len(lines) > 1 else ""

        st.markdown(
            f'<div style="'
            f'background: {style_info["bg_color"]}; '
            f'border-left: 3px solid {style_info["border_color"]}; '
            f'padding: 4px 6px; '
            f'margin: 2px 0; '
            f'border-radius: 3px; '
            f'font-size: 0.75em; '
            f'">'
            f'<strong>{style_info["agent_label"]} {style_info["icon"]} {timestamp}{time_info}</strong><br>'
            f'<span style="font-size: 0.95em;">{header}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

        if prompt_content.strip():
            with st.expander("📝 Prompt Content", expanded=False):
                st.text(prompt_content.strip())

    @staticmethod
    def _render_standard_entry(style_info: Dict[str, str], timestamp: str, time_info: str, data: str) -> None:
        """Render standard log entry."""
        # Escape HTML characters in data to prevent injection
        import html
        escaped_data = html.escape(data)

        st.markdown(
            f'<div style="'
            f'background: {style_info["bg_color"]}; '
            f'border-left: 3px solid {style_info["border_color"]}; '
            f'padding: 6px 8px; '
            f'margin: 1px 0; '
            f'border-radius: 4px; '
            f'font-size: 0.8em; '
            f'font-family: "Courier New", monospace; '
            f'line-height: 1.2; '
            f'">'
            f'<strong style="color: {style_info["border_color"]};">{style_info["agent_label"]} {style_info["icon"]} {timestamp}{time_info}</strong><br>'
            f'<span style="font-size: 0.95em; white-space: pre-wrap;">{escaped_data}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    def _copy_logs_to_clipboard(self) -> None:
        """Copy all logs to clipboard as formatted text."""
        if not st.session_state[self._session_key]:
            st.warning("Brak logów do skopiowania")
            return

        # Format logs as plain text
        formatted_logs = []
        for log_entry in st.session_state[self._session_key]:
            timestamp = self._format_timestamp(log_entry["timestamp"])
            event_type = log_entry["event_type"]
            data = log_entry["data"]
            response_time = log_entry.get("response_time_ms")

            time_info = self._format_response_time(response_time)
            formatted_logs.append(f"[{timestamp}{time_info}] {event_type}: {data}")

        logs_text = "\n".join(formatted_logs)

        # Use Streamlit's built-in clipboard functionality
        st.code(logs_text, language="text")
        st.success("📋 Logi sformatowane powyżej - użyj Ctrl+A, Ctrl+C aby skopiować")

    def _show_block_copy_content(self, block: Dict[str, Any]) -> None:
        """Show block content in popover for copying."""
        logs = block["logs"]
        user_message = block["user_message"]

        # Format block header
        formatted_logs = []
        if user_message:
            formatted_logs.append(f"=== 💬 WIADOMOŚĆ UŻYTKOWNIKA: {user_message} ===")
        else:
            formatted_logs.append(f"=== 📋 BLOK LOGÓW ({len(logs)} wpisów) ===")

        formatted_logs.append("")

        # Format all logs in block
        for log_entry in logs:
            timestamp = self._format_timestamp(log_entry["timestamp"])
            event_type = log_entry["event_type"]
            data = log_entry["data"]
            response_time = log_entry.get("response_time_ms")

            time_info = self._format_response_time(response_time)
            formatted_logs.append(f"[{timestamp}{time_info}] {event_type}: {data}")

        formatted_logs.append("")
        formatted_logs.append("=" * 60)

        block_text = "\n".join(formatted_logs)

        # Show content in text area for easy copying
        st.text_area(
            "Zaznacz i skopiuj (Ctrl+A, Ctrl+C):",
            value=block_text,
            height=300,
            help="Kliknij w pole, naciśnij Ctrl+A aby zaznaczyć wszystko, potem Ctrl+C aby skopiować"
        )

    def _group_logs_by_user_messages(self) -> List[Dict[str, Any]]:
        """Group logs into blocks separated by user messages."""
        blocks = []
        current_block = []

        for log_entry in st.session_state[self._session_key]:
            data = log_entry["data"]

            # Check if this is a user message
            if "👤 Użytkownik:" in data:
                # Start new block if we have logs in current block
                if current_block:
                    blocks.append({
                        "logs": current_block.copy(),
                        "user_message": self._extract_user_message(current_block[0]["data"]) if current_block else ""
                    })
                    current_block = []

                current_block.append(log_entry)
            else:
                current_block.append(log_entry)

        # Add remaining logs as final block
        if current_block:
            user_msg = ""
            for log in current_block:
                if "👤 Użytkownik:" in log["data"]:
                    user_msg = self._extract_user_message(log["data"])
                    break

            blocks.append({
                "logs": current_block,
                "user_message": user_msg
            })

        return blocks

    def _extract_user_message(self, log_data: str) -> str:
        """Extract user message from log data."""
        if "👤 Użytkownik:" in log_data:
            return log_data.split("👤 Użytkownik:", 1)[1].strip().strip("'\"")
        return ""

    def _display_log_blocks(self, blocks: List[Dict[str, Any]]) -> None:
        """Display logs organized in expandable blocks."""
        for i, block in enumerate(blocks):
            user_message = block["user_message"]
            logs = block["logs"]

            # Create block title with copy button
            if user_message:
                block_title = f"💬 Wiadomość {i+1}: {user_message[:50]}{'...' if len(user_message) > 50 else ''}"
            else:
                block_title = f"📋 Blok logów {i+1} ({len(logs)} wpisów)"

            # Display block in expander with copy button in header
            col1, col2 = st.columns([10, 1])

            with col1:
                expanded = (i == len(blocks) - 1)  # Last block expanded by default
                with st.expander(block_title, expanded=expanded):
                    for log_entry in logs:
                        self._render_log_entry(log_entry)

            with col2:
                # Use popover directly instead of button callback
                with st.popover("📋", help="Skopiuj cały blok", use_container_width=False):
                    self._show_block_copy_content(block)


# Legacy compatibility functions
def add_technical_log(event_type: str, data: str, response_time_ms: Optional[int] = None) -> None:
    """Legacy function for backward compatibility."""
    # Use session_state directly instead of creating new instance
    import streamlit as st
    session_key = "technical_log"

    # Initialize if needed
    if session_key not in st.session_state:
        st.session_state[session_key] = []

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "data": data,
        "response_time_ms": response_time_ms
    }

    st.session_state[session_key].append(log_entry)


def display_technical_log() -> None:
    """Legacy function for backward compatibility."""
    display = TechnicalLogDisplay()
    display.display()


def copy_technical_logs() -> None:
    """Copy all technical logs to clipboard."""
    display = TechnicalLogDisplay()
    display._copy_logs_to_clipboard()


