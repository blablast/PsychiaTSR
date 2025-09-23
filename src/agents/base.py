"""Base agent class for all therapeutic agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from ..llm.base import LLMProvider
from ..utils.safety import SafetyChecker
from ..utils.schemas import MessageData


class BaseAgent(ABC):
    """Base class for all therapeutic agents following SOLID principles."""

    def __init__(self, llm_provider: LLMProvider, safety_checker: SafetyChecker):
        """Initialize base agent with required dependencies."""
        self.llm_provider = llm_provider
        self.safety_checker = safety_checker
        self._last_used_prompt_info: Optional[Dict[str, str]] = None
        self._system_prompt: Optional[str] = None
        self._agent_type = self.__class__.__name__.lower().replace('agent', '')

    def set_system_prompt(self, system_prompt: str) -> None:
        """Set system prompt once at conversation start.

        Optimizes memory usage by setting prompt once in LLM provider
        if it supports conversation memory.
        """
        self._system_prompt = system_prompt

        # Log system prompt setting with dedicated method
        self._log_system_prompt(system_prompt, "Set once per session")

        # Initialize LLM provider conversation if it supports memory optimization
        if hasattr(self.llm_provider, 'start_conversation'):
            self.llm_provider.start_conversation(system_prompt)
            self._log_prompt_setting("SYSTEM", "Conversation started", "Provider conversation started with system prompt")
        elif hasattr(self.llm_provider, 'set_system_prompt'):
            self.llm_provider.set_system_prompt(system_prompt)
            self._log_prompt_setting("SYSTEM", "Provider set", "System prompt set directly in provider")

    def get_last_used_prompt_info(self) -> Dict[str, str]:
        """Get information about the last used prompt for debugging."""
        return self._last_used_prompt_info or {
            "id": "unknown",
            "created_at": "unknown",
            "review": "No prompt info available",
            "prompt_preview": "N/A",
            "full_prompt": "N/A"
        }

    def _prepare_prompt_info(self, prompt_id: str, prompt_type: str,
                           prompt_content: str, review: str) -> None:
        """Helper to set prompt info consistently across all agents."""
        self._last_used_prompt_info = {
            "id": f"{self._agent_type}_{prompt_id}",
            "created_at": datetime.now().isoformat(),
            "review": review,
            "prompt_preview": f"{prompt_type.title()} prompt: {len(prompt_content)} chars",
            "full_prompt": prompt_content
        }

    def _get_agent_parameters(self) -> dict:
        """Get agent-specific parameters from config"""
        try:
            from config import Config
            return Config.get_agent_parameters(self._agent_type)
        except ImportError:
            # Fallback if config not available
            return {"temperature": 0.7, "max_tokens": 150, "top_p": 0.9}

    def _generate_with_memory_optimization(self, prompt: str, system_prompt: str = None,
                                         **llm_kwargs) -> str:
        """Generate response using memory optimization if available.

        Args:
            prompt: User/context prompt to send
            system_prompt: Optional system prompt (falls back to set system prompt)
            **llm_kwargs: Additional arguments for LLM (temperature, max_tokens, etc.)

        Returns:
            Generated response text
        """
        effective_system_prompt = system_prompt or self._system_prompt

        if not effective_system_prompt:
            raise ValueError(f"System prompt not set for {self._agent_type}. Call set_system_prompt() first.")

        # Get agent-specific parameters and merge with provided kwargs
        agent_params = self._get_agent_parameters()
        final_kwargs = {**agent_params, **llm_kwargs}  # llm_kwargs override agent defaults

        # Check if provider supports memory optimization
        supports_memory = (hasattr(self.llm_provider, 'conversation_messages') or
                          hasattr(self.llm_provider, 'chat_session'))

        if supports_memory:
            # Memory-optimized: system prompt already set, just send user prompt
            self._log_prompt_setting("CONVERSATION", prompt, "Memory-optimized: sending user prompt only")

            response = self.llm_provider.generate_sync(
                prompt=prompt,
                **final_kwargs
            )

            self._prepare_prompt_info(
                prompt_id="memory_optimized",
                prompt_type="memory_optimized",
                prompt_content=prompt,
                review="Memory-optimized approach - system prompt set once in conversation"
            )
        else:
            # Traditional: send complete prompt with system context
            complete_prompt = f"SYSTEM: {effective_system_prompt}\n\nUSER: {prompt}"
            self._log_prompt_setting("CONVERSATION", complete_prompt, "Traditional: sending complete prompt with system context")

            response = self.llm_provider.generate_sync(
                prompt=prompt,
                system_prompt=effective_system_prompt,
                **final_kwargs
            )

            self._prepare_prompt_info(
                prompt_id="traditional",
                prompt_type="traditional",
                prompt_content=complete_prompt,
                review="Traditional approach - provider doesn't support conversation memory"
            )

        return response

    def _log_prompt_setting(self, prompt_type: str, prompt_content: str, description: str) -> None:
        """Log prompt setting for debugging and monitoring."""
        try:
            # Use add_technical_log function which writes to session_state technical_log
            from src.ui.technical_log_display import add_technical_log

            # Create detailed log entry
            log_content = (
                f"📝 {prompt_type} PROMPT - {self._agent_type.upper()}\n"
                f"Description: {description}\n"
                f"Content preview: {prompt_content[:100]}{'...' if len(prompt_content) > 100 else ''}\n"
                f"Full length: {len(prompt_content)} characters"
            )

            add_technical_log(f"{self._agent_type}_prompt_setting", log_content)
        except Exception:
            # Silent fail - logging shouldn't break the application
            pass

    def _log_system_prompt(self, prompt_content: str, description: str) -> None:
        """Log system prompt setting with dedicated method."""
        try:
            # Use add_technical_log function which writes to session_state technical_log
            from src.ui.technical_log_display import add_technical_log

            # Create detailed log entry for system prompt
            log_content = (
                f"📝 SYSTEM PROMPT - {self._agent_type.upper()}\n"
                f"Description: {description}\n"
                f"Content preview: {prompt_content[:200]}{'...' if len(prompt_content) > 200 else ''}\n"
                f"Full length: {len(prompt_content)} characters"
            )

            add_technical_log(f"{self._agent_type}_system_prompt", log_content)
        except Exception:
            # Silent fail - logging shouldn't break the application
            pass

    def _log_stage_prompt(self, stage_id: str, prompt_content: str, description: str) -> None:
        """Log stage prompt setting with dedicated method."""
        try:
            # Use add_technical_log function which writes to session_state technical_log
            from src.ui.technical_log_display import add_technical_log

            # Create detailed log entry for stage prompt
            log_content = (
                f"📝 STAGE PROMPT - {self._agent_type.upper()} - {stage_id}\n"
                f"Description: {description}\n"
                f"Content preview: {prompt_content[:200]}{'...' if len(prompt_content) > 200 else ''}\n"
                f"Full length: {len(prompt_content)} characters"
            )

            add_technical_log(f"{self._agent_type}_stage_prompt", log_content)
        except Exception:
            # Silent fail - logging shouldn't break the application
            pass

    def _handle_llm_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """Standard error handling for LLM operations.

        Args:
            error: The exception that occurred
            context: Additional context about what was being attempted

        Returns:
            Standardized error response dict
        """
        error_msg = f"{self._agent_type.title()} agent error"
        if context:
            error_msg += f" ({context})"
        error_msg += f": {str(error)}"

        return {
            "success": False,
            "error": error_msg,
            "error_type": type(error).__name__,
            "agent_type": self._agent_type
        }

    @staticmethod
    def _build_conversation_context(conversation_history: List[MessageData],
                                    max_messages: int = None,
                                    include_roles: List[str] = None) -> str:
        """Build conversation context from message history.

        Args:
            conversation_history: List of conversation messages
            max_messages: Optional limit on number of messages to include
            include_roles: Optional filter for specific roles (e.g., ['user', 'therapist'])

        Returns:
            Formatted conversation context string
        """
        if not conversation_history:
            return "Początek rozmowy."

        # Filter by roles if specified
        if include_roles:
            filtered_history = [msg for msg in conversation_history if msg.role in include_roles]
        else:
            filtered_history = conversation_history

        # Apply message limit if specified
        if max_messages:
            filtered_history = filtered_history[-max_messages:]

        if not filtered_history:
            return "Brak dostępnej historii rozmowy."

        # Format messages
        context_lines = []
        role_display_map = {
            "user": "Użytkownik",
            "therapist": "Terapeuta",
            "supervisor": "Nadzorca",
            "crisis": "Agent Kryzysowy",
            "analysis": "Agent Analityczny",
            "report": "Agent Raportujący"
        }

        for msg in filtered_history:
            role_display = role_display_map.get(msg.role, msg.role.title())
            context_lines.append(f"{role_display}: {msg.text}")

        return "\n".join(context_lines)

    def _validate_required_prompt(self) -> None:
        """Validate that system prompt is set before generation."""
        if not self._system_prompt:
            raise ValueError(f"System prompt not set for {self._agent_type}. Call set_system_prompt() first.")

    def _supports_memory(self) -> bool:
        """Check if provider supports conversation memory."""
        return (hasattr(self.llm_provider, 'conversation_messages') or
                hasattr(self.llm_provider, 'chat_session'))

    def get_memory_info(self) -> Dict[str, Any]:
        """Get information about current memory state."""
        return {
            "supports_memory": self._supports_memory(),
            "system_prompt_set": bool(self._system_prompt),
            "conversation_length": getattr(self.llm_provider, 'get_conversation_length', lambda: 0)(),
            "agent_type": self._agent_type
        }

    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about this agent instance."""
        return {
            "agent_type": self._agent_type,
            "class_name": self.__class__.__name__,
            "llm_provider": self.llm_provider.__class__.__name__,
            "llm_model": getattr(self.llm_provider, 'model_name', 'unknown'),
            "has_system_prompt": bool(self._system_prompt),
            "supports_memory": hasattr(self.llm_provider, 'conversation_messages') or
                             hasattr(self.llm_provider, 'chat_session')
        }

    @abstractmethod
    def generate_response(self, *args, **kwargs) -> Dict[str, Any]:
        """Generate response using agent-specific logic.

        Must be implemented by subclasses with their specific parameters
        and return standardized response format.

        Returns:
            Dict with keys: success, response/result, error (optional),
            plus any agent-specific fields
        """
        pass