"""Async interfaces for agents following Interface Segregation Principle."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator
from ...core.models.schemas import MessageData, SupervisorDecision


class IAsyncTherapistAgent(ABC):
    """Async interfaces for therapist agent operations."""

    @abstractmethod
    async def generate_response_async(self,
                                     user_message: str,
                                     stage_prompt: str,
                                     conversation_history: List[MessageData],
                                     stage_id: str = None) -> Dict[str, Any]:
        """Generate therapeutic response asynchronously."""
        pass

    @abstractmethod
    async def generate_streaming_response_async(self,
                                               user_message: str,
                                               stage_prompt: str,
                                               conversation_history: List[MessageData],
                                               stage_id: str = None) -> AsyncGenerator[Any, None]:
        """Generate streaming therapeutic response asynchronously."""
        pass


class IAsyncSupervisorAgent(ABC):
    """Async interfaces for supervisor agent operations."""

    @abstractmethod
    async def evaluate_stage_completion_async(self,
                                             stage: str,
                                             history: List[MessageData],
                                             stage_prompt: str) -> SupervisorDecision:
        """Evaluate stage completion asynchronously."""
        pass

    @abstractmethod
    async def generate_response_async(self,
                                     user_message: str,
                                     stage_prompt: str,
                                     conversation_history: List[MessageData],
                                     stage_id: str = None) -> Dict[str, Any]:
        """Generate supervisor response asynchronously."""
        pass

