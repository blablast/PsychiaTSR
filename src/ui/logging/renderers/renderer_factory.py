"""Renderer factory - Chain of Responsibility implementation."""

from typing import Dict, Any, List

from .base_renderer import BaseRenderer
from .prompt_renderer import PromptRenderer
from .json_renderer import JsonRenderer
from .standard_renderer import StandardRenderer


class RendererFactory:
    """
    Factory with Chain of Responsibility pattern.

    Eliminates duplicate routing logic in main display class.
    """

    def __init__(self):
        # Order matters - more specific renderers first
        self.renderers: List[BaseRenderer] = [
            PromptRenderer(),
            JsonRenderer(),
            StandardRenderer(),  # Fallback - always returns True
        ]

    def get_renderer(self, log_entry: Dict[str, Any]) -> BaseRenderer:
        """Get appropriate renderer for log entry."""
        for renderer in self.renderers:
            if renderer.can_render(log_entry):
                return renderer

        # Should never reach here due to StandardRenderer fallback
        return self.renderers[-1]

    def render_entry(self, log_entry: Dict[str, Any]) -> None:
        """Find and use appropriate renderer - single entry point."""
        renderer = self.get_renderer(log_entry)
        renderer.render(log_entry)
