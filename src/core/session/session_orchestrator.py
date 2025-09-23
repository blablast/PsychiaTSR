"""Session orchestration separate from workflow logic."""

from typing import Dict, Any
from ..workflow.workflow_result import WorkflowResult
from .stage_progression_handler import StageProgressionHandler


class SessionOrchestrator:
    """Handles session-specific operations separate from workflow."""

    def __init__(self, session_manager, stage_progression_handler: StageProgressionHandler, logger):
        """
        Initialize session orchestrator.

        Args:
            session_manager: Session state manager
            stage_progression_handler: Stage progression logic handler
            logger: Logger for session events
        """
        self._session_manager = session_manager
        self._stage_progression_handler = stage_progression_handler
        self._logger = logger

    def handle_stage_progression(self, supervisor_decision) -> Dict[str, Any]:
        """
        Handle stage progression based on supervisor decision.

        Args:
            supervisor_decision: SupervisorDecision object

        Returns:
            Dict with progression results
        """
        if self._stage_progression_handler.should_advance_stage(supervisor_decision):
            progression_result = self._stage_progression_handler.advance_stage()

            return {
                "stage_changed": progression_result.success,
                "old_stage": progression_result.old_stage,
                "new_stage": progression_result.new_stage,
                "progression_error": progression_result.error
            }
        else:
            return {
                "stage_changed": False,
                "old_stage": self._session_manager.get_current_stage(),
                "new_stage": self._session_manager.get_current_stage(),
                "progression_error": None
            }

    def update_conversation_history(self, user_message: str, therapist_response: str, prompt_id: str = "unknown") -> None:
        """
        Update conversation with new exchange.

        Args:
            user_message: User's message
            therapist_response: Therapist's response
            prompt_id: ID of prompt used for response
        """
        try:
            # Check if user message is already in session
            messages = self._session_manager.get_conversation_history()
            if not messages or messages[-1].text != user_message:
                self._session_manager.add_user_message(user_message)

            self._session_manager.add_assistant_message(therapist_response, prompt_id)

        except Exception as e:
            self._logger.log_error(f"Failed to update conversation history: {str(e)}")

    def finalize_exchange(self, workflow_result: WorkflowResult, original_user_message: str) -> None:
        """
        Finalize the complete exchange including stage transitions.

        Args:
            workflow_result: Result from workflow execution
            original_user_message: Original user message
        """
        try:
            if not workflow_result.success:
                return

            data = workflow_result.data

            # Handle stage progression
            if data.get("stage_changed", False):
                current_stage = data.get("current_stage")
                if current_stage:
                    self._stage_progression_handler.add_stage_transition_message(current_stage)

            # Update conversation
            therapist_response = data.get("therapist_response", "")
            prompt_id = data.get("prompt_id", "unknown")

            self.update_conversation_history(
                user_message=original_user_message,
                therapist_response=therapist_response,
                prompt_id=prompt_id
            )

        except Exception as e:
            self._logger.log_error(f"Failed to finalize exchange: {str(e)}")