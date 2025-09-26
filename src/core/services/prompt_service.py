"""Prompt management service following Single Responsibility Principle."""

from typing import Optional
from ..prompts.unified_prompt_manager import UnifiedPromptManager


class PromptService:
    """Handles all prompt-related operations for agents."""

    def __init__(self, prompt_manager: UnifiedPromptManager):
        self._prompt_manager = prompt_manager

    def get_system_prompt(self, agent_type: str) -> Optional[str]:
        """Get system prompt for agent type."""
        return self._prompt_manager.get_system_prompt(agent_type)

    def get_stage_prompt(self, stage_id: str, agent_type: str) -> Optional[str]:
        """Get stage-specific prompt for agent."""
        return self._prompt_manager.get_stage_prompt(stage_id, agent_type)

    def build_supervisor_prompt(
        self, stage_id: str, conversation_context: str, safety_context: str
    ) -> str:
        """Build complete prompt for supervisor evaluation."""
        stage_prompt = self.get_stage_prompt(stage_id, "supervisor")

        prompt_parts = []
        if conversation_context:
            prompt_parts.append(f"OSTATNIE WIADOMOŚCI:\n{conversation_context}")
        if safety_context:
            prompt_parts.append(safety_context)

        return "\n\n".join(prompt_parts)

    @staticmethod
    def build_therapist_prompt(user_message: str, conversation_context: str) -> str:
        """Build complete prompt for therapist response."""
        return f"KONTEKST ROZMOWY:\n{conversation_context}\n\nAKTUALNA WIADOMOŚĆ UŻYTKOWNIKA:\n{user_message}"
