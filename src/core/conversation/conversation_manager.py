"""
ConversationManager - centralized conversation state management.

Manages the separation between:
- Committed context (finalized user-therapist exchanges)
- Current question (user's pending input buffer)
- Processing state (workflow in progress)
"""

from typing import List, Tuple
from datetime import datetime
from ..models.schemas import MessageData
from .interfaces.conversation_manager_interface import IConversationManager


class ConversationManager(IConversationManager):
    """
    Centralized conversation state manager.

    Maintains clear separation between committed conversation history
    and the current user question being processed.

    States:
    - Accepting: User can add/extend current question
    - Processing: Workflow active, current question frozen
    - Committing: Finalizing user-therapist exchange

    Example:
        >>> manager = ConversationManager()
        >>> manager.accept_user_input("Witaj, jak się masz?")
        >>> context, question = manager.start_processing()
        >>> manager.commit_therapist_response("Dziękuję za pytanie...")
        >>> conversation = manager.get_full_conversation_for_display()
    """

    def __init__(self):
        """Initialize empty conversation state."""
        self._committed_context: List[MessageData] = []  # Finalized exchanges
        self._current_question: str = ""  # User's pending input buffer
        self._is_processing: bool = False  # Workflow state lock

    def accept_user_input(self, text: str) -> bool:
        """
        Accept user input and add to current question.

        If current_question is empty - start new question.
        If current_question exists - extend it.

        Args:
            text: User input text to add

        Returns:
            True if accepted, False if rejected (processing active)
        """
        if self._is_processing:
            return False  # Cannot modify during workflow processing

        text = text.strip()
        if not text:
            return True  # Accept empty input silently

        if self._current_question:
            # Check if this is the same text to avoid duplication
            if self._current_question.strip() != text.strip():
                # Extend existing question only if different
                self._current_question += " " + text
        else:
            self._current_question = text

        return True

    def get_current_question(self) -> str:
        """Get the current pending user question."""
        return self._current_question

    def has_pending_question(self) -> bool:
        """Check if there's a non-empty pending question."""
        return bool(self._current_question.strip())

    def clear_current_question(self) -> None:
        """Clear the current question buffer."""
        if self._is_processing:
            raise ValueError("Cannot clear question during processing")
        self._current_question = ""

    def get_committed_context(self) -> List[MessageData]:
        """
        Get committed conversation history without current question.

        Returns:
            Copy of committed context (finalized user-therapist pairs)
        """
        return self._committed_context.copy()

    def start_processing(self) -> Tuple[List[MessageData], str]:
        """
        Start workflow processing - freeze current question.

        Returns:
            Tuple of (committed_context, current_question)

        Raises:
            ValueError: If no question to process or already processing
        """
        if self._is_processing:
            raise ValueError("Already in processing state")

        if not self.has_pending_question():
            raise ValueError("No current question to process")

        self._is_processing = True
        return self._committed_context.copy(), self._current_question

    def commit_therapist_response(self, therapist_response: str) -> None:
        """
        Commit the current exchange (user question + therapist response).

        Adds both messages to committed context and resets state.

        Args:
            therapist_response: The therapist's response text

        Raises:
            ValueError: If not in processing state or no current question
        """
        if not self._is_processing:
            raise ValueError("Not in processing state")

        if not self._current_question:
            raise ValueError("No current question to commit")

        therapist_response = therapist_response.strip()
        if not therapist_response:
            raise ValueError("Therapist response cannot be empty")

        # Create user message
        user_msg = MessageData(
            role="user",
            text=self._current_question,
            timestamp=datetime.now().isoformat(),
            prompt_used="",
        )

        # Create therapist message
        therapist_msg = MessageData(
            role="therapist",
            text=therapist_response,
            timestamp=datetime.now().isoformat(),
            prompt_used="",
        )

        # Commit both messages atomically
        self._committed_context.extend([user_msg, therapist_msg])

        # Reset state
        self._current_question = ""
        self._is_processing = False

    def abort_processing(self) -> None:
        """
        Abort current processing without committing.

        Keeps current question intact for retry.
        """
        if not self._is_processing:
            raise ValueError("Not in processing state")

        self._is_processing = False

    def get_full_conversation_for_display(self) -> List[MessageData]:
        """
        Get complete conversation including pending question for UI display.

        Returns:
            Complete conversation with pending question marked
        """
        result = self._committed_context.copy()

        if self.has_pending_question():
            pending_msg = MessageData(
                role="user",
                text=self._current_question,
                timestamp=datetime.now().isoformat(),
                prompt_used="",
            )
            # Add pending marker as attribute after creation
            pending_msg.is_pending = True
            result.append(pending_msg)

        return result

    def get_stats(self) -> dict:
        """
        Get conversation statistics.

        Returns:
            Dictionary with conversation metrics
        """
        user_messages = [msg for msg in self._committed_context if msg.role == "user"]

        return {
            "committed_exchanges": len(user_messages),
            "total_committed_messages": len(self._committed_context),
            "has_pending_question": self.has_pending_question(),
            "current_question_length": len(self._current_question),
            "is_processing": self._is_processing,
        }

    def is_processing(self) -> bool:
        """Check if workflow is currently processing."""
        return self._is_processing

    def reset(self) -> None:
        """
        Reset conversation state completely.

        Clears all committed context and current question.
        """
        if self._is_processing:
            raise ValueError("Cannot reset during processing")

        self._committed_context.clear()
        self._current_question = ""
        self._is_processing = False
