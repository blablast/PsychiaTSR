"""Conversation workflow strategy - extracted from process_pending_question."""

from ..workflow_result import WorkflowResult
from .workflow_strategy import WorkflowStrategy
from .workflow_context import WorkflowContext


class ConversationWorkflowStrategy(WorkflowStrategy):
    """Conversation workflow strategy using ConversationManager."""

    def __init__(self, supervisor_evaluator, therapist_responder, conversation_manager, logger):
        """
        Initialize conversation workflow strategy.

        Args:
            supervisor_evaluator: Supervisor evaluation handler
            therapist_responder: Therapist response handler
            conversation_manager: Conversation state manager
            logger: Logger for workflow events
        """
        self._supervisor_evaluator = supervisor_evaluator
        self._therapist_responder = therapist_responder
        self._conversation_manager = conversation_manager
        self._logger = logger

    def execute(self, context: WorkflowContext) -> WorkflowResult:
        """
        Execute conversation workflow strategy.

        This mirrors the original process_pending_question logic.
        """
        try:
            # Check if already processing and abort if needed
            if self._conversation_manager.is_processing():
                # Remove excessive warning logging - this is expected behavior
                self._conversation_manager.abort_processing()

            # Start processing - freeze current question
            committed_context, current_question = self._conversation_manager.start_processing()

            # Step 1: Supervisor evaluation (simplified logging)
            # Removed: "🔍 Rozpoczynam konsultację z supervisorem..." - too verbose

            supervisor_result = self._supervisor_evaluator.evaluate_stage(
                context.current_stage, current_question, committed_context
            )

            if not supervisor_result.success:
                self._conversation_manager.abort_processing()
                return supervisor_result

            supervisor_decision = supervisor_result.data["decision"]

            # Simplified supervisor decision logging (decision already logged by supervisor)
            # Removed verbose info logging

            # Step 2: Generate therapist response (removed verbose logging)

            therapist_result = self._therapist_responder.generate_response(
                context.current_stage, current_question, committed_context
            )

            if not therapist_result.success:
                self._conversation_manager.abort_processing()
                return therapist_result

            therapist_response = therapist_result.data["response"]

            # Step 3: Commit the conversation exchange
            self._conversation_manager.commit_therapist_response(therapist_response)

            return WorkflowResult(
                success=True,
                message="Pending question processed successfully",
                data={
                    "supervisor_decision": supervisor_decision,
                    "therapist_response": therapist_response,
                    "stage_changed": supervisor_decision.decision == "advance",
                    "current_stage": context.current_stage,
                },
            )

        except Exception as e:
            # Ensure we abort processing if we're still in that state
            if self._conversation_manager.is_processing():
                self._conversation_manager.abort_processing()
            self._logger.log_error(f"Conversation workflow failed: {str(e)}")
            return WorkflowResult(
                success=False, message="Conversation workflow processing failed", error=str(e)
            )

    def execute_stream(self, context: WorkflowContext):
        """
        Execute conversation workflow strategy with streaming therapist response.

        Yields therapist response chunks while handling supervisor evaluation normally.
        """
        try:

            # Check if already processing and abort if needed
            if self._conversation_manager.is_processing():
                self._conversation_manager.abort_processing()

            # Start processing - freeze current question
            committed_context, current_question = self._conversation_manager.start_processing()

            # Step 1: Supervisor evaluation (non-streaming, simplified logging)

            supervisor_result = self._supervisor_evaluator.evaluate_stage(
                context.current_stage, current_question, committed_context
            )

            if not supervisor_result.success:
                self._conversation_manager.abort_processing()
                yield f"[Błąd supervisora: {supervisor_result.message}]"
                return supervisor_result

            supervisor_decision = supervisor_result.data["decision"]

            # Step 2: Generate streaming therapist response

            full_response = ""
            therapist_result = None

            # Stream therapist response
            stream_generator = self._therapist_responder.generate_response_stream(
                context.current_stage, current_question, committed_context
            )

            chunk_count = 0
            for chunk in stream_generator:
                chunk_count += 1
                if isinstance(chunk, str):
                    full_response += chunk
                    yield chunk
                else:
                    # This is the final WorkflowResult
                    therapist_result = chunk
                    break

            if not therapist_result or not therapist_result.success:
                self._conversation_manager.abort_processing()
                error_msg = (
                    therapist_result.message if therapist_result else "Therapist streaming failed"
                )
                yield f"[Błąd terapeuty: {error_msg}]"
                return therapist_result or WorkflowResult(
                    success=False, message="Therapist streaming failed", error="STREAMING_FAILED"
                )

            therapist_response = therapist_result.data["response"]

            # Step 3: Commit the conversation exchange
            self._conversation_manager.commit_therapist_response(therapist_response)

            return WorkflowResult(
                success=True,
                message="Streaming pending question processed successfully",
                data={
                    "supervisor_decision": supervisor_decision,
                    "therapist_response": therapist_response,
                    "stage_changed": supervisor_decision.decision == "advance",
                    "current_stage": context.current_stage,
                    "streaming": True,
                },
            )

        except Exception as e:
            # Ensure we abort processing if we're still in that state
            if self._conversation_manager.is_processing():
                self._conversation_manager.abort_processing()
            self._logger.log_error(f"Conversation streaming workflow failed: {str(e)}")
            yield f"[Błąd workflow: {str(e)}]"
            return WorkflowResult(
                success=False,
                message="Conversation streaming workflow processing failed",
                error=str(e),
            )
