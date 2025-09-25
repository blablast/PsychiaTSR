"""Base renderer - Template Method pattern."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..components.header_renderer import HeaderRenderer
from ..components.content_renderer import ContentRenderer
from ..components.style_provider import StyleProvider, StyleInfo
from ..parsers.message_parser import MessageParser, ParsedMessage


class BaseRenderer(ABC):
    """
    Base renderer using Template Method pattern.

    Eliminates duplicate flow logic across renderers.
    """

    def __init__(self):
        self.header_renderer = HeaderRenderer()
        self.content_renderer = ContentRenderer()
        self.style_provider = StyleProvider()
        self.message_parser = MessageParser()

    @abstractmethod
    def can_render(self, log_entry: Dict[str, Any]) -> bool:
        """Check if this renderer can handle the log entry."""
        pass

    def render(self, log_entry: Dict[str, Any]) -> None:
        """
        Template method - defines rendering flow.

        Same flow for all renderers, eliminates duplicate logic.
        """
        # Parse message
        parsed = self.message_parser.parse(log_entry["data"])

        # Get style
        style_info = self.style_provider.get_style(
            log_entry["event_type"],
            log_entry["data"]
        )

        # Render header (same for all)
        self.header_renderer.render_header(
            style_info=style_info,
            timestamp=log_entry["timestamp"],
            response_time_ms=log_entry.get("response_time_ms"),
            compact_info=parsed.compact_info or ""
        )

        # Render content (specific implementation)
        self._render_content(parsed, style_info)

    @abstractmethod
    def _render_content(self, parsed: ParsedMessage, style_info: StyleInfo) -> None:
        """Render content - specific to each renderer type."""
        pass