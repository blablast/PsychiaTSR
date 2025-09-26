"""Async interfaces for agents following Interface Segregation Principle."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, AsyncGenerator
from ...core.models.schemas import MessageData, SupervisorDecision


class IAsyncTherapistAgent(ABC):
    """Async interface for therapist agent operations.

    Defines async methods for therapeutic response generation including
    standard response generation and streaming capabilities.
    """

    @abstractmethod
    async def generate_response_async(
        self,
        user_message: str,
        stage_prompt: str,
        conversation_history: List[MessageData],
        stage_id: str = None,
    ) -> Dict[str, Any]:
        """Generate therapeutic response asynchronously.

        Args:
            user_message: User's message requiring therapeutic response
            stage_prompt: Stage-specific prompt for therapy guidance
            conversation_history: Previous conversation messages
            stage_id: Current therapy stage identifier

        Returns:
            Dict containing response text, validation results, and metadata
        """
        pass

    @abstractmethod
    async def generate_streaming_response_async(
        self,
        user_message: str,
        stage_prompt: str,
        conversation_history: List[MessageData],
        stage_id: str = None,
    ) -> AsyncGenerator[Any, None]:
        """Generate streaming therapeutic response asynchronously.

        Args:
            user_message: User's message requiring therapeutic response
            stage_prompt: Stage-specific prompt for therapy guidance
            conversation_history: Previous conversation messages
            stage_id: Current therapy stage identifier

        Yields:
            Response chunks as strings, followed by final metadata dict
        """
        pass


class IAsyncSupervisorAgent(ABC):
    """Async interface for supervisor agent operations.

    Defines async methods for stage evaluation and supervisor response
    generation in therapy workflows.
    """

    @abstractmethod
    async def evaluate_stage_completion_async(
        self, stage: str, history: List[MessageData], stage_prompt: str
    ) -> SupervisorDecision:
        """Evaluate stage completion asynchronously.

        Args:
            stage: Current therapy stage identifier
            history: Conversation history for evaluation
            stage_prompt: Stage-specific evaluation prompt

        Returns:
            SupervisorDecision with advancement recommendation
        """
        pass

    @abstractmethod
    async def generate_response_async(
        self,
        user_message: str,
        stage_prompt: str,
        conversation_history: List[MessageData],
        stage_id: str = None,
    ) -> Dict[str, Any]:
        """Generate supervisor response asynchronously.

        Args:
            user_message: User's message requiring supervisor response
            stage_prompt: Stage-specific prompt for guidance
            conversation_history: Previous conversation messages
            stage_id: Current therapy stage identifier

        Returns:
            Dict containing response text and metadata
        """
        pass
