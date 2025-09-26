"""Crisis response configuration."""

import json
from pathlib import Path
from typing import Dict, Any


class CrisisConfig:
    """Configuration for crisis response messages and contacts."""

    @staticmethod
    def _load_crisis_config() -> Dict[str, Any]:
        """Load crisis configuration from template file."""
        try:
            template_path = Path("config/templates/defaults/crisis_config_default.json")
            if template_path.exists():
                with open(template_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass

        # Fallback to hardcoded values
        return {
            "crisis_response": {
                "message": "**⚠️ NATYCHMIASTOWA POMOC POTRZEBNA**\n\nRozumiem, że przeżywasz bardzo trudny moment. Twoje bezpieczeństwo jest najważniejsze.\n\n**PILNE KONTAKTY:**\n• **Telefon Zaufania**: 116 123 (bezpłatny, całodobowy)\n• **Pogotowie Ratunkowe**: 112\n• **Najbliższy SOR** (Szpitalny Oddział Ratunkowy)\n\n**Nie jesteś sam/sama.** Jeśli masz myśli o skrzywdzeniu siebie, proszę natychmiast skontaktuj się z którymś z powyższych numerów lub udaj się do najbliższego szpitala.\n\nCzy możesz mi powiedzieć, czy jesteś teraz w bezpiecznym miejscu?"
            },
            "crisis_contacts": {
                "telefon_zaufania": {
                    "number": "116 123",
                    "description": "Bezpłatny, całodobowy",
                    "type": "emotional_support",
                },
                "pogotowie": {
                    "number": "112",
                    "description": "Pogotowie Ratunkowe",
                    "type": "emergency",
                },
                "sor": {
                    "number": None,
                    "description": "Najbliższy Szpitalny Oddział Ratunkowy",
                    "type": "medical_emergency",
                },
            },
            "crisis_protocols": {
                "immediate_response": "crisis_protocol_v1",
                "followup_required": True,
                "escalation_threshold": "high",
                "log_level": "critical",
            },
        }

    @staticmethod
    def get_crisis_response() -> str:
        """Get standardized crisis response message."""
        config = CrisisConfig._load_crisis_config()
        return config.get("crisis_response", {}).get("message", "")

    @staticmethod
    def get_crisis_contacts() -> Dict[str, Any]:
        """Get emergency contact information."""
        config = CrisisConfig._load_crisis_config()
        return config.get("crisis_contacts", {})

    @staticmethod
    def get_crisis_protocols() -> Dict[str, Any]:
        """Get crisis handling protocols."""
        config = CrisisConfig._load_crisis_config()
        return config.get("crisis_protocols", {})
