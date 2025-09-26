"""Standard renderer - handles regular log entries."""

from typing import Dict, Any

from .base_renderer import BaseRenderer
from ..components.style_provider import StyleInfo
from ..parsers.message_parser import ParsedMessage


class StandardRenderer(BaseRenderer):
    """Renders standard log entries (fallback for everything else)."""

    def can_render(self, log_entry: Dict[str, Any]) -> bool:
        """Can render any entry - this is the fallback renderer."""
        return True

    def _render_content(self, parsed: ParsedMessage, style_info: StyleInfo) -> None:
        """Render standard content with optional expander."""
        if parsed.full_content and parsed.full_content.strip():
            # Use expandable content to avoid header duplication
            self.content_renderer.render_expandable_content(
                summary=parsed.header,
                content=parsed.raw_data,  # Use raw_data to include header + content
                expanded=False,
            )
