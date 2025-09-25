"""LLM memory management service following Single Responsibility Principle."""

from typing import List, Optional
from ...core.models.schemas import MessageData
from ..logging.interfaces.logger_interface import ILogger


class MemoryService:
    """Handles LLM conversation memory management for agents."""

    def __init__(self, logger: Optional[ILogger] = None):
        self._logger = logger

    def setup_system_prompt(self, llm_provider, system_prompt: str, agent_type: str) -> bool:
        """Set up system prompt for LLM provider."""
        try:
            if hasattr(llm_provider, 'start_conversation'):
                llm_provider.start_conversation(system_prompt)
                if self._logger:
                    # Log detailed system prompt for technical logs
                    self._logger.log_system_prompt(agent_type, system_prompt, "Set once per session")

                    # Also log summary info
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
                    # Log detailed stage prompt for technical logs
                    self._logger.log_stage_prompt(agent_type, stage_id, stage_prompt, f"Stage prompt for {agent_type}")

                    # Also log summary info
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

    @staticmethod
    def build_optimized_conversation_context(conversation_history: List[MessageData],
                                           max_messages: int = None,
                                           enable_summarization: bool = True) -> str:
        """
        Build optimized conversation context with summarization for older messages.

        Args:
            conversation_history: List of previous conversation messages
            max_messages: Maximum number of recent messages to include fully
            enable_summarization: Whether to summarize older messages instead of dropping them

        Returns:
            Optimized conversation context string
        """
        if not conversation_history:
            return "Początek rozmowy."

        # If no limit or within limit, use standard method
        if not max_messages or len(conversation_history) <= max_messages:
            return MemoryService.build_conversation_context(conversation_history, max_messages)

        if not enable_summarization:
            # Use standard method with hard cutoff
            return MemoryService.build_conversation_context(conversation_history, max_messages)

        # Split into old (to summarize) and recent (to keep fully)
        split_point = len(conversation_history) - max_messages
        old_messages = conversation_history[:split_point]
        recent_messages = conversation_history[split_point:]

        context_parts = []

        # Summarize old messages
        if old_messages:
            summary = MemoryService._summarize_conversation_segment(old_messages)
            context_parts.append(f"[PODSUMOWANIE WCZEŚNIEJSZEJ ROZMOWY: {summary}]")

        # Add recent messages in full
        role_display_map = {
            "user": "Użytkownik",
            "therapist": "Terapeuta",
            "supervisor": "Nadzorca"
        }

        for msg in recent_messages:
            role_display = role_display_map.get(msg.role, msg.role.title())
            context_parts.append(f"{role_display}: {msg.text}")

        return "\n".join(context_parts)

    @staticmethod
    def _summarize_conversation_segment(messages: List[MessageData]) -> str:
        """
        Create a concise summary of conversation segment.

        Args:
            messages: Messages to summarize

        Returns:
            Brief summary of the conversation segment
        """
        if not messages:
            return "Brak wiadomości do podsumowania."

        # Count message types
        user_messages = [msg for msg in messages if msg.role == "user"]
        therapist_messages = [msg for msg in messages if msg.role == "therapist"]

        # Extract key themes (simple keyword extraction)
        all_text = " ".join(msg.text.lower() for msg in messages if msg.role in ["user", "therapist"])

        # Common therapy-related keywords to look for
        key_themes = []
        theme_keywords = {
            "cel": ["cel", "chcę", "chciałbym", "potrzebuję", "problem"],
            "emocje": ["czuję", "smutny", "szczęśliwy", "zły", "zmartwiony", "lęk", "stres"],
            "zasoby": ["umiem", "potrafię", "radzę sobie", "mocna strona", "sukces"],
            "skale": ["skala", "od 1 do 10", "oceniam", "punktów"],
            "działania": ["zrobię", "planuję", "spróbuję", "krok", "działanie"]
        }

        for theme, keywords in theme_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                key_themes.append(theme)

        # Build summary
        summary_parts = []
        if user_messages and therapist_messages:
            summary_parts.append(f"{len(user_messages)} wypowiedzi użytkownika, {len(therapist_messages)} odpowiedzi terapeuty")

        if key_themes:
            summary_parts.append(f"Tematy: {', '.join(key_themes)}")
        else:
            # Fallback: use first few words from first and last user message
            first_user = next((msg for msg in messages if msg.role == "user"), None)
            last_user = next((msg for msg in reversed(messages) if msg.role == "user"), None)

            if first_user:
                first_words = first_user.text
                summary_parts.append(f"Rozpoczęcie: {first_words}")

                if last_user and last_user != first_user:
                    last_words = last_user.text
                    summary_parts.append(f"Ostatnio: {last_words}")

        return "; ".join(summary_parts) if summary_parts else f"{len(messages)} wymian wiadomości"