"""LLM memory management service following Single Responsibility Principle."""

from typing import List
from ...utils.schemas import MessageData


class MemoryService:
    """Handles LLM conversation memory management for agents."""

    def __init__(self, logger=None):
        self._logger = logger

    def setup_system_prompt(self, llm_provider, system_prompt: str, agent_type: str) -> bool:
        """Set up system prompt for LLM provider."""
        try:
            if hasattr(llm_provider, 'start_conversation'):
                llm_provider.start_conversation(system_prompt)
                if self._logger:
                    self._logger.log_info(f"System prompt set for {agent_type}", {
                        "description": "Set once per session"
                    })
                return True
            else:
                # For providers without memory, system prompt will be included per request
                if self._logger:
                    self._logger.log_info(f"Provider doesn't support memory - system prompt will be included per message", {
                        "agent_type": agent_type,
                        "provider_type": "traditional"
                    })
                return False
        except Exception as e:
            if self._logger:
                self._logger.log_error(f"Failed to set system prompt for {agent_type}: {str(e)}")
            return False

    def setup_stage_prompt(self, llm_provider, stage_prompt: str, stage_id: str, agent_type: str) -> bool:
        """Set up stage-specific prompt for memory-optimized providers."""
        try:
            if hasattr(llm_provider, 'conversation_messages') or hasattr(llm_provider, 'chat_session'):
                stage_instruction = ""
                confirmation = ""

                if agent_type == "supervisor":
                    stage_instruction = f"NOWY ETAP OCENY SUPERVISORA:\n{stage_prompt}\n\nOd teraz oceniaj postęp zgodnie z wytycznymi tego etapu."
                    confirmation = "Rozumiem. Oceniam postęp zgodnie z wytycznymi tego etapu."
                elif agent_type == "therapist":
                    stage_instruction = f"NOWY ETAP TERAPII:\n{stage_prompt}\n\nOd teraz prowadź rozmowę zgodnie z wytycznymi tego etapu."
                    confirmation = "Rozumiem. Prowadzę rozmowę zgodnie z wytycznymi tego etapu."
                else:
                    ValueError(f"Unknown agent type: {agent_type}")

                if hasattr(llm_provider, 'add_user_message') and hasattr(llm_provider, 'add_assistant_message'):
                    llm_provider.add_user_message(stage_instruction)
                    llm_provider.add_assistant_message(confirmation)

                if self._logger:
                    self._logger.log_info(f"Stage prompt set for {agent_type} - {stage_id}", {
                        "description": f"Setting stage prompt for {agent_type}"
                    })
                return True
            else:
                # Provider doesn't support memory - stage prompt will be included per request
                return False
        except Exception as e:
            if self._logger:
                self._logger.log_error(f"Failed to set stage prompt for {agent_type}: {str(e)}")
            return False

    @staticmethod
    def supports_memory(llm_provider) -> bool:
        """Check if LLM provider supports conversation memory."""
        return hasattr(llm_provider, 'conversation_messages') or hasattr(llm_provider, 'chat_session')

    @staticmethod
    def build_conversation_context(conversation_history: List[MessageData], max_messages: int = None) -> str:
        """Build conversation context string from message history."""
        if not conversation_history:
            return "Początek rozmowy."

        # Apply message limit if specified
        filtered_history = conversation_history if not max_messages else conversation_history[-max_messages:]

        if not filtered_history:
            return "Brak dostępnej historii rozmowy."

        # Format messages
        context_lines = []
        role_display_map = {
            "user": "Użytkownik",
            "therapist": "Terapeuta",
            "supervisor": "Nadzorca"
        }

        for msg in filtered_history:
            role_display = role_display_map.get(msg.role, msg.role.title())
            context_lines.append(f"{role_display}: {msg.text}")

        return "\n".join(context_lines)