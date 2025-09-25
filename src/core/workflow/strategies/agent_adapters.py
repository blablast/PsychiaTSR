"""Adapters for using agents directly in strategies."""

from typing import List
from src.core.workflow.workflow_result import WorkflowResult
from src.core.models.schemas import MessageData


class SupervisorAdapter:
    """Adapter for supervisor agent to match old interfaces."""

    def __init__(self, agent_provider, prompt_manager, logger):
        self._agent_provider = agent_provider
        self._prompt_manager = prompt_manager
        self._logger = logger

    def evaluate_stage(self, current_stage: str, user_message: str, conversation_history: List[MessageData]) -> WorkflowResult:
        """Evaluate stage using supervisor agent directly."""
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

            # Call supervisor agent directly
            decision = supervisor_agent.evaluate_stage_completion(
                stage=current_stage,
                history=conversation_history,
                stage_prompt=stage_prompt
            )

            return WorkflowResult(
                success=True,
                message="Stage evaluation completed",
                data={"decision": decision}
            )

        except Exception as e:
            self._logger.log_error(f"Supervisor evaluation failed: {str(e)}")
            return WorkflowResult(
                success=False,
                message="Supervisor evaluation failed",
                error=str(e)
            )


class TherapistAdapter:
    """Adapter for therapist agent to match old interfaces."""

    def __init__(self, agent_provider, prompt_manager, logger):
        self._agent_provider = agent_provider
        self._prompt_manager = prompt_manager
        self._logger = logger

    def generate_response(self, current_stage: str, user_message: str, conversation_history: List[MessageData]) -> WorkflowResult:
        """Generate response using therapist agent directly."""
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

            # Call therapist agent directly
            response = therapist_agent.generate_response(
                user_message=user_message,
                stage_prompt=stage_prompt,
                conversation_history=conversation_history,
                stage_id=current_stage
            )

            if not response["success"]:
                return WorkflowResult(
                    success=False,
                    message="Therapist response generation failed",
                    error=response.get("error", "Unknown error")
                )

            return WorkflowResult(
                success=True,
                message="Response generated successfully",
                data={
                    "response": response["response"],
                    "prompt_id": f"therapist_{current_stage}"
                }
            )

        except Exception as e:
            self._logger.log_error(f"Therapist response generation failed: {str(e)}")
            return WorkflowResult(
                success=False,
                message="Therapist response generation failed",
                error=str(e)
            )

    def generate_response_stream(self, current_stage: str, user_message: str, conversation_history: List[MessageData]):
        """Generate streaming response using therapist agent directly."""
        try:

            therapist_agent = self._agent_provider.get_therapist_agent()
            if not therapist_agent:
                # Yield error message for streaming context
                yield f"[Błąd: Agent terapeuty nie jest dostępny]"
                return WorkflowResult(
                    success=False,
                    message="Therapist agent not available",
                    error="THERAPIST_NOT_AVAILABLE"
                )


            # Get stage prompt
            stage_prompt = self._prompt_manager.get_stage_prompt(current_stage, "therapist")
            if not stage_prompt:
                yield f"[Błąd: Brak promptu dla etapu: {current_stage}]"
                return WorkflowResult(
                    success=False,
                    message=f"No stage prompt available for stage: {current_stage}",
                    error="STAGE_PROMPT_NOT_FOUND"
                )


            # Stream response from therapist agent
            full_response = ""
            metadata = None

            stream_generator = therapist_agent.generate_response_stream(
                user_message=user_message,
                stage_prompt=stage_prompt,
                conversation_history=conversation_history,
                stage_id=current_stage
            )

            chunk_count = 0
            for chunk in stream_generator:
                chunk_count += 1
                if isinstance(chunk, str):
                    full_response += chunk
                    yield chunk
                else:
                    # This is the final metadata dict
                    metadata = chunk
                    break


            # Yield final result with collected response
            if full_response:
                yield WorkflowResult(
                    success=True,
                    message="Streaming response generated successfully",
                    data={
                        "response": full_response,
                        "prompt_id": f"therapist_{current_stage}",
                        "response_time_ms": metadata.get("response_time_ms", 0) if metadata else 0
                    }
                )
            else:
                error_msg = metadata.get("error", "No response generated") if metadata else "Streaming failed"
                yield WorkflowResult(
                    success=False,
                    message="Therapist streaming response generation failed",
                    error=error_msg
                )

        except Exception as e:
            self._logger.log_error(f"Therapist streaming response failed: {str(e)}")
            yield f"[Błąd streamingu: {str(e)}]"
            return WorkflowResult(
                success=False,
                message="Therapist streaming response generation failed",
                error=str(e)
            )