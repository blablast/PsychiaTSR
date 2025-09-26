"""Async conversation workflow strategy using dependency injection."""

from typing import AsyncGenerator

from .async_agent_adapters import AsyncSupervisorAdapter, AsyncTherapistAdapter
from ..workflow_result import WorkflowResult


class AsyncConversationWorkflowStrategy:
    """
    Async workflow strategy that handles conversation flow with supervisor and therapist agents.

    This strategy mirrors ConversationWorkflowStrategy but uses async/await for better performance.
    """

    def __init__(self, agent_provider, prompt_manager, conversation_manager, logger):
        """Initialize with injected dependencies."""
        self._agent_provider = agent_provider
        self._prompt_manager = prompt_manager
        self._conversation_manager = conversation_manager
        self._logger = logger

        # Create async adapters
        self._supervisor_adapter = AsyncSupervisorAdapter(agent_provider, prompt_manager, logger)
        self._therapist_adapter = AsyncTherapistAdapter(agent_provider, prompt_manager, logger)

    async def process_user_message_async(
        self, user_message: str, current_stage: str
    ) -> WorkflowResult:
        """
        Process user message asynchronously through the full conversation workflow.

        Steps:
        1. Get conversation history
        2. Evaluate stage completion with supervisor (async)
        3. Generate therapist response (async)
        4. Commit response to conversation
        """
        try:
            if self._logger:
                self._logger.log_info(
                    f"Starting async conversation workflow for stage: {current_stage}"
                )

            # Get conversation history
            conversation_history = self._conversation_manager.get_conversation_for_agents()

            # Step 1: Evaluate stage completion with supervisor (async)
            supervisor_result = await self._supervisor_adapter.evaluate_stage_async(
                current_stage=current_stage,
                user_message=user_message,
                conversation_history=conversation_history,
            )

            if not supervisor_result.success:
                return supervisor_result

            decision = supervisor_result.data.get("decision")
            if self._logger:
                self._logger.log_info(
                    f"Async supervisor evaluation completed",
                    {
                        "should_advance": decision.should_advance if decision else False,
                        "confidence": decision.confidence_score if decision else 0.0,
                    },
                )

            # Step 2: Generate therapist response (async)
            therapist_result = await self._therapist_adapter.generate_response_async(
                current_stage=current_stage,
                user_message=user_message,
                conversation_history=conversation_history,
            )

            if not therapist_result.success:
                return therapist_result

            # Step 3: Commit response to conversation
            response_data = therapist_result.data
            response_text = response_data.get("response", "")

            # Commit the therapist response
            self._conversation_manager.commit_therapist_response(response_text)

            if self._logger:
                self._logger.log_info("Async conversation workflow completed successfully")

            return WorkflowResult(
                success=True,
                message="Async conversation workflow completed",
                data={
                    "response": response_text,
                    "supervisor_decision": decision.__dict__ if decision else None,
                    "response_time_ms": response_data.get("response_time_ms", 0),
                },
            )

        except Exception as e:
            if self._logger:
                self._logger.log_error(f"Async conversation workflow failed: {str(e)}")

            return WorkflowResult(
                success=False,
                message=f"Async conversation workflow failed: {str(e)}",
                error="ASYNC_WORKFLOW_ERROR",
            )

    async def process_user_message_streaming_async(
        self, user_message: str, current_stage: str
    ) -> AsyncGenerator[str, None]:
        """
        Process user message with streaming response asynchronously.

        This provides real-time streaming of the therapist response while handling
        the full conversation workflow asynchronously.
        """
        try:
            if self._logger:
                self._logger.log_info(
                    f"Starting async streaming conversation workflow for stage: {current_stage}"
                )

            # Get conversation history
            conversation_history = self._conversation_manager.get_conversation_for_agents()

            # Step 1: Evaluate stage completion with supervisor (async)
            supervisor_result = await self._supervisor_adapter.evaluate_stage_async(
                current_stage=current_stage,
                user_message=user_message,
                conversation_history=conversation_history,
            )

            if not supervisor_result.success:
                yield f"[Błąd supervisora: {supervisor_result.message}]"
                return

            decision = supervisor_result.data.get("decision")
            if self._logger:
                self._logger.log_info(
                    f"Async supervisor evaluation completed",
                    {
                        "should_advance": decision.should_advance if decision else False,
                        "confidence": decision.confidence_score if decision else 0.0,
                    },
                )

            # Step 2: Generate streaming therapist response (async)
            full_response = ""
            workflow_result = None

            async for chunk in self._therapist_adapter.generate_streaming_response_async(
                current_stage=current_stage,
                user_message=user_message,
                conversation_history=conversation_history,
            ):
                if isinstance(chunk, str):
                    full_response += chunk
                    yield chunk
                elif isinstance(chunk, WorkflowResult):
                    # Capture the final workflow result
                    workflow_result = chunk
                    break

            # Step 3: Commit response to conversation (if successful)
            if workflow_result and workflow_result.success:
                self._conversation_manager.commit_therapist_response(full_response)

                if self._logger:
                    self._logger.log_info(
                        "Async streaming conversation workflow completed successfully"
                    )
            else:
                if self._logger:
                    self._logger.log_error("Async streaming workflow failed to complete properly")

        except Exception as e:
            if self._logger:
                self._logger.log_error(f"Async streaming conversation workflow failed: {str(e)}")
            yield f"[Błąd async workflow: {str(e)}]"
