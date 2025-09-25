from abc import ABC, abstractmethod
from typing import Optional, AsyncGenerator, Dict, List, Any
import aiohttp


class LLMProvider(ABC):
    """Base class for LLM providers with shared functionality"""

    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self.config = kwargs

        # HTTP Session Management
        self._session = None

        # Conversation Management
        self.conversation_messages = []
        self.system_prompt_set = False

    # === HTTP Session Management (shared by all providers) ===

    async def _get_session(self, headers: Optional[Dict[str, str]] = None) -> 'aiohttp.ClientSession':
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=60)
            session_headers = headers or {}
            self._session = aiohttp.ClientSession(headers=session_headers, timeout=timeout)
        return self._session

    async def _close_session(self):
        """Close aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def close(self):
        """Close any async resources."""
        await self._close_session()

    # === Conversation Management (shared by all providers) ===

    def start_conversation(self, system_prompt: Optional[str] = None) -> None:
        """Start a new conversation with optional system prompt."""
        self.conversation_messages = []
        self.system_prompt_set = False

        if system_prompt:
            self.set_system_prompt(system_prompt)

    def set_system_prompt(self, system_prompt: str) -> None:
        """Set system prompt once for the conversation."""
        if not self.system_prompt_set:
            # Add or update system prompt at the beginning
            if self.conversation_messages and self.conversation_messages[0]["role"] == "system":
                self.conversation_messages[0] = {"role": "system", "content": system_prompt}
            else:
                self.conversation_messages.insert(0, {"role": "system", "content": system_prompt})
            self.system_prompt_set = True

    def add_user_message(self, message: str) -> None:
        """Add user message to conversation history."""
        self.conversation_messages.append({"role": "user", "content": message})

    def add_assistant_message(self, message: str) -> None:
        """Add assistant message to conversation history."""
        self.conversation_messages.append({"role": "assistant", "content": message})

    def reset_conversation(self) -> None:
        """Reset conversation memory."""
        self.conversation_messages = []
        self.system_prompt_set = False

    def get_conversation_length(self) -> int:
        """Get current conversation length."""
        return len(self.conversation_messages)

    def get_conversation_messages(self) -> List[Dict[str, str]]:
        """Get full conversation history."""
        return self.conversation_messages.copy()

    # === API Utilities (shared by all providers) ===

    @staticmethod
    def _prepare_common_params(**kwargs) -> Dict[str, Any]:
        """Prepare common API parameters."""
        return {
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 150),
            "top_p": kwargs.get("top_p", 0.9)
        }

    def _prepare_messages(self, prompt: str, system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
        """Prepare messages for API call."""
        # Set system prompt if provided and not already set
        if system_prompt and not self.system_prompt_set:
            self.set_system_prompt(system_prompt)

        # Add current user message to conversation
        self.add_user_message(prompt)

        return self.conversation_messages.copy()

    # === Abstract Methods (provider-specific) ===

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate a response from the LLM asynchronously"""
        pass

    @abstractmethod
    def generate_sync(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """Generate a response from the LLM synchronously"""
        pass

    def generate_stream(self, prompt: str, system_prompt: Optional[str] = None, **kwargs):
        """Generate a streaming response from the LLM (sync)"""
        # Default implementation - providers can override
        full_response = self.generate_sync(prompt, system_prompt, **kwargs)
        yield full_response

    async def generate_stream_async(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM (async)"""
        # Default implementation - providers can override
        full_response = await self.generate(prompt, system_prompt, **kwargs)
        yield full_response

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available"""
        pass