"""Conversation manager interface for dependency inversion."""

from abc import ABC, abstractmethod
from typing import List, Tuple
from ...models.schemas import MessageData


class IConversationManager(ABC):
    """Interface for conversation state management following DIP."""

    @abstractmethod
    def accept_user_input(self, text: str) -> bool:
        """
        Accept user input and add to current question.

        Args:
            text: User input text to add

        Returns:
            True if accepted, False if rejected (processing active)
        """
        pass

    @abstractmethod
    def get_current_question(self) -> str:
        """Get the current pending user question."""
        pass

    @abstractmethod
    def has_pending_question(self) -> bool:
        """Check if there's a non-empty pending question."""
        pass

    @abstractmethod
    def clear_current_question(self) -> None:
        """Clear the current question buffer."""
        pass

    @abstractmethod
    def get_committed_context(self) -> List[MessageData]:
        """
        Get committed conversation history without current question.

        Returns:
            Copy of committed context (finalized user-therapist pairs)
        """
        pass

    @abstractmethod
    def start_processing(self) -> Tuple[List[MessageData], str]:
        """
        Start workflow processing - freeze current question.

        Returns:
            Tuple of (committed_context, current_question)

        Raises:
            ValueError: If no question to process or already processing
        """
        pass

    @abstractmethod
    def commit_therapist_response(self, therapist_response: str) -> None:
        """
        Commit the current exchange (user question + therapist response).

        Args:
            therapist_response: The therapist's response text

        Raises:
            ValueError: If not in processing state or no current question
        """
        pass

    @abstractmethod
    def abort_processing(self) -> None:
        """
        Abort current processing without committing.

        Keeps current question intact for retry.
        """
        pass

    @abstractmethod
    def get_full_conversation_for_display(self) -> List[MessageData]:
        """
        Get complete conversation including pending question for UI display.

        Returns:
            Complete conversation with pending question marked
        """
        pass

    @abstractmethod
    def get_stats(self) -> dict:
        """
        Get conversation statistics.

        Returns:
            Dictionary with conversation metrics
        """
        pass

    @abstractmethod
    def is_processing(self) -> bool:
        """Check if workflow is currently processing."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """
        Reset conversation state completely.

        Clears all committed context and current question.
        """
        pass
