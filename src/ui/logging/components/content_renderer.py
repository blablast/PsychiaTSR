"""Content renderer - eliminates JSON/Code rendering redundancy."""

import json
import streamlit as st
from typing import Optional


class ContentRenderer:
    """Handles content rendering with unified JSON/Code logic."""

    @staticmethod
    def is_json(content: str) -> bool:
        """Check if content is valid JSON."""
        try:
            content = content.strip()
            if content.startswith('{') and content.endswith('}'):
                json.loads(content)
                return True
        except (json.JSONDecodeError, AttributeError):
            pass
        return False

    def render_content(self, content: str) -> None:
        """
        Render content with automatic JSON detection.

        Single implementation replaces 4+ duplicate try/except blocks.
        """
        if not content or not content.strip():
            return

        content = content.strip()

        if self.is_json(content):
            try:
                json_data = json.loads(content)
                st.json(json_data)
            except json.JSONDecodeError:
                # Fallback to code if JSON parsing fails
                st.code(content, language="text")
        else:
            st.code(content, language="text")

    def render_expandable_content(self, summary: str, content: str,
                                expanded: bool = False) -> None:
        """
        Render content in expander if it's longer than summary.

        Eliminates duplicate expander logic.
        """
        if not content or not content.strip():
            return

        # Only show expander if content is different/longer than summary
        lines = content.split('\n', 1)
        content_without_header = lines[1] if len(lines) > 1 else ""

        if content_without_header.strip():
            with st.expander(f"📋 {summary}", expanded=expanded):
                self.render_content(content_without_header)
        # If no additional content, don't show expander