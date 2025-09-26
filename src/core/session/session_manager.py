"""
Main session manager coordinating session state, stages, and conversation history.

Follows Single Responsibility Principle by delegating specific concerns
to specialized managers while providing a unified interfaces.
"""

from typing import List, Optional

from .interfaces.session_state_interface import ISessionState
from .stages.stage_manager import StageManager
from ..models.session_info import SessionInfo
from datetime import datetime
from ..models.schemas import MessageData
from ...infrastructure.storage import StorageProvider


class SessionManager:
    """
    Main session manager coordinating session state, stages, and conversation history.

    Follows Single Responsibility Principle by delegating specific concerns
    to specialized managers while providing a unified interfaces.
    """

    def __init__(
        self,
        session_state: ISessionState,
        stage_manager: StageManager,
        storage_provider: Optional[StorageProvider] = None,
    ):
        """Initialize session manager with dependencies.

        Args:
            session_state: Session state management interface
            stage_manager: Therapy stage management service
            storage_provider: Optional persistent storage provider
        """
        self._session_state = session_state
        self._stage_manager = stage_manager
        self._storage_provider = storage_provider

    def create_new_session(self, user_id: Optional[str] = None) -> str:
        """Create a new therapy session.

        Args:
            user_id: Optional user identifier for session tracking

        Returns:
            Unique session identifier

        Raises:
            ValueError: If session creation fails
        """
        if not self._storage_provider:
            raise ValueError("Storage provider not configured")

        try:
            session_id = self._storage_provider.create_session(user_id)
            self._session_state.set_session_id(session_id)

            # Get first stage dynamically
            first_stage = self._stage_manager.get_first_stage()
            first_stage_id = first_stage.stage_id if first_stage else "opening"

            self._session_state.set_current_stage(first_stage_id)
            self._session_state.clear_messages()

            # Persist initial state
            self._storage_provider.update_stage(session_id, first_stage_id)

            return session_id

        except Exception as e:
            raise ValueError(f"Failed to create new session: {str(e)}")

    def get_session_info(self) -> SessionInfo:
        """Get current session information.

        Returns:
            SessionInfo containing session metadata
        """
        return SessionInfo(
            session_id=self._session_state.get_session_id(),
            current_stage=self._session_state.get_current_stage(),
            message_count=len(self._session_state.get_messages()),
        )

    def get_current_stage(self) -> str:
        """Get current therapy stage.

        Returns:
            Current stage identifier
        """
        return self._session_state.get_current_stage()

    def get_session_id(self) -> str:
        """Get current session ID.

        Returns:
            Current session identifier
        """
        return self._session_state.get_session_id()

    def get_current_stage_info(self):
        """Get detailed information about current stage.

        Returns:
            StageInfo object with current stage details
        """
        current_stage = self.get_current_stage()
        return self._stage_manager.get_stage_by_id(current_stage)

    def advance_to_next_stage(self):
        """Advance to the next therapy stage.

        Returns:
            WorkflowResult indicating success or failure
        """
        return self._change_stage("next", "Advanced", "advance")

    def retreat_to_previous_stage(self):
        """Go back to the previous therapy stage.

        Returns:
            WorkflowResult indicating success or failure
        """
        return self._change_stage("previous", "Returned", "retreat")

    def _change_stage(self, direction: str, action_verb: str, action_name: str):
        """Helper method to change stage in either direction.

        Args:
            direction: Stage change direction ('next' or 'previous')
            action_verb: Verb for success message ('Advanced' or 'Returned')
            action_name: Action name for error messages ('advance' or 'retreat')

        Returns:
            WorkflowResult with stage change outcome
        """
        from ..models import WorkflowResult

        try:
            current_stage = self.get_current_stage()

            if direction == "next":
                target_stage = self._stage_manager.get_next_stage(current_stage)
                not_found_msg = "No next stage available"
            else:
                target_stage = self._stage_manager.get_previous_stage(current_stage)
                not_found_msg = "No previous stage available"

            if not target_stage:
                return WorkflowResult(success=False, message=not_found_msg, error="STAGE_NOT_FOUND")

            self._session_state.set_current_stage(target_stage.stage_id)

            if self._storage_provider and self._session_state.get_session_id():
                self._storage_provider.update_stage(
                    self._session_state.get_session_id(), target_stage.stage_id
                )

            return WorkflowResult(
                success=True,
                message=f"{action_verb} to stage: {target_stage.name}",
                data={"new_stage": target_stage.stage_id, "stage_name": target_stage.name},
            )

        except Exception as e:
            return WorkflowResult(
                success=False, message=f"Failed to {action_name} stage", error=str(e)
            )

    def get_conversation_history(
        self, exclude_stage_transitions: bool = False
    ) -> List[MessageData]:
        """Get conversation history as structured data.

        Args:
            exclude_stage_transitions: Whether to filter out stage transition messages

        Returns:
            List of MessageData objects representing conversation history
        """
        messages = self._session_state.get_messages()

        # Filter out stage transition messages if requested
        if exclude_stage_transitions:
            messages = [msg for msg in messages if not msg.get("is_stage_transition", False)]

        return [
            MessageData(
                role=msg["role"],
                text=msg["content"],
                timestamp=msg.get("timestamp", ""),
                prompt_used=msg.get("prompt_used", ""),
            )
            for msg in messages
        ]

    def add_user_message(self, content: str) -> None:
        """Add user message to conversation.

        Args:
            content: The user's message content
        """
        message = {
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "prompt_used": "",
        }
        self._session_state.add_message(message)

        # Persist to storage if available
        if self._storage_provider and self._session_state.get_session_id():
            try:
                self._storage_provider.append_message(
                    self._session_state.get_session_id(), "user", content
                )
            except Exception:
                # Log but don't fail on storage errors
                pass

    def add_assistant_message(self, content: str, prompt_id: str = "") -> None:
        """Add assistant message to conversation.

        Args:
            content: The assistant's response content
            prompt_id: Optional identifier for the prompt used
        """
        message = {
            "role": "assistant",
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "prompt_used": prompt_id,
        }
        self._session_state.add_message(message)

        # Persist to storage if available
        if self._storage_provider and self._session_state.get_session_id():
            try:
                self._storage_provider.append_message(
                    self._session_state.get_session_id(), "assistant", content, prompt_id
                )
            except Exception:
                # Log but don't fail on storage errors
                pass

    def reset_session(self) -> None:
        """Reset current session to initial state.

        Resets to first stage and clears all messages.
        """
        # Get first stage dynamically
        first_stage = self._stage_manager.get_first_stage()
        first_stage_id = first_stage.stage_id if first_stage else "opening"

        self._session_state.set_current_stage(first_stage_id)
        self._session_state.clear_messages()

    def clear_conversation_history(self) -> None:
        """Clear only the conversation history, keeping session and stage.

        Preserves session ID and current stage while removing all messages.
        """
        self._session_state.clear_messages()

    def add_stage_transition_message(self, content: str) -> None:
        """Add stage transition message to conversation.

        Args:
            content: Stage transition notification message
        """
        message = {
            "role": "system",
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "prompt_used": "",
            "is_stage_transition": True,
        }
        self._session_state.add_message(message)
