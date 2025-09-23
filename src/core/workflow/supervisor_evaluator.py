"""Handles supervisor evaluations for stage progression."""

import time
from datetime import datetime
from typing import List

from ..agents.interfaces.agent_provider_interface import IAgentProvider
from ..prompts.unified_prompt_manager import UnifiedPromptManager
from .workflow_result import WorkflowResult
from ...utils.schemas import MessageData


class SupervisorEvaluator:
    """Handles supervisor evaluations for stage progression."""

    def __init__(self,
                 agent_provider: IAgentProvider,
                 prompt_manager: UnifiedPromptManager,
                 logger):
        self._agent_provider = agent_provider
        self._prompt_manager = prompt_manager
        self._logger = logger

    def evaluate_stage(self,
                      current_stage: str,
                      user_message: str,
                      conversation_history: List[MessageData]) -> WorkflowResult:
        """
        Evaluate current therapy stage and determine if progression is needed.

        Args:
            current_stage: Current therapy stage identifier
            user_message: Latest user message
            conversation_history: Full conversation history

        Returns:
            WorkflowResult containing evaluation results
        """
        try:
            supervisor_agent = self._agent_provider.get_supervisor_agent()
            if not supervisor_agent:
                return WorkflowResult(
                    success=False,
                    message="Supervisor agent not initialized",
                    error="AGENT_NOT_FOUND"
                )

            start_time = time.time()

            # Set system prompt if not already set
            system_prompt = self._prompt_manager.get_system_prompt("supervisor")
            if not system_prompt:
                return WorkflowResult(
                    success=False,
                    message="No system prompt available for supervisor",
                    error="SYSTEM_PROMPT_NOT_FOUND"
                )

            if not hasattr(supervisor_agent, '_system_prompt') or not supervisor_agent._system_prompt:
                supervisor_agent.set_system_prompt(system_prompt)

            # Get stage prompt
            stage_prompt = self._prompt_manager.get_stage_prompt(current_stage, "supervisor")
            if not stage_prompt:
                return WorkflowResult(
                    success=False,
                    message=f"No stage prompt available for stage: {current_stage}",
                    error="STAGE_PROMPT_NOT_FOUND"
                )

            # Create prompt data for logging
            prompt_data = {
                "id": f"supervisor_{current_stage}",
                "prompt_text": f"{system_prompt}\n\n{stage_prompt}"
            }

            # Log request
            self._logger.log_supervisor_request(prompt_data)

            # Prepare conversation history
            full_history = conversation_history + [
                MessageData(
                    role="user",
                    text=user_message,
                    timestamp=datetime.now().isoformat(),
                    prompt_used=""
                )
            ]

            # Execute supervisor evaluation
            decision = supervisor_agent.evaluate_stage_completion(
                current_stage, full_history, stage_prompt
            )

            response_time = int((time.time() - start_time) * 1000)

            # Log full prompt that was actually sent to supervisor
            prompt_info = supervisor_agent.get_last_used_prompt_info()
            if prompt_info and prompt_info.get("full_prompt"):
                try:
                    from src.ui.technical_log_display import add_technical_log
                    add_technical_log(
                        "supervisor_full_prompt",
                        f"📝 Complete supervisor prompt with context:\n{prompt_info['full_prompt']}"
                    )
                except ImportError:
                    # Fallback to standard logger if import fails
                    self._logger.log_info(f"📝 Complete supervisor prompt with context:\n{prompt_info['full_prompt']}")

            # Log response
            self._logger.log_supervisor_response(decision, response_time)

            return WorkflowResult(
                success=True,
                message="Stage evaluation completed",
                data={
                    "decision": decision,
                    "response_time_ms": response_time,
                    "prompt_used": prompt_data
                }
            )

        except Exception as e:
            self._logger.log_error(f"Supervisor evaluation failed: {str(e)}")
            return WorkflowResult(
                success=False,
                message="Supervisor evaluation failed",
                error=str(e)
            )