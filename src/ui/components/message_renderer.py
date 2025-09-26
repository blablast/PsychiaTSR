"""Message rendering component for chat interface."""

from typing import Optional, Dict, Any
import streamlit as st
from src.core.session import format_timestamp


class MessageRenderer:
    """Component responsible for rendering individual chat messages."""

    @staticmethod
    def render_message(message: Any) -> None:
        """Render a single chat message with avatar and metadata.

        Args:
            message: Message object with role, text, timestamp, etc.
        """
        is_pending = getattr(message, "is_pending", False)
        avatar = "💚" if message.role == "therapist" else None

        with st.chat_message(message.role, avatar=avatar):
            MessageRenderer._render_message_content(message, is_pending)
            MessageRenderer._render_message_metadata(message)

    @staticmethod
    def _render_message_content(message: Any, is_pending: bool) -> None:
        """Render message content with audio controls."""
        col_content, col_audio = st.columns([9, 1])

        with col_content:
            content = message.text
            if is_pending:
                content += " ⏳"
            st.write(content)

        with col_audio:
            if (
                message.role == "therapist"
                and hasattr(message, "audio_file_path")
                and message.audio_file_path
            ):
                MessageRenderer._render_audio_button(message)

    @staticmethod
    def _render_audio_button(message: Any) -> None:
        """Render audio play button for therapist messages."""
        from src.ui.chat import _render_audio_play_button

        _render_audio_play_button(message)

    @staticmethod
    def _render_message_metadata(message: Any) -> None:
        """Render timestamp and response times for message."""
        if not hasattr(message, "timestamp"):
            return
        caption_parts = [f"🕒 {format_timestamp(message.timestamp)}"]

        if message.role == "therapist":
            response_times = MessageRenderer._get_response_times(message)
            time_info = MessageRenderer._format_response_times(response_times)
            if time_info:
                caption_parts.append(time_info)

        final_caption = " ".join(caption_parts)
        st.caption(final_caption)

    @staticmethod
    def _get_response_times(message: Any) -> Optional[Dict[str, Any]]:
        """Get response times for a message."""
        from src.ui.chat import _get_response_times_for_message

        return _get_response_times_for_message(message)

    @staticmethod
    def _format_response_times(response_times: Optional[Dict[str, Any]]) -> Optional[str]:
        """Format response times into a readable string."""
        if not response_times:
            return None

        sup_time = response_times.get("supervisor_time_ms", 0)
        ther_time = response_times.get("therapist_time_ms", 0)
        first_chunk_time = response_times.get("first_chunk_time_ms")

        if sup_time <= 0 and ther_time <= 0:
            return None

        time_parts = []
        if sup_time > 0:
            time_parts.append(f"SUP: {sup_time/1000:.2f}s")
        if first_chunk_time is not None:
            total_time = (sup_time + first_chunk_time) / 1000
            time_parts.append(f"1st: {first_chunk_time/1000:.2f}s - {total_time:.2f} from start")
        if ther_time > 0:
            time_parts.append(f"THE: {ther_time/1000:.2f}s")

        return f"({', '.join(time_parts)})"
