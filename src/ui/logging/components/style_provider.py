"""Style provider for log entries - eliminates style mapping redundancy."""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class StyleInfo:
    """Style information for log entries."""

    bg_color: str
    border_color: str
    icon: str
    agent_label: str


class StyleProvider:
    """Provides consistent styling for different log entry types."""

    # Configuration-driven styles - eliminates redundant conditions
    STYLE_CONFIG = {
        # Supervisor styles
        ("supervisor_request", None): StyleInfo(
            bg_color="rgba(233, 30, 99, 0.1)", border_color="#e91e63", icon="→", agent_label="SUP"
        ),
        ("supervisor_response", None): StyleInfo(
            bg_color="rgba(233, 30, 99, 0.15)", border_color="#e91e63", icon="←", agent_label="SUP"
        ),
        # Therapist styles
        ("therapist_request", None): StyleInfo(
            bg_color="rgba(33, 150, 243, 0.1)", border_color="#2196f3", icon="→", agent_label="THR"
        ),
        ("therapist_response", None): StyleInfo(
            bg_color="rgba(33, 150, 243, 0.15)", border_color="#2196f3", icon="←", agent_label="THR"
        ),
        # System styles
        ("stage_transition", None): StyleInfo(
            bg_color="rgba(76, 175, 80, 0.1)",
            border_color="#4caf50",
            icon="🔄",
            agent_label="STAGE",
        ),
        ("model_info", None): StyleInfo(
            bg_color="rgba(156, 39, 176, 0.1)",
            border_color="#9c27b0",
            icon="🤖",
            agent_label="MODEL",
        ),
        ("error", None): StyleInfo(
            bg_color="rgba(244, 67, 54, 0.1)", border_color="#f44336", icon="❌", agent_label="ERR"
        ),
        ("info", None): StyleInfo(
            bg_color="rgba(158, 158, 158, 0.1)", border_color="#999", icon="ℹ️", agent_label="INFO"
        ),
        # Content-based styles (for data patterns)
        ("*", "user_message"): StyleInfo(
            bg_color="rgba(255, 152, 0, 0.1)", border_color="#ff9800", icon="💬", agent_label="USR"
        ),
        ("*", "supervisor_decision"): StyleInfo(
            bg_color="rgba(255, 152, 0, 0.15)", border_color="#ff9800", icon="🔍", agent_label="DEC"
        ),
        ("*", "stage_change"): StyleInfo(
            bg_color="rgba(76, 175, 80, 0.2)",
            border_color="#4caf50",
            icon="🎯",
            agent_label="STAGE",
        ),
        ("*", "workflow_phase"): StyleInfo(
            bg_color="rgba(156, 39, 176, 0.1)",
            border_color="#9c27b0",
            icon="🔄",
            agent_label="PHASE",
        ),
        ("*", "crisis"): StyleInfo(
            bg_color="rgba(244, 67, 54, 0.2)",
            border_color="#f44336",
            icon="🚨",
            agent_label="CRISIS",
        ),
        ("*", "prompt"): StyleInfo(
            bg_color="rgba(121, 85, 72, 0.1)",
            border_color="#795548",
            icon="📝",
            agent_label="PROMPT",
        ),
    }

    def get_style(self, event_type: str, data: str) -> StyleInfo:
        """Get style info for log entry - single source of truth."""
        # First try exact event_type match
        style = self.STYLE_CONFIG.get((event_type, None))
        if style:
            return style

        # Then try content-based patterns
        content_type = self._detect_content_type(data)
        if content_type:
            style = self.STYLE_CONFIG.get(("*", content_type))
            if style:
                return style

        # Default fallback
        return self.STYLE_CONFIG[("info", None)]

    def _detect_content_type(self, data: str) -> Optional[str]:
        """Detect content type from data patterns."""
        if "👤 Użytkownik:" in data:
            return "user_message"
        elif "🔍 Supervisor decision:" in data:
            return "supervisor_decision"
        elif "🎯 ZMIANA ETAPU TERAPII:" in data:
            return "stage_change"
        elif (
            "🔍 Rozpoczynam konsultację z supervisorem" in data
            or "💬 Generuję odpowiedź terapeuty" in data
        ):
            return "workflow_phase"
        elif "🚨" in data and ("KRYZYS" in data or "PROTOKÓŁ" in data):
            return "crisis"
        elif "📝" in data and ("PROMPT" in data or "Prompt content" in data):
            return "prompt"
        return None
