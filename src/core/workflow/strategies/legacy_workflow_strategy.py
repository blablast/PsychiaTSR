"""Legacy workflow strategy - extracted from process_user_message."""

from ..workflow_result import WorkflowResult
from .workflow_strategy import WorkflowStrategy
from .workflow_context import WorkflowContext


class LegacyWorkflowStrategy(WorkflowStrategy):
    """Legacy workflow strategy implementation."""

    def __init__(self, supervisor_evaluator, therapist_responder, session_manager, logger):
        """
        Initialize legacy workflow strategy.

        Args:
            supervisor_evaluator: Supervisor evaluation handler
            therapist_responder: Therapist response handler
            session_manager: Session state manager
            logger: Logger for workflow events
        """
        self._supervisor_evaluator = supervisor_evaluator
        self._therapist_responder = therapist_responder
        self._session_manager = session_manager
        self._logger = logger

    def execute(self, context: WorkflowContext) -> WorkflowResult:
        """
        Execute legacy workflow strategy.

        This mirrors the original process_user_message logic.
        """
        try:
            # Step 1: Supervisor evaluation
            self._logger.log_info("🔍 Rozpoczynam konsultację z supervisorem...")

            supervisor_result = self._supervisor_evaluator.evaluate_stage(
                context.current_stage, context.user_message, context.conversation_history
            )

            if not supervisor_result.success:
                return supervisor_result

            supervisor_decision = supervisor_result.data["decision"]

            # Log supervisor decision
            self._logger.log_info(
                f"🔍 Supervisor decision: [{supervisor_decision.decision}] {supervisor_decision.reason}"
            )

            # Step 2: Handle stage progression if needed
            stage_changed = False
            if supervisor_decision.decision == "advance":
                old_stage = context.current_stage
                progression_result = self._session_manager.advance_to_next_stage()
                if not progression_result.success:
                    self._logger.log_error(f"Stage progression failed: {progression_result.error}")
                else:
                    new_stage = self._session_manager.get_current_stage()
                    self._logger.log_info("=" * 60)
                    self._logger.log_info(f"🎯 ZMIANA ETAPU TERAPII: '{old_stage}' → '{new_stage}'")
                    self._logger.log_info("Nowe prompty systemowe zostaną ustawione dla agentów")
                    self._logger.log_info("=" * 60)
                    stage_changed = True

            current_stage = self._session_manager.get_current_stage()

            # Step 3: Generate therapist response
            self._logger.log_info("💬 Generuję odpowiedź terapeuty...")

            therapist_result = self._therapist_responder.generate_response(
                current_stage, context.user_message, context.conversation_history
            )

            if not therapist_result.success:
                return therapist_result

            therapist_response = therapist_result.data["response"]

            # Add stage transition message if stage changed
            if stage_changed:
                self._add_stage_transition_message(current_stage)

            # Step 4: Update conversation history
            # Check if user message is already in session
            messages = self._session_manager.get_conversation_history()
            if not messages or messages[-1].text != context.user_message:
                self._session_manager.add_user_message(context.user_message)

            self._session_manager.add_assistant_message(
                therapist_response,
                therapist_result.data.get("prompt_id", "unknown")
            )

            return WorkflowResult(
                success=True,
                message="User message processed successfully",
                data={
                    "supervisor_decision": supervisor_decision,
                    "therapist_response": therapist_response,
                    "stage_changed": stage_changed,
                    "current_stage": current_stage
                }
            )

        except Exception as e:
            self._logger.log_error(f"Legacy workflow failed: {str(e)}")
            return WorkflowResult(
                success=False,
                message="Legacy workflow processing failed",
                error=str(e)
            )

    def _add_stage_transition_message(self, current_stage: str) -> None:
        """Add stage transition message to conversation."""
        stage_transition_message = f"[Etap terapii: {current_stage}]"
        self._session_manager.add_stage_transition_message(stage_transition_message)