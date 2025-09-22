"""Handles therapist response generation."""

import time
from datetime import datetime
from typing import List, Optional

from ..agents.interfaces.agent_provider_interface import IAgentProvider
from ..prompts.unified_prompt_manager import UnifiedPromptManager
from .workflow_result import WorkflowResult
from ...utils.schemas import MessageData, SupervisorDecision


class TherapistResponder:
    """Handles therapist response generation."""

    def __init__(self,
                 agent_provider: IAgentProvider,
                 prompt_manager: UnifiedPromptManager,
                 logger):
        self._agent_provider = agent_provider
        self._prompt_manager = prompt_manager
        self._logger = logger

    def generate_response(self,
                         current_stage: str,
                         user_message: str,
                         conversation_history: List[MessageData]) -> WorkflowResult:
        """
        Generate therapist response for the current stage.

        Args:
            current_stage: Current therapy stage identifier
            user_message: Latest user message
            conversation_history: Full conversation history

        Returns:
            WorkflowResult containing therapist response
        """
        try:
            therapist_agent = self._agent_provider.get_therapist_agent()
            if not therapist_agent:
                return WorkflowResult(
                    success=False,
                    message="Therapist agent not initialized",
                    error="AGENT_NOT_FOUND"
                )

            start_time = time.time()

            # Set system prompt if not already set
            system_prompt = self._prompt_manager.get_system_prompt("therapist")
            if not system_prompt:
                return WorkflowResult(
                    success=False,
                    message="No system prompt available for therapist",
                    error="SYSTEM_PROMPT_NOT_FOUND"
                )

            if not hasattr(therapist_agent, '_system_prompt') or not therapist_agent._system_prompt:
                therapist_agent.set_system_prompt(system_prompt)

            # Get stage prompt
            stage_prompt = self._prompt_manager.get_stage_prompt(current_stage, "therapist")
            if not stage_prompt:
                return WorkflowResult(
                    success=False,
                    message=f"No stage prompt available for stage: {current_stage}",
                    error="STAGE_PROMPT_NOT_FOUND"
                )

            # Create prompt data for logging
            prompt_data = {
                "id": f"therapist_{current_stage}",
                "prompt_text": f"{system_prompt}\n\n{stage_prompt}"
            }

            # Log request
            self._logger.log_therapist_request(prompt_data)

            # Prepare conversation history
            full_history = conversation_history + [
                MessageData(
                    role="user",
                    text=user_message,
                    timestamp=datetime.now().isoformat(),
                    prompt_used=""
                )
            ]

            # Generate response with stage optimization
            response = therapist_agent.generate_response(
                user_message=user_message,
                stage_prompt=stage_prompt,
                conversation_history=full_history,
                stage_id=current_stage
            )

            response_time = int((time.time() - start_time) * 1000)

            # Log full prompt that was actually sent to therapist
            prompt_info = therapist_agent.get_last_used_prompt_info()
            if prompt_info and prompt_info.get("full_prompt"):
                self._logger.log_info(f"📝 Complete therapist prompt with context:\n{prompt_info['full_prompt']}")

            if response["success"]:
                # Clean response without supervisor context for user
                clean_response = response["response"].replace('\\n', '\n')

                self._logger.log_therapist_response(clean_response, response_time)

                return WorkflowResult(
                    success=True,
                    message="Response generated successfully",
                    data={
                        "response": clean_response,
                        "original_response": response["response"],
                        "response_time_ms": response_time,
                        "prompt_used": prompt_data
                    }
                )
            else:
                return WorkflowResult(
                    success=False,
                    message="Therapist response generation failed",
                    error=response.get("error", "Unknown error")
                )

        except Exception as e:
            self._logger.log_error(f"Therapist response generation failed: {str(e)}")
            return WorkflowResult(
                success=False,
                message="Therapist response generation failed",
                error=str(e)
            )

