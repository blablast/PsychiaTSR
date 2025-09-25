"""JSON renderer - handles JSON-only entries."""

import json
from typing import Dict, Any
import streamlit as st

from .base_renderer import BaseRenderer
from ..components.style_provider import StyleInfo
from ..parsers.message_parser import ParsedMessage


class JsonRenderer(BaseRenderer):
    """Renders entries that are pure JSON."""

    def can_render(self, log_entry: Dict[str, Any]) -> bool:
        """Check if entry is pure JSON and supervisor response."""
        event_type = log_entry.get("event_type", "")
        data = log_entry.get("data", "")

        # JSON entries are typically supervisor responses
        return (event_type == "supervisor_response" and
                self.content_renderer.is_json(data))

    def _render_content(self, parsed: ParsedMessage, style_info: StyleInfo) -> None:
        """Render JSON content in expander."""
        if parsed.full_content and parsed.full_content.strip():
            with st.expander("📋 JSON", expanded=False):
                try:
                    json_data = json.loads(parsed.full_content)
                    st.json(json_data)
                except json.JSONDecodeError:
                    # Fallback to code
                    st.code(parsed.full_content, language="text")