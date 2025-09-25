"""Async adapters for using agents in async workflows."""

from typing import List, AsyncGenerator
from src.core.workflow.workflow_result import WorkflowResult
from src.core.models.schemas import MessageData


class AsyncSupervisorAdapter:
    """Async adapter for supervisor agent to match async workflow interfaces."""

    def __init__(self, agent_provider, prompt_manager, logger):
        self._agent_provider = agent_provider
        self._prompt_manager = prompt_manager
        self._logger = logger

    async def evaluate_stage_async(self, current_stage: str, user_message: str, conversation_history: List[MessageData]) -> WorkflowResult:
        """Evaluate stage using supervisor agent asynchronously."""
        try:
            supervisor_agent = self._agent_provider.get_supervisor_agent()
            if not supervisor_agent:
                return WorkflowResult(
                    success=False,
                    message="Supervisor agent not available",
                    error="SUPERVISOR_NOT_AVAILABLE"
                )

            # Get stage prompt
            stage_prompt = self._prompt_manager.get_stage_prompt(current_stage, "supervisor")
            if not stage_prompt:
                return WorkflowResult(
                    success=False,
                    message=f"No stage prompt available for stage: {current_stage}",
                    error="STAGE_PROMPT_NOT_FOUND"
                )

            # Call supervisor agent asynchronously
            decision = await supervisor_agent.evaluate_stage_completion_async(
                stage=current_stage,
                history=conversation_history,
                stage_prompt=stage_prompt
            )

            return WorkflowResult(
                success=True,
                message="Async stage evaluation completed",
                data={"decision": decision}
            )

        except Exception as e:
            if self._logger:
                self._logger.log_error(f"Async supervisor evaluation failed: {str(e)}")

            return WorkflowResult(
                success=False,
                message=f"Async supervisor evaluation failed: {str(e)}",
                error="ASYNC_SUPERVISOR_ERROR"
            )


class AsyncTherapistAdapter:
    """Async adapter for therapist agent to match async workflow interfaces."""

    def __init__(self, agent_provider, prompt_manager, logger):
        self._agent_provider = agent_provider
        self._prompt_manager = prompt_manager
        self._logger = logger

    async def generate_response_async(self, current_stage: str, user_message: str, conversation_history: List[MessageData]) -> WorkflowResult:
        """Generate therapist response using agent asynchronously."""
        try:
            therapist_agent = self._agent_provider.get_therapist_agent()
            if not therapist_agent:
                return WorkflowResult(
                    success=False,
                    message="Therapist agent not available",
                    error="THERAPIST_NOT_AVAILABLE"
                )

            # Get stage prompt
            stage_prompt = self._prompt_manager.get_stage_prompt(current_stage, "therapist")
            if not stage_prompt:
                return WorkflowResult(
                    success=False,
                    message=f"No stage prompt available for stage: {current_stage}",
                    error="STAGE_PROMPT_NOT_FOUND"
                )

            # Call therapist agent asynchronously
            response_data = await therapist_agent.generate_response_async(
                user_message=user_message,
                stage_prompt=stage_prompt,
                conversation_history=conversation_history,
                stage_id=current_stage
            )

            if response_data.get("success", False):
                return WorkflowResult(
                    success=True,
                    message="Async therapist response generated successfully",
                    data=response_data
                )
            else:
                return WorkflowResult(
                    success=False,
                    message=f"Therapist response generation failed: {response_data.get('error', 'Unknown error')}",
                    error="ASYNC_THERAPIST_ERROR"
                )

        except Exception as e:
            if self._logger:
                self._logger.log_error(f"Async therapist response generation failed: {str(e)}")

            return WorkflowResult(
                success=False,
                message=f"Async therapist response generation failed: {str(e)}",
                error="ASYNC_THERAPIST_ERROR"
            )

    async def generate_streaming_response_async(self, current_stage: str, user_message: str, conversation_history: List[MessageData]) -> AsyncGenerator[str, None]:
        """Generate streaming therapist response using agent asynchronously."""
        try:
            therapist_agent = self._agent_provider.get_therapist_agent()
            if not therapist_agent:
                yield "[Błąd: Agent terapeuty niedostępny]"
                return

            # Get stage prompt
            stage_prompt = self._prompt_manager.get_stage_prompt(current_stage, "therapist")
            if not stage_prompt:
                yield f"[Błąd: Brak promptu dla etapu {current_stage}]"
                return

            # Stream from therapist agent asynchronously
            async for chunk in therapist_agent.generate_streaming_response_async(
                user_message=user_message,
                stage_prompt=stage_prompt,
                conversation_history=conversation_history,
                stage_id=current_stage
            ):
                if isinstance(chunk, str):
                    yield chunk
                elif isinstance(chunk, dict):
                    # Handle final metadata - this needs to be processed by the workflow
                    if chunk.get("success", False):
                        # Log successful completion but don't yield the metadata
                        if self._logger:
                            self._logger.log_info("Async streaming response completed successfully")

                        # Log completion - workflow will handle final result separately
                        if self._logger:
                            self._logger.log_info(f"Async streaming completed for stage {current_stage}")
                    else:
                        # Handle error metadata
                        error_msg = chunk.get("error", "Unknown error")
                        if self._logger:
                            self._logger.log_error(f"Async streaming response failed: {error_msg}")

        except Exception as e:
            if self._logger:
                self._logger.log_error(f"Async therapist streaming failed: {str(e)}")
            yield f"[Błąd streamingu async: {str(e)}]"