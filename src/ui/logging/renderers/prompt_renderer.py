"""Prompt renderer - handles enhanced prompt messages."""

from typing import Dict, Any

from .base_renderer import BaseRenderer
from ..components.style_provider import StyleInfo
from ..parsers.message_parser import ParsedMessage


class PromptRenderer(BaseRenderer):
    """Renders enhanced prompt messages (📝 PROMPT - ...)."""

    def can_render(self, log_entry: Dict[str, Any]) -> bool:
        """Check if entry is an enhanced prompt."""
        event_type = log_entry.get("event_type", "")
        data = log_entry.get("data", "")

        # Handle both event types and data patterns
        return (event_type in ["system_prompt_set", "stage_prompt_set"] or
                any(pattern in data for pattern in [
                    "📝 SUPERVISOR PROMPT -",
                    "📝 THERAPIST PROMPT -",
                    "📝 SYSTEM PROMPT -",
                    "📝 STAGE PROMPT -",
                    "Description:",
                    "Content preview:",
                    "Full content:"
                ]))

    def _render_content(self, parsed: ParsedMessage, style_info: StyleInfo) -> None:
        """Render prompt content in expander."""
        if parsed.full_content and parsed.full_content.strip():
            self.content_renderer.render_expandable_content(
                summary=f"{parsed.compact_info or 'Prompt'} Details",
                content=f"Full content: {parsed.full_content}",
                expanded=False
            )