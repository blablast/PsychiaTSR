"""Header renderer - eliminates duplicate header rendering code."""

import streamlit as st
from datetime import datetime
from typing import Optional

from .style_provider import StyleInfo


class HeaderRenderer:
    """Renders consistent headers for all log entry types."""

    @staticmethod
    def format_timestamp(timestamp: str) -> str:
        """Format timestamp with milliseconds."""
        if not timestamp:
            return ""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%H:%M:%S.%f")[:-3]
        except:
            return timestamp

    @staticmethod
    def format_response_time(response_time_ms: Optional[int]) -> str:
        """Format response time for display."""
        if response_time_ms is None:
            return ""

        if response_time_ms < 1000:
            return f" ({response_time_ms}ms)"
        else:
            return f" ({response_time_ms/1000:.1f}s)"

    def render_header(self, style_info: StyleInfo, timestamp: str,
                     response_time_ms: Optional[int] = None,
                     compact_info: str = "") -> None:
        """
        Render unified header for all log entry types.

        Args:
            style_info: Style configuration
            timestamp: Entry timestamp
            response_time_ms: Optional response time
            compact_info: Optional additional info for header
        """
        formatted_timestamp = self.format_timestamp(timestamp)
        time_info = self.format_response_time(response_time_ms)

        # Build header content
        header_content = f'<strong>{style_info.agent_label} {style_info.icon} {formatted_timestamp}{time_info}</strong>'

        if compact_info:
            header_content += f'<br><span style="font-size: 0.9em;">{compact_info}</span>'

        # Single header implementation - used by all renderers
        st.markdown(
            f'<div style="'
            f'background: {style_info.bg_color}; '
            f'border-left: 3px solid {style_info.border_color}; '
            f'padding: 4px 6px; '
            f'margin: 2px 0; '
            f'border-radius: 3px; '
            f'font-size: 0.75em; '
            f'">'
            f'{header_content}'
            f'</div>',
            unsafe_allow_html=True
        )